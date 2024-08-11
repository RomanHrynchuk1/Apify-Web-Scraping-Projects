"""
This module defines the `main()` coroutine for the Apify Actor, executed from the `__main__.py` file.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

import time
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By

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
    {"url": "https://eitrawmaterials.eu/startups-portfolio/"},
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

        # Attempt to click the cookie consent button with try-except
        try:
            driver.find_element(By.ID, "CybotCookiebotDialogBodyButtonAccept").click()
            time.sleep(1)  # Consider replacing this with an explicit wait
        except Exception as e:
            Actor.log.exception(
                f"An error occurred while trying to click the cookie consent button: {e}"
            )
        
        otherLinks = []

        while True:
            try:
                articles = driver.find_elements(By.CSS_SELECTOR, "article.eit-startups-carret")
                for article in articles:
                    try:
                        link = article.find_element(By.CSS_SELECTOR, "a.eit-startup-link").get_attribute("href")
                        if link.find('supportedstartups') > -1:
                            otherLinks.append(link)
                    except Exception as ex:
                        Actor.log.exception(f"Error retrieving link from article: {ex}")
                
                next_button = driver.find_element(By.CSS_SELECTOR, "a.next.page-numbers")
                next_button.click()
                time.sleep(0.3)
            except Exception as ex:
                Actor.log.warn(f"End of page or an error occurred. Found {len(otherLinks)} companies. Error: {ex}")
                break

        Names, Solutions, Websites, Institutions = False, False, False, False

        for otherLink in otherLinks:
            try:
                driver.get(otherLink)
                time.sleep(0.3)
                
                try:
                    companyName = driver.find_element(By.CSS_SELECTOR, "h2.entry-title").text.strip()
                except Exception as e:
                    companyName = ""
                    Actor.log.exception(f"Error retrieving company name: {e}")

                try:
                    companySolution = driver.find_element(By.CSS_SELECTOR, "div.post-content p").text.strip()
                except Exception as e:
                    companySolution = ""
                    Actor.log.warn(f"Error retrieving company solution: {e}")

                try:
                    companyWebsite_dummy = driver.find_elements(By.CSS_SELECTOR, 'div.inline-field')
                    companyWebsite = ""
                    for dummy in companyWebsite_dummy:
                        try:
                            if dummy.find_element(By.CSS_SELECTOR, "span.label").text.strip().lower() == "website:":
                                companyWebsite = dummy.find_element(By.CSS_SELECTOR, "span.content a").get_attribute('href') or ""
                                break
                        except Exception as e:
                            Actor.log.exception(f"Error processing company website dummy element: {e}")
                    if companyWebsite == "":
                        Actor.log.warn(f"Error retrieving company website: {e}")
                except Exception as e:
                    companyWebsite = ""
                    Actor.log.warn(f"Error retrieving company website: {e}")

                companyName = companyName or ""
                companySolution = companySolution or ""
                companyWebsite = companyWebsite or ""
                
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

            except Exception as e:
                Actor.log.exception(f"Error navigating to {otherLink}: {e}")
                
        driver.quit()
        
        if not (Names and Solutions and Websites):
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
