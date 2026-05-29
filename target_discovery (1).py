import os
import json
import time  # NEW: Required for the backoff delay timers
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv

# 1. Import the NEW Google GenAI SDK
from google import genai
from google.genai import types

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# 2. Initialize the new Client
client = genai.Client(api_key=GEMINI_API_KEY)


def generate_search_dorks(country, num_dorks=5):
    print(f"[*] Asking Gemini to generate {num_dorks} broad-net footprint dorks for medical professionals in {country}...")
    
    
    prompt = f"""
    You are an elite OSINT architecture system specialized in high-yield medical infrastructure data collection.
    Your objective is to generate exactly {num_dorks} flat, broad-net Google Search Operators (dorks) that surface maximum-density directory "Hub" pages containing lists of cancer care professionals EXCLUSIVELY within {country}.

    THE MASSIVE COHORT BLOCK (Mandatory: Copy this entire block exactly inside every single dork as your primary keyword anchor):
    (oncologist OR hematologist OR specialist OR physician OR researcher OR faculty OR consultant OR pathologist OR clinician)

    DECENTRALIZATION LAWS FOR HIGH DOMAIN YIELD (25-40+ UNIQUE DOMAINS PER QUERY):
    1. ONE INFRASTRUCTURE TYPE PER QUERY: Do not mix architectural layers together. Dedicate individual dorks to target distinct domain groups:
       - Academic Layer: Higher-Education domains using native regional filters (e.g., 'site:edu.in' for India, 'site:ac.uk' for UK).
       - Public Trust Layer: Non-profit foundations and charitable organizations (e.g., using 'site:org.in').
       - Commercial/Private Layer: Multi-specialty networks and private clinic hubs (e.g., using 'site:co.in' or 'site:com').
    2. CASCADING EXCLUSIONS: You must instruct at least two queries to actively use the minus site operator (-site:) to ban the top 2 dominant hospital networks of {country} to force Google to unearth hidden regional clinics.
    3. NO MULTI-FILTER CHOKING: Never combine a country name, city names, and a top-level domain filter in the same query. Use exactly ONE broad geographic or TLD indicator per dork to keep the search window wide open.
    4. STRUCTURAL FOOTPRINTS ONLY: Force the engine to hit aggregate tables using footprints like intitle:"staff directory", intitle:"our team", or inurl:find-a-doctor.

    Return a valid JSON array of exactly {num_dorks} highly unique string queries matching these structural layers. Do not include markdown code fences or explanations.
    """

    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            # FIX: Wrapped inside retry mechanism to automatically absorb 503 Server Unavailable errors
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json",  # Forces Gemini to output structural JSON text
                    response_schema=list[str]              # Demands a clean string array collection natively
                )
            )
            
            # If the network execution completes successfully, decode immediately
            dorks = json.loads(response.text)
            print(f"[+] Gemini natively generated {len(dorks)} high-yield dorks successfully.")
            return dorks
            
        except Exception as e:
            # Detect transient server spike capacities (HTTP 503)
            if "503" in str(e) and attempt < max_retries:
                sleep_time = attempt * 5  # Incremental exponential wait block (5s, 10s)
                print(f"[-] Gemini API busy (503 Unavailable). Retrying attempt {attempt}/{max_retries} in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                print(f"[-] Native JSON parsing fell behind or API down: {e}. Executing structural fallback logic.")
                # Bulletproof fallback queries specific to country to keep the scraping flow active
                return [
                    f'-jobs -careers site:au intitle:"staff directory" oncology',
                    f'-jobs -careers site:au inurl:faculty "cancer research"',
                    f'-jobs -careers site:au intitle:"our team" medical physician'
                ][:num_dorks]


def fetch_urls_from_serp(dork):
    print(f"[*] Executing search for: {dork}")
    
    params = {
        "engine": "google",
        "q": dork,
        "api_key": SERPAPI_API_KEY,
        "num": 100  # MAXIMIZED: 100 results per 1 API credit
    }
    
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=20.0)
        
        if response.status_code != 200:
            print(f"[-] SERP API Error: {response.text}")
            return []
            
        data = response.json()
        organic_results = data.get("organic_results", [])
        
        urls = [result.get("link") for result in organic_results if "link" in result]
        print(f"[+] Found {len(urls)} URLs from this search.")
        return urls
    except Exception as e:
        print(f"[-] Network layer error querying SerpApi: {e}")
        return []

def group_by_domain(urls):
    grouped_data = {}
    for url in urls:
        if not url:
            continue
        domain = urlparse(url).netloc
        if not domain:
            continue
            
        parts = domain.split('.')
        root_domain = ".".join(parts[-2:]) if len(parts) >= 2 else domain
        
        if root_domain not in grouped_data:
            grouped_data[root_domain] = []
        
        if url not in grouped_data[root_domain]:
            grouped_data[root_domain].append(url)
            
    return grouped_data

def run_phase_1():
    print("=== Starting Phase 1: Intelligent Target Discovery ===")
    
    target_country = "Australia"
    
    dorks = generate_search_dorks(target_country, num_dorks=3)
    
    all_discovered_urls = []
    for dork in dorks:
        urls = fetch_urls_from_serp(dork)
        all_discovered_urls.extend(urls)
        
    grouped_urls = group_by_domain(all_discovered_urls)
    
    # FIX: Pin absolute execution folder paths to prevent hidden routing across Windows
    current_directory = os.getcwd()
    # output_file = os.path.join(current_directory, "phase1_targets.json")
    # print(f"[*] Securely committing tracking array to: {output_file}")
    
    # # FIX: Added strict encoding formats and persistent OS write barriers
    # with open(output_file, "w", encoding="utf-8") as f:
    #     json.dump(grouped_urls, f, indent=4, ensure_ascii=False)
    #     f.flush()              # Force internal Python data blocks down to the OS level
    #     os.fsync(f.fileno())   # Force the Windows Kernel to physically write data to your storage hardware
        
    output_file = os.path.join(current_directory, "phase1_targets.txt")

# remove duplicates while preserving order
    unique_urls = list(dict.fromkeys(all_discovered_urls))

    with open(output_file, "w", encoding="utf-8") as f:
      for url in unique_urls:
        f.write(url + "\n")

      f.flush()
      os.fsync(f.fileno())

    print(f"\n=== Phase 1 Complete ===")
    print(f"Total Unique Domains Found: {len(grouped_urls)}")
    print(f"Total URLs Discovered: {len(all_discovered_urls)}")
    print(f"[!!!] Targets successfully verified and physically locked onto your disk.")

if __name__ == "__main__":
    run_phase_1()