import nest_asyncio
nest_asyncio.apply()
import os
from dotenv import load_dotenv, find_dotenv
import asyncio
import vt

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
URL_TO_CHECK = "https://www.example.com"
nest_asyncio.apply()

async def get_url_info():
    async with vt.Client(VIRUSTOTAL_API_KEY) as client:
        url_id = vt.url_id(URL_TO_CHECK)
        url = client.get_object("/urls/{}", url_id)  # No await here
        print("URL:", url.url)
        print("Last analysis stats:", url.last_analysis_stats)

if __name__ == "__main__":
    asyncio.run(get_url_info())