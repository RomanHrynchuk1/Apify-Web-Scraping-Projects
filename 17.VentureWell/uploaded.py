"""
This module defines the `main()` coroutine for the Apify Actor, executed from the `__main__.py` file.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

import time
# from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
# from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup

# # from selenium.webdriver.chrome.service import Service
# from selenium.common.exceptions import (
#     TimeoutException,
#     NoSuchElementException,
#     WebDriverException,
# )

from apify import Actor
from apify_shared.consts import ActorExitCodes

# To run this Actor locally, you need to have the Selenium Chromedriver installed.
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# When running on the Apify platform, it is already included in the Actor's Docker image.

BASE_URL_LIST = [
    {"url": "https://venturewell.org/e-team-grantees/#?sectors=Energy%20%26%20Materials&sectors=Environment&sectors=Infrastructure%2FBuilding&sectors=Manufacturing&sectors=Sanitation%2FWater&sectors=Transportation%2FDriver%20Safety%2FAutomotive&sectors=Agriculture&vw="},
]


async def main() -> None:
    """
    The main coroutine is being executed using `asyncio.run()`, so do not attempt to make a normal function
    out of it, it will not work. Asynchronous execution is required for communication with Apify platform,
    and it also enhances performance in the field of web scraping significantly.
    """
    async with Actor:
        # Read the Actor input
        actor_input = await Actor.get_input() or {}
        # start_urls = actor_input.get('start_urls', [{'url': 'https://activate-companies.softr.app/'}])
        # max_depth = actor_input.get('max_depth', 1)

        # start_urls = actor_input.get('start_urls', BASE_URL_LIST)
        start_urls = BASE_URL_LIST
        Actor.log.info(f"start_urls: {str(start_urls)}")

        # Launch a new Selenium Chrome WebDriver
        Actor.log.info("Launching Chrome WebDriver...")
        chrome_options = ChromeOptions()
        if Actor.config.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_options.add_argument("--blink-settings=imagesEnabled=false")

        driver = webdriver.Chrome(options=chrome_options)

        driver.get("http://www.example.com")
        assert driver.title == "Example Domain"

        start_url = start_urls[0]["url"]

        try:
            driver.get(start_url)
            time.sleep(3)
        except:
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
            return

        page_source = driver.page_source
        
        soup = BeautifulSoup(page_source, "html.parser")
        
        elements = soup.select("div.cards__card__back")
        
        Names, Solutions, Websites, Institutions = False, False, False, False
        
        for element in elements:
            try:
                companyName = element.select_one("h1").text.strip()
            except Exception as e:
                Actor.log.exception(f"An error occurred while extracting companyName: {e}")
                companyName = ""
            
            try:
                companySolution = element.select_one("p:not(.cards__card__lower__bottom__institution):not(.cards__card__back__website)").text.strip()
            except Exception as e:
                Actor.log.warn(f"An error occurred while extracting companySolution: {e}")
                companySolution = ""
            
            try:
                companyWebsite = element.select_one("p.cards__card__back__website a").get('href')
            except Exception as e:
                Actor.log.warn(f"An error occurred while extracting companyWebsite: {e}")
                companyWebsite = ""
            
            try:
                affiliatedInstitution = element.select_one("p.cards__card__lower__bottom__institution").text.strip()
            except Exception as e:
                Actor.log.warn(f"An error occurred while extracting affiliatedInstitution: {e}")
                affiliatedInstitution = ""
            
            try:
                Actor.log.info(
                    f"Name: {companyName}; Institution: {affiliatedInstitution}; Solution: {companySolution}; Website: {companyWebsite}"
                )
                await Actor.push_data(
                    {
                        "companyName": companyName,
                        "affiliatedInstitution": affiliatedInstitution,
                        "companySolution": companySolution,
                        "companyWebsite": companyWebsite,
                        "otherLink": "",
                    }
                )
                
                Names = True if companyName else Names
                Solutions = True if companySolution else Solutions
                Websites = True if companyWebsite else Websites
                Institutions = True if affiliatedInstitution else Institutions

            except Exception as e:
                Actor.log.exception(f"Error pushing results: {e}")
                
        driver.quit()

        if not (Names and Solutions and Websites and Institutions):
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
