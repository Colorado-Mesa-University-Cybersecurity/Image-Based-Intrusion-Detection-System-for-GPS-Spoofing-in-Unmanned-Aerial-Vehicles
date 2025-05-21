import csv
import os
from dotenv import load_dotenv, find_dotenv
import asyncio
import vt
import requests
import json

# Configuration
URL_FILE = "urls.txt"  # filename for input URLs
OUTPUT_CSV = "URL_Dataset.csv"  # Output CSV filename

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
GSB_API_KEY = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY")

GSB_API_ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"


def check_url_with_google_safe_browsing(url):
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
            "threatEntries": [{"url": url}]
        }
    }
    params = {"key": GSB_API_KEY}
    response = requests.post(GSB_API_ENDPOINT, params=params, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Google Safe Browsing API error: {response.status_code} - {response.text}")
        return None


def load_urls_from_file(filename):
    urls = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                url = line.strip()
                if url and not url.startswith('#'):  # Skip empty lines and comments
                    urls.append(url)
        print(f"Loaded {len(urls)} URLs from {filename}")
        return urls
    except Exception as e:
        print(f"Error loading URLs from file: {e}")
        return []


async def categorize_urls(urls):
    malicious_urls = []
    benign_urls = []

    async with vt.Client(VIRUSTOTAL_API_KEY) as client:
        for url in urls:
            # Initialize variables
            vt_malicious_count = 0
            vt_suspicious_count = 0
            gsb_is_malicious = False

            # Check with VirusTotal
            try:
                url_id = vt.url_id(url)
                url_obj = await client.get_object_async(f"/urls/{url_id}")
                vt_stats = url_obj.last_analysis_stats
                vt_malicious_count = vt_stats.get('malicious', 0)
                vt_suspicious_count = vt_stats.get('suspicious', 0)
                print(f"URL: {url}, VT Malicious: {vt_malicious_count}, Suspicious: {vt_suspicious_count}")
            except Exception as e:
                print(f"Error checking {url} with VirusTotal: {e}")
                continue  # Skip to the next URL if there's an error

            # Check with Google Safe Browsing
            gsb_result = check_url_with_google_safe_browsing(url)
            if gsb_result and "matches" in gsb_result and gsb_result["matches"]:
                gsb_is_malicious = True
                print(f"URL: {url}, GSB: Malicious")
            else:
                print(f"URL: {url}, GSB: Safe")

            # Categorize based on rules
            if gsb_is_malicious or vt_malicious_count >= 5:
                malicious_urls.append(url)
            elif vt_malicious_count == 0 and vt_suspicious_count == 0:
                benign_urls.append(url)
            else:
                print(f"URL: {url} doesn't fit strictly into malicious or benign categories")

    return malicious_urls, benign_urls


def write_to_csv(malicious_urls, benign_urls, filename=OUTPUT_CSV):

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["# Input file", URL_FILE])
        writer.writerow([])  # Empty row for separation
        writer.writerow(["Malicious", "Benign"])

        # Find the maximum length of either list
        max_length = max(len(malicious_urls), len(benign_urls))

        # Write rows, padding the shorter list with empty strings
        for i in range(max_length):
            malicious = malicious_urls[i] if i < len(malicious_urls) else ""
            benign = benign_urls[i] if i < len(benign_urls) else ""
            writer.writerow([malicious, benign])


async def main():
    if not os.path.exists(URL_FILE):
        print(f"Error: File '{URL_FILE}' not found. Please create this file with one URL per line.")
        return

    urls_to_check = load_urls_from_file(URL_FILE)

    if not urls_to_check:
        print("No URLs to check. Exiting.")
        return

    print(f"Analyzing {len(urls_to_check)} URLs...")
    malicious_urls, benign_urls = await categorize_urls(urls_to_check)

    print("\nResults:")
    print(f"Malicious URLs ({len(malicious_urls)}):")
    for url in malicious_urls:
        print(f"  - {url}")

    print(f"\nBenign URLs ({len(benign_urls)}):")
    for url in benign_urls:
        print(f"  - {url}")

    write_to_csv(malicious_urls, benign_urls)
    print(f"Results written to {OUTPUT_CSV}")


if __name__ == "__main__":
    asyncio.run(main())