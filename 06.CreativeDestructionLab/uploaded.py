"""
This module defines the `main()` coroutine for the Apify Actor, executed from the `__main__.py` file.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

import time
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By

# from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

from apify import Actor
from apify_shared.consts import ActorExitCodes

# To run this Actor locally, you need to have the Selenium Chromedriver installed.
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# When running on the Apify platform, it is already included in the Actor's Docker image.

BASE_URL_LIST = [
    {
        "url": "https://creativedestructionlab.com/companies/?stream=energy"
    },
    {
        "url": "https://creativedestructionlab.com/companies/?stream=climate"
    },
    {
        "url": "https://creativedestructionlab.com/companies/?stream=matter"
    },
    {
        "url": "https://creativedestructionlab.com/companies/?stream=ag"
    },
    {
        "url": "https://creativedestructionlab.com/companies/?stream=oceans"
    },
    {
        "url": "https://creativedestructionlab.com/companies/?stream=space"
    },
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

        otherLinks = []

        for start_url in start_urls:
            
            Actor.log.info(start_url)

            try:
                driver.get(start_url["url"])
                time.sleep(3)
            except:
                e = Exception("The website is changed!")
                await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
                return

            try:
                other_links = [element.get_attribute('href') for element in driver.find_elements(By.XPATH, "//div[@id='companies-container']/div[@class='unit']/a")]
                otherLinks.extend(other_links)
            except NoSuchElementException as e:
                Actor.log.exception(f"No elements found with specified XPath: {e}")
            except WebDriverException as e:
                Actor.log.exception(f"WebDriver error while finding elements: {e}")
            except Exception as e:
                Actor.log.exception(f"An unexpected error occurred: {e}")
                
        Names, Solutions, Websites, Institutions = False, False, False, False
                
        for otherLink in otherLinks:
            try:
                Actor.log.info(f"Webpage-url: ( {otherLink} )")
                driver.get(otherLink)
                time.sleep(0.3)
            except TimeoutException as e:
                Actor.log.exception(f"Timeout while trying to load the page: {e}")
            except WebDriverException as e:
                Actor.log.exception(f"WebDriver error while navigating to the link: {e}")
            except Exception as e:
                Actor.log.exception(f"An unexpected error occurred: {e}")

            try:
                companyName = driver.find_element(By.CSS_SELECTOR, "div.article-body > h2").text
            except NoSuchElementException as e:
                Actor.log.info(f"Company name element not found: {e}")
                companyName = ""
            except WebDriverException as e:
                Actor.log.exception(f"WebDriver error while finding company name: {e}")
                companyName = ""
            except Exception as e:
                Actor.log.exception(f"An unexpected error occurred: {e}")
                companyName = ""

            try:
                companySolution_elements = driver.find_elements(By.CSS_SELECTOR, "div.article-body > p")
                if companySolution_elements:
                    companySolution = "\n".join([solution.text.strip() for solution in companySolution_elements[1:]])
                else:
                    companySolution = ""
            except NoSuchElementException as e:
                Actor.log.info(f"Company solution elements not found: {e}")
                companySolution = ""
            except WebDriverException as e:
                Actor.log.exception(f"WebDriver error while finding company solution elements: {e}")
                companySolution = ""
            except Exception as e:
                Actor.log.exception(f"An unexpected error occurred: {e}")
                companySolution = ""

            try:
                companyWebsite = driver.find_element(By.CSS_SELECTOR, "a.company-website-link").get_attribute('href')
            except NoSuchElementException as e:
                Actor.log.info(f"Company website element not found: {e}")
                companyWebsite = ""
            except WebDriverException as e:
                Actor.log.exception(f"WebDriver error while finding company website: {e}")
                companyWebsite = ""
            except Exception as e:
                Actor.log.exception(f"An unexpected error occurred: {e}")
                companyWebsite = ""

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
                
                Names = True if companyName else Names
                Solutions = True if companySolution else Solutions
                Websites = True if companyWebsite else Websites

            except Exception as e:
                Actor.log.exception(f"Error pushing results: {e}")

        driver.quit()
        
        if not (Names and Solutions and Websites):
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
