import os
import json
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

def get_proven_australian_dorks():
    """
    Returns a completely hardcoded, high-yield array of broad-net
    Australian dorks covering all 10 requested target sectors.
    """
    return [
        # 1. University Medical Faculties
        '-jobs -careers site:edu.au intitle:"staff directory" oncology OR cancer',
        '-jobs -careers site:edu.au intitle:"faculty directory" medicine OR clinical',
        '-jobs -careers site:edu.au "research profiles" hematology OR radiation',
        
        # 2. Public Hospital Staff Infrastructure
        '-jobs -careers site:vic.gov.au OR site:nsw.gov.au "medical staff directory"',
        '-jobs -careers site:qld.gov.au OR site:sa.gov.au "clinical profiles" hospital',
        '-jobs -careers "Royal Melbourne" OR "Royal Prince Alfred" intitle:"team" doctor',
        '-jobs -careers "Sir Charles Gairdner" OR "Princess Alexandra" staff directory',
        
        # 3. Cancer Research Institutes
        '-jobs -careers site:org.au "peter maccallum" intitle:"our researchers"',
        '-jobs -careers site:org.au "garvan" OR "qimr berghofer" intitle:"our team"',
        '-jobs -careers site:org.au "wehi" OR "anzup" cancer research faculty',
        
        # 4. Medical Conferences & Abstracts
        'site:org.au "invited speakers" "annual scientific meeting" oncology',
        'site:com.au "speaker profiles" "cancer conference" abstract',
        
        # 5. Practitioner Aggregators & Registries
        'site:healthengine.com.au/find/oncology specialist',
        'site:hotdoc.com.au/medical-centres oncologist',
        
        # 6. Government Health Networks
        '-jobs -careers site:health.gov.au OR site:aihw.gov.au "clinical panel" OR "committee"',
        
        # 7. Medical Journals (Australian Affiliations)
        'inurl:article "Department of Radiation Oncology" "Australia" email',
        'inurl:pmc "hematology department" "Australia" corresponding author',
        
        # 8. Private Oncology Clinics
        '-jobs -careers site:com.au "our specialists" oncology clinic',
        '-jobs -careers site:com.au intitle:"find a doctor" private cancer hospital',
        
        # 9. Cancer Council State Branches
        '-jobs -careers "cancercouncil.com.au" OR "cancervic.org.au" intitle:"researchers"',
        
        # 10. Professional Bodies
        '-jobs -careers "cosa.org.au" OR "ranzcr.com" committee OR faculty'
    ]

def fetch_urls_from_serp(dork):
    print(f"[*] Executing target search: {dork}")
    
    params = {
        "engine": "google",
        "q": dork,
        "api_key": SERPAPI_API_KEY,
        "num": 100  # Max out the index payload per credit call
    }
    
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=20.0)
        if response.status_code != 200:
            print(f"[-] SERP API Error: {response.text}")
            return []
            
        data = response.json()
        organic_results = data.get("organic_results", [])
        
        urls = [result.get("link") for result in organic_results if "link" in result]
        print(f"[+] Found {len(urls)} URLs from this branch.")
        return urls
    except Exception as e:
        print(f"[-] Connection tracking issue: {e}")
        return []

def group_by_domain(urls):
    grouped_data = {}
    for url in urls:
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
    print("=== Starting Phase 1: High-Yield Target Discovery (Australia) ===")
    
    # Fire all 21 highly targeted, broad-index queries sequentially
    dorks = get_proven_australian_dorks()
    
    all_discovered_urls = []
    
    for dork in dorks:
        urls = fetch_urls_from_serp(dork)
        all_discovered_urls.extend(urls)
        
    grouped_urls = group_by_domain(all_discovered_urls)
    
    output_file = "phase1_targets.json"
    with open(output_file, "w") as f:
        json.dump(grouped_urls, f, indent=4)
        
    print(f"\n=== Phase 1 Harvesting Complete ===")
    print(f"Total Unique Base Domains Aggregated: {len(grouped_urls)}")
    print(f"Total Raw Target URLs Harvested: {len(all_discovered_urls)}")
    print(f"[+] Multi-sector data safely saved to: {output_file}")

if __name__ == "__main__":
    run_phase_1()