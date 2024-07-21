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

# To run this Actor locally, you need to have the Selenium Chromedriver installed.
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# When running on the Apify platform, it is already included in the Actor's Docker image.

BASE_URL_LIST = [
    {"url": "https://www.hightechcampus.com/companies?category=4"},
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
            Actor.log.warn("This actor should run on no-headless mode.")
            # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_options.add_argument("--blink-settings=imagesEnabled=false")

        driver = webdriver.Chrome(options=chrome_options)

        driver.get("http://www.example.com")
        assert driver.title == "Example Domain"

        start_url = start_urls[0]["url"]

        try:
            driver.get(start_url)
            time.sleep(5)
        except Exception as e:
            Actor.log.exception(
                f"An error occurred while navigating to the start URL: {e}"
            )

        # Attempt to click the cookie consent button with try-except
        try:
            driver.find_element(
                By.CSS_SELECTOR,
                "button#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
            ).click()
            time.sleep(3)  # Consider replacing this with an explicit wait
        except Exception as e:
            Actor.log.exception(
                f"An error occurred while trying to click the cookie consent button: {e}"
            )

        # Attempt to find and click the down arrow
        try:
            down_arrow = driver.find_element(By.CSS_SELECTOR, "svg.arrows")
            down_arrow.click()
            time.sleep(2)  # Consider replacing this with an explicit wait
        except Exception as e:
            Actor.log.exception(
                f"An error occurred while trying to click the down arrow: {e}"
            )

        otherLinks = []

        while True:
            try:
                new_link_elements = driver.find_elements(
                    By.CSS_SELECTOR,
                    "section.companies>div.container>div.reveal-item>div>a",
                )
                for element in new_link_elements:
                    otherLinks.append(element.get_attribute("href"))

                next_button = driver.find_element(
                    By.CSS_SELECTOR, "a.page-link[rel='next']"
                )
                if not next_button.is_displayed():
                    driver.execute_script(
                        "arguments[0].scrollIntoView(true);", next_button
                    )
                    time.sleep(0.3)
                next_button.click()
                time.sleep(3)
            except Exception as ex:
                Actor.log.info(
                    f"The last page. {len(otherLinks)} companies are discovered."
                )
                break

        for otherLink in otherLinks:
            driver.get(otherLink)
            time.sleep(0.3)

            try:
                companyName = driver.find_element(
                    By.CSS_SELECTOR, "h4.green"
                ).text.strip()
            except Exception as ex:
                companyName = "N/A"
                Actor.log.warn(f"Error retrieving companyName: {ex}")

            try:
                companySolution = driver.find_element(
                    By.CSS_SELECTOR, "div.text"
                ).text.strip()
            except Exception as ex:
                companySolution = "N/A"
                Actor.log.warn(f"Error retrieving companySolution: {ex}")

            try:
                companyWebsite = driver.find_element(
                    By.CSS_SELECTOR, "div.item--block a.button__standard"
                ).get_attribute("href")
            except Exception as ex:
                companyWebsite = "#"
                Actor.log.warn(f"Error retrieving companyWebsite: {ex}")

            try:
                Actor.log.info(
                    f"Name: {companyName}, Solution: {companySolution}, Website: {companyWebsite}, Link: {otherLink}"
                )
                await Actor.push_data(
                    {
                        "companyName": companyName,
                        "affiliatedInstitution": "N/A",
                        "companySolution": companySolution,
                        "companyWebsite": companyWebsite,
                        "otherLink": otherLink,
                    }
                )
            except Exception as e:
                Actor.log.exception(f"Error pushing results: {e}")

        driver.quit()
