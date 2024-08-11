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
from selenium.webdriver.common.by import By

# from bs4 import BeautifulSoup

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
    {"url": "https://www.joinef.com/portfolio/?filter-industry=ar-vr-xr,automotive,b2b,climate-or-environment,computing,electrical-infrastructure,energy,environmental-science,food-agriculture-or-farming,hardware,manufacturing-or-industrial,military-or-defense,robotics-iot,space,supply-chain-transportation-or-logistics,sustainability"},
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

        try:
            driver.find_element(By.CSS_SELECTOR, "button.cky-btn-accept").click()
            Actor.log.info()
            time.sleep(1)
        except Exception as e:
            Actor.log.exception(
                f"An error occurred while attempting to click on `Accept cookies` button."
            )
        
        while True:
            try:
                load_more_button = driver.find_element(By.CSS_SELECTOR, "a.btn--loadmore")
                load_more_button.click()
                time.sleep(3)
            except Exception as e:
                Actor.log.info(
                    f"May be the end of `loading more` elements, or An error: {e}"
                )
                break
        
        Names, Solutions, Websites, Institutions = False, False, False, False
        
        elements = driver.find_elements(By.CSS_SELECTOR, "div.tile--company--row a.tile__link")
        Actor.log.info(f"{len(elements)} elements are found.")
        otherLinks = []
        for element in elements:
            try:
                href = element.get_attribute('href')
                otherLinks.append(href)
            except Exception as ex:
                Actor.log.exception(f"Unexpected Error: {ex}")
        
        for otherLink in otherLinks:
            try:
                driver.get(otherLink)
                time.sleep(0.3)
            except Exception as e:
                Actor.log.exception(f"An error occurred while opening: {href or 'None'}")
                continue
            
            try:
                companyName = driver.find_element(By.CSS_SELECTOR, "h1.pageheader__heading").text.strip()
            except Exception as e:
                Actor.log.exception(f"An error occurred while extracting companyName: {e}")
                companyName = ""
            try:
                companySolution = driver.find_element(By.CSS_SELECTOR, "div.company__longbio").text.strip()
            except Exception as e:
                Actor.log.warn(f"An error occurred while extracting companySolution: {e}")
                companySolution = ""
            
            try:
                companyWebsite = driver.find_element(By.CSS_SELECTOR, "a.pageheader__websitebtn").get_attribute('href')
            except Exception as e:
                Actor.log.warn(f"An error occurred while extracting companyWebsite: {e}")
                companyWebsite = ""
                
            companyName = companyName or ""
            companySolution = companySolution or ""
            companyWebsite = companyWebsite or ""
            
            try:
                Actor.log.info(
                    f"Name: {companyName}; Solution: {companySolution}; Website: {companyWebsite}; OtherLink: {otherLink}"
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
                
                Names = True if companyName else Names
                Solutions = True if companySolution else Solutions
                Websites = True if companyWebsite else Websites

            except Exception as e:
                Actor.log.exception(f"Error pushing results: {e}")
                
        driver.quit()

        if not (Names and Solutions and Websites):
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
