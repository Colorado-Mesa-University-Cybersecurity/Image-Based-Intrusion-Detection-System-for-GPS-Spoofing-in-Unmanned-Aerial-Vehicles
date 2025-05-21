import nest_asyncio
nest_asyncio.apply()
import os
from dotenv import load_dotenv, find_dotenv
import asyncio
import vt
import requests
import json

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
GSB_API_KEY = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY")

URLS_TO_CHECK = [
    "https://www.example.com",  # Safe URL
    "https://www.google.com",   # Safe URL
    "https://www.github.com",   # Safe URL
    "http://ww6.17ebook.com/",  # This URL is known to be malicious
]

GSB_API_ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"

def check_with_google_safe_browsing(urls):
    headers = {"Content-Type": "application/json"}
    payload = {
        "client": {
            "clientId": "Colorado Mesa University Cybersecurity Research",
            "clientVersion": "1.0"
        },
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION"
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": u} for u in urls]
        }
    }
    params = {"key": GSB_API_KEY}
    response = requests.post(GSB_API_ENDPOINT, params=params, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Google Safe Browsing API error: {response.status_code} - {response.text}")
        return None

async def get_url_info(urls):
    print("=== VirusTotal Results ===")
    async with vt.Client(VIRUSTOTAL_API_KEY) as client:
        for url_str in urls:
            try:
                url_id = vt.url_id(url_str)
                url_obj = client.get_object(f"/urls/{url_id}")
                print(f"URL: {url_obj.url}")
                print("Last analysis stats:", url_obj.last_analysis_stats)
                print("-" * 40)
            except Exception as e:
                print(f"Error checking {url_str}: {e}")

    print("\n=== Google Safe Browsing Results ===")
    gsb_results = check_with_google_safe_browsing(urls)
    if gsb_results and "matches" in gsb_results:
        for match in gsb_results["matches"]:
            print("Threat found for URL:", match["threat"]["url"])
            print("Threat type:", match["threatType"])
            print("Platform type:", match["platformType"])
            print("-" * 40)
    else:
        print("No threats found by Google Safe Browsing for the given URLs.")

if __name__ == "__main__":
    asyncio.run(get_url_info(URLS_TO_CHECK))