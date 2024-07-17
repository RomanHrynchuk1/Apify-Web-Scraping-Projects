"""
This module defines the `main()` coroutine for the Apify Actor, executed from the `__main__.py` file.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from httpx import AsyncClient, HTTPStatusError, RequestError

from apify import Actor

# To run this Actor locally, you need to have the Selenium Chromedriver installed.
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# When running on the Apify platform, it is already included in the Actor's Docker image.

BASE_URL_LIST = [
    {
        "url": "https://engineventures.com/companies"
    },
]


async def main() -> None:
    """
    The main coroutine is being executed using `asyncio.run()`, so do not attempt to make a normal function
    out of it, it will not work. Asynchronous execution is required for communication with Apify platform,
    and it also enhances performance in the field of web scraping significantly.
    """
    async with Actor:
        
        async def get_response(url):
            try:
                # Fetch the content from the URL
                async with AsyncClient() as client:
                    response = await client.get(url, follow_redirects=True)
                    response.raise_for_status()
                return response
            except HTTPStatusError as e:
                print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                return None
            except RequestError as e:
                print(f"Error while requesting {e.request.url}: {e}")
                return None
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                return None

        # Read the Actor input
        actor_input = await Actor.get_input() or {}
        # start_urls = actor_input.get('start_urls', [{'url': 'https://activate-companies.softr.app/'}])
        # max_depth = actor_input.get('max_depth', 1)

        # start_urls = actor_input.get('start_urls', BASE_URL_LIST)
        start_urls = BASE_URL_LIST
        Actor.log.info(f"start_urls: {str(start_urls)}")

        start_url = start_urls[0].get("url", "#")
        response = await get_response(start_url)
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        otherLinks = [element["href"] for element in soup.select("ul#companies-list__results > li > a")]
        
        if not otherLinks:
            Actor.log.critical("Can't find the list elements.")
        
        for otherLink in otherLinks:
            response = await get_response(otherLink)
            soup = BeautifulSoup(response.content, "html.parser")
            
            companyName, companySolution, companyWebsite = None, None, None

            try:
                companyName = soup.select_one("h1.split-topper__title")
                companyName = companyName.text.strip() if companyName else "N/A"
            except Exception as e:
                print(f"An error occurred while extracting company name: {e}")

            try:
                companySolution = soup.select_one("section.content-block")
                companySolution = companySolution.find("p").text.strip() if companySolution else "N/A"
            except Exception as e:
                print(f"An error occurred while extracting company solution: {e}")

            try:
                companyWebsite = soup.select_one("div.company-footer__definition-list a[href*='.']")
                companyWebsite = companyWebsite["href"].strip() if companyWebsite else "#"
            except Exception as e:
                print(f"An error occurred while extracting company website: {e}")

            try:
                Actor.log.info(
                    f"Name: {companyName}, Solution: {companySolution}, Website: {companyWebsite}, Link: {otherLink}"
                )
                await Actor.push_data(
                    {
                        "companyName": companyName,
                        "affiliatedInstitution": "",
                        "companySolution": companySolution,
                        "companyWebsite": companyWebsite,
                        "otherLink": otherLink,
                    }
                )
            except Exception as e:
                Actor.log.exception(f"Error pushing results: {e}")