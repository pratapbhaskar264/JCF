import os
import json
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
    You are an elite OSINT researcher tasked with finding high-yield directories of medical professionals in {country}.
    Your goal is to generate Google Search Operators (dorks) that will surface "Hub" pages: staff directories, 
    faculty lists, researcher profiles, and "find a doctor" indexes across ANY domain (.com, .org, .edu, .net, etc.).
    
    RULES FOR GENERATION:
    1. TARGET AUDIENCE: Include a mix of keywords for Oncologists, Researchers, Clinicians, PhDs, Scientists, and Faculty.
    2. FOOTPRINTING: Use operators like intitle: and inurl: to target the structure of directory pages (e.g., intitle:"our team", intitle:"faculty directory", inurl:staff, inurl:find-a-doctor, intitle:"researchers").
    3. EXCLUSIONS: Heavily utilize the minus operator (-) to remove junk. You MUST exclude terms like -jobs, -careers, -apply, -vacancies, -hr, -patients, -enquiry.
    4. NO SITE RESTRICTIONS: Do not restrict to specific top-level domains (like site:edu). Let the footprint keywords find the sites naturally.
    5. DIVERSITY: Ensure every single dork is structurally different from the others to maximize unique domain discovery.
    
    Return ONLY a valid JSON array of {num_dorks} string queries. Do not include markdown formatting or explanations.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7 # Increased slightly to force Gemini to be more creative and diverse
        )
    )
    
    try:
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        dorks = json.loads(clean_text)
        print(f"[+] Gemini generated {len(dorks)} high-yield dorks successfully.")
        return dorks
    except json.JSONDecodeError:
        print("[-] Error parsing Gemini response. Fallback to raw text split.")
        return [line.strip().strip('",') for line in response.text.splitlines() if line.strip() and len(line) > 5]


def fetch_urls_from_serp(dork):
    print(f"[*] Executing search for: {dork}")
    
    params = {
        "engine": "google",
        "q": dork,
        "api_key": SERPAPI_API_KEY,
        "num": 100  # MAXIMIZED: 100 results per 1 API credit
    }
    
    response = requests.get("https://serpapi.com/search", params=params)
    
    if response.status_code != 200:
        print(f"[-] SERP API Error: {response.text}")
        return []
        
    data = response.json()
    organic_results = data.get("organic_results", [])
    
    urls = [result.get("link") for result in organic_results if "link" in result]
    print(f"[+] Found {len(urls)} URLs from this search.")
    return urls

def group_by_domain(urls):
    grouped_data = {}
    for url in urls:
        domain = urlparse(url).netloc
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
    # target_specialty = "Oncology OR Gastroenterology"
    
    # We request 2 dorks to test. 2 Dorks * 100 results = Up to 200 URLs for just 2 API credits.
    dorks = generate_search_dorks(target_country, num_dorks=3)
    
    all_discovered_urls = []
    
    for dork in dorks:
        urls = fetch_urls_from_serp(dork)
        all_discovered_urls.extend(urls)
        
    grouped_urls = group_by_domain(all_discovered_urls)
    
    output_file = "phase1_targets.json"
    with open(output_file, "w") as f:
        json.dump(grouped_urls, f, indent=4)
        
    print(f"\n=== Phase 1 Complete ===")
    print(f"Total Unique Domains Found: {len(grouped_urls)}")
    print(f"Total URLs Discovered: {len(all_discovered_urls)}")
    print(f"Targets saved to {output_file}. Ready for Phase 2.")

if __name__ == "__main__":
    run_phase_1()