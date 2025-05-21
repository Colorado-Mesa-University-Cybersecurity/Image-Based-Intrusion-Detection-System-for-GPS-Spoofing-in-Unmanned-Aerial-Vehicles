import csv
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

            # Check with Google Safe Browsing
            gsb_result = check_url_with_google_safe_browsing(url)
            if gsb_result and "matches" in gsb_result and gsb_result["matches"]:
                gsb_is_malicious = True
                print(f"URL: {url}, GSB: Malicious")
            else:
                print(f"URL: {url}, GSB: Safe")

            # Categorize based on updated rules
            if gsb_is_malicious or vt_malicious_count >= 5:
                malicious_urls.append(url)
            elif vt_malicious_count == 0 and vt_suspicious_count == 0:
                benign_urls.append(url)
            else:
                # URLs that don't fit either category - you might want to handle these separately
                print(f"URL: {url} doesn't fit strictly into malicious or benign categories")

    return malicious_urls, benign_urls


def write_to_csv(malicious_urls, benign_urls, filename="URL_Dataset.csv"):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Malicious", "Benign"])

        # Find the maximum length of either list
        max_length = max(len(malicious_urls), len(benign_urls))

        # Write rows, padding the shorter list with empty strings
        for i in range(max_length):
            malicious = malicious_urls[i] if i < len(malicious_urls) else ""
            benign = benign_urls[i] if i < len(benign_urls) else ""
            writer.writerow([malicious, benign])

    print(f"CSV file '{filename}' has been created successfully.")


async def main():
    URLS_TO_CHECK = [
        "https://www.example.com",
        "https://www.google.com",
        "https://www.github.com",
        "http://ww6.17ebook.com/",
    ]

    print("Analyzing URLs...")
    malicious_urls, benign_urls = await categorize_urls(URLS_TO_CHECK)

    print("\nResults:")
    print(f"Malicious URLs ({len(malicious_urls)}):")
    for url in malicious_urls:
        print(f"  - {url}")

    print(f"\nBenign URLs ({len(benign_urls)}):")
    for url in benign_urls:
        print(f"  - {url}")

    write_to_csv(malicious_urls, benign_urls)


if __name__ == "__main__":
    asyncio.run(main())