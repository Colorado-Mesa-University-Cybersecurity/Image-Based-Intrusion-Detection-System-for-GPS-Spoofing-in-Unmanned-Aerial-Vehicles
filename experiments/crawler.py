import nest_asyncio
nest_asyncio.apply()
import os
from dotenv import load_dotenv, find_dotenv
import asyncio
import vt

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

URLS_TO_CHECK = [
    "https://www.example.com",
    "https://www.google.com",
    "https://www.github.com"
]

async def get_url_info(urls):
    async with vt.Client(VIRUSTOTAL_API_KEY) as client:
        for url_str in urls:
            try:
                url_id = vt.url_id(url_str)
                url_obj = client.get_object("/urls/{}", url_id)
                print(f"URL: {url_obj.url}")
                print("Last analysis stats:", url_obj.last_analysis_stats)
                print("-" * 40)
            except Exception as e:
                print(f"Error checking {url_str}: {e}")

if __name__ == "__main__":
    asyncio.run(get_url_info(URLS_TO_CHECK))