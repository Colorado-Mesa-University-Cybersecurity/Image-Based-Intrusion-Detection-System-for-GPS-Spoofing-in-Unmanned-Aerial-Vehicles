import csv
import os
from dotenv import load_dotenv, find_dotenv
import asyncio
import vt
import requests
import json
import socket
import geoip2.database
import whois
import tldextract
from urllib.parse import urlparse

# Configuration
URL_FILE = "urls.txt"
OUTPUT_CSV = "URL_Dataset.csv"
MAX_REDIRECTS = 15
GEOIP_DB_PATH = "../../Datasets/Geo/GeoLite2-Country.mmdb"  # You'll need to download this https://github.com/P3TERX/GeoLite.mmdb?tab=readme-ov-file

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
                if url and not url.startswith('#'):
                    urls.append(url)
        print(f"Loaded {len(urls)} URLs from {filename}")
        return urls
    except Exception as e:
        print(f"Error loading URLs from file: {e}")
        return []


def count_redirects(url):
    try:
        response = requests.head(url, allow_redirects=False, timeout=10)
        redirects = 0
        max_redirects = MAX_REDIRECTS
        final_url = url

        while 'location' in response.headers and redirects < max_redirects:
            redirects += 1
            redirect_url = response.headers['location']

            # Handle relative URLs
            if not redirect_url.startswith('http'):
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                redirect_url = base_url + redirect_url

            final_url = redirect_url
            response = requests.head(redirect_url, allow_redirects=False, timeout=10)

        return redirects, final_url
    except Exception as e:
        print(f"Error counting redirects for {url}: {e}")
        return 0, url


def get_server_info(url):
    try:
        response = requests.head(url, timeout=10)
        server = response.headers.get('Server', 'Unknown')
        content_type = response.headers.get('Content-Type', 'Unknown')
        return {
            'server': server,
            'content_type': content_type,
            'headers': dict(response.headers)
        }
    except Exception as e:
        print(f"Error getting server info for {url}: {e}")
        return {
            'server': 'Error',
            'content_type': 'Error',
            'headers': {}
        }


def get_domain_info(url):
    try:
        extracted = tldextract.extract(url)
        domain = f"{extracted.domain}.{extracted.suffix}"

        # Get WHOIS information
        w = whois.whois(domain)

        # Get IP address
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc
        ip = socket.gethostbyname(hostname)

        # Get country from IP (requires GeoIP2 database)
        country = "Unknown"
        if os.path.exists(GEOIP_DB_PATH):
            try:
                with geoip2.database.Reader(GEOIP_DB_PATH) as reader:
                    response = reader.country(ip)
                    country = response.country.name
            except Exception as e:
                print(f"Error getting country for {ip}: {e}")

        return {
            'domain': domain,
            'ip': ip,
            'country': country,
            'registrar': getattr(w, 'registrar', 'Unknown'),
            'creation_date': getattr(w, 'creation_date', 'Unknown'),
            'expiration_date': getattr(w, 'expiration_date', 'Unknown')
        }
    except Exception as e:
        print(f"Error getting domain info for {url}: {e}")
        return {
            'domain': 'Error',
            'ip': 'Error',
            'country': 'Error',
            'registrar': 'Error',
            'creation_date': 'Error',
            'expiration_date': 'Error'
        }


async def analyze_url(url, vt_client):
    # Initialize results dictionary
    result = {
        'url': url,
        'url_length': len(url),  # Added URL length here
        'vt_malicious': 0,
        'vt_suspicious': 0,
        'gsb_malicious': False,
        'redirects_count': 0,
        'final_url': url,
        'server': 'Unknown',
        'content_type': 'Unknown',
        'domain': 'Unknown',
        'ip': 'Unknown',
        'country': 'Unknown',
        'registrar': 'Unknown',
        'creation_date': 'Unknown',
        'expiration_date': 'Unknown'
    }

    # Check VirusTotal
    try:
        url_id = vt.url_id(url)
        url_obj = await vt_client.get_object_async(f"/urls/{url_id}")
        vt_stats = url_obj.last_analysis_stats
        result['vt_malicious'] = vt_stats.get('malicious', 0)
        result['vt_suspicious'] = vt_stats.get('suspicious', 0)
        print(f"URL: {url}, VT Malicious: {result['vt_malicious']}, Suspicious: {result['vt_suspicious']}")
    except Exception as e:
        print(f"Error checking {url} with VirusTotal: {e}")

    # Check Google Safe Browsing
    gsb_result = check_url_with_google_safe_browsing(url)
    if gsb_result and "matches" in gsb_result and gsb_result["matches"]:
        result['gsb_malicious'] = True
        print(f"URL: {url}, GSB: Malicious")
    else:
        print(f"URL: {url}, GSB: Safe")

    # Get redirect information
    redirects, final_url = count_redirects(url)
    result['redirects_count'] = redirects
    result['final_url'] = final_url
    print(f"URL: {url}, Redirects: {redirects}, Final URL: {final_url}")

    # Get server information
    server_info = get_server_info(final_url)
    result['server'] = server_info['server']
    result['content_type'] = server_info['content_type']
    print(f"URL: {final_url}, Server: {result['server']}, Content Type: {result['content_type']}")

    # Get domain information
    domain_info = get_domain_info(final_url)
    result.update(domain_info)
    print(f"URL: {final_url}, Domain: {result['domain']}, IP: {result['ip']}, Country: {result['country']}")

    # Categorize as Malicious or Benign
    if result['gsb_malicious'] or result['vt_malicious'] >= 5:
        result['category'] = 'Malicious'
    elif result['vt_malicious'] == 0 and result['vt_suspicious'] == 0:
        result['category'] = 'Benign'
    else:
        result['category'] = 'Unknown'

    return result


def write_results_to_csv(results, filename=OUTPUT_CSV):
    # Define CSV headers
    if results:
        fieldnames = results[0].keys()
    else:
        fieldnames = ["url", "url_length", "category", "vt_malicious", "vt_suspicious", "gsb_malicious",
                      "redirects_count", "final_url", "server", "content_type",
                      "domain", "ip", "country", "registrar", "creation_date", "expiration_date"]

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)

        dict_writer = csv.DictWriter(file, fieldnames=fieldnames)
        dict_writer.writeheader()
        dict_writer.writerows(results)


async def main():
    print(f"Using URL file: {URL_FILE}")

    if not os.path.exists(URL_FILE):
        print(f"Error: File '{URL_FILE}' not found. Please create this file with one URL per line.")
        return

    # Check for GeoIP database
    if not os.path.exists(GEOIP_DB_PATH):
        print(f"Warning: GeoIP database file '{GEOIP_DB_PATH}' not found. Country information will be unavailable.")
        print("Download from: https://github.com/P3TERX/GeoLite.mmdb?tab=readme-ov-file")

    urls_to_check = load_urls_from_file(URL_FILE)

    if not urls_to_check:
        print("No URLs to check. Exiting.")
        return

    print(f"Analyzing {len(urls_to_check)} URLs...")

    results = []
    async with vt.Client(VIRUSTOTAL_API_KEY) as client:
        for url in urls_to_check:
            result = await analyze_url(url, client)
            results.append(result)
            print(f"Completed analysis of {url}")

    # Count categories
    categories = {}
    for result in results:
        cat = result['category']
        categories[cat] = categories.get(cat, 0) + 1

    print("\nSummary:")
    for category, count in categories.items():
        print(f"{category}: {count} URLs")

    write_results_to_csv(results)
    print(f"Results written to {OUTPUT_CSV}")


if __name__ == "__main__":
    asyncio.run(main())
