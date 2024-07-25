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

from bs4 import BeautifulSoup

# # from selenium.webdriver.chrome.service import Service
# from selenium.common.exceptions import (
#     TimeoutException,
#     NoSuchElementException,
#     WebDriverException,
# )

from apify import Actor

# To run this Actor locally, you need to have the Selenium Chromedriver installed.
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# When running on the Apify platform, it is already included in the Actor's Docker image.

BASE_URL_LIST = [
    {"url": "https://www.marsdd.com/who-we-work-with/"},
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
        except Exception as e:
            Actor.log.exception(
                f"An error occurred while navigating to the start URL: {e}"
            )
            return

        try:
            cancel_button = driver.find_element(By.ID, "onesignal-slidedown-cancel-button")
            cancel_button.click()
            time.sleep(0.5)
            Actor.log.info("OneSignal cancel button is clicked.")
        except Exception as e:
            Actor.log.warn("OneSignal cancel button not found or not clickable:", e)

        try:
            element = driver.find_element(By.CSS_SELECTOR, "li.allVentures__filter-list-option")
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            element.click()
            time.sleep(0.5)
            Actor.log.info("The filter option drop-down button is clicked.")
        except Exception as e:
            Actor.log.exception("An error occurred while clicking the filter option drop-down:", e)

        try:
            element = driver.find_element(By.CSS_SELECTOR, "li[data-text='cleantech']")
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            element.click()
            time.sleep(3)
            Actor.log.info("The 'cleantech' filter option is clicked.")
        except Exception as e:
            Actor.log.exception("An error occurred while clicking the 'cleantech' filter option:", e)


        while True:
            try:
                load_more_button = driver.find_element(By.XPATH, "//a[@data-url and @class='button button--tertiary']")
                # Scroll the element into view
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                time.sleep(0.5)
                load_more_button.click()
                time.sleep(3)
            except Exception as ex:
                Actor.log.warn("End of the `load more` button. (or Error!)")
                break
            
            
        try:
            soup = BeautifulSoup(driver.page_source, "html.parser")

            elements = soup.select("a.allVentures__link")

            for element in elements:
                try:
                    companyName = element.select_one("div.allVentures__Description h3").text.strip()
                except AttributeError:
                    companyName = "N/A"
                    Actor.log.exception(f"Warning: h3 element not found for a company link")

                try:
                    companySolution = element.select_one("div.allVentures__Description p").text.strip()
                except AttributeError:
                    companySolution = "N/A"
                    Actor.log.warn(f"Warning: p element not found for a company link")

                try:
                    companyWebsite = element.get('href')
                except KeyError:
                    companyWebsite = "#"
                    Actor.log.warn(f"Warning: href attribute not found for a company link")

                companyName = companyName or "N/A"
                companySolution = companySolution or "N/A"
                companyWebsite = companyWebsite or "#"
                
                try:
                    Actor.log.info(
                        f"Name: {companyName}, Solution: {companySolution}, Website: {companyWebsite}"
                    )
                    await Actor.push_data(
                        {
                            "companyName": companyName,
                            "affiliatedInstitution": "N/A",
                            "companySolution": companySolution,
                            "companyWebsite": companyWebsite,
                            "otherLink": "#",
                        }
                    )
                except Exception as e:
                    Actor.log.exception(f"Error pushing results: {e}")
                
        except Exception as e:
            Actor.log.exception(f"An error occurred: {e}")

        driver.quit()
