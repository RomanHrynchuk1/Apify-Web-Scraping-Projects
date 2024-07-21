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

# from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

from apify import Actor

# To run this Actor locally, you need to have the Selenium Chromedriver installed.
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# When running on the Apify platform, it is already included in the Actor's Docker image.

BASE_URL_LIST = [
    {
        "url": "https://chainreaction.anl.gov/innovators/"
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
        
        
        start_url = start_urls[0]["url"]
        
        try:
            driver.get(start_url)
            time.sleep(3)
        except Exception as e:
            Actor.log.exception(f"An error occurred while navigating to the start URL: {e}")

        other_link_s = driver.find_elements(By.CSS_SELECTOR, "section.landing-section article div.feature-block p a")

        otherLinks_d = []
        for url in other_link_s:
            try:
                href = url.get_attribute('href')
                if not url.find_elements(By.TAG_NAME, "img"):
                    otherLinks_d.append(href)
            except Exception as e:
                Actor.log.exception(f"An error occurred while processing a URL: {e}")
        
        otherLinks = list(set(otherLinks_d))
        

        for otherLink in otherLinks:
            
            try:
                driver.get(otherLink)
                time.sleep(0.3)
            except Exception as e:
                Actor.log.exception(f"An error occurred while navigating to the start URL: {e}")


            companyName1_list = driver.find_elements(By.XPATH, "//h3[contains(@class, 'widget-title')]")
            try:
                companyName1 = companyName1_list[0].text.strip() if companyName1_list else ""
            except Exception as e:
                Actor.log.exception(f"An error occurred while extracting companyName1: {e}")
                companyName1 = ""


            companyName2_list = driver.find_elements(By.XPATH, "//*[contains(@class, 'textwidget')]//img")
            try:
                companyName2 = (
                    companyName2_list[0].get_attribute("alt").replace("logo of ", "").replace("Logo of ", "")
                    if companyName2_list else ""
                )
            except Exception as e:
                Actor.log.exception(f"An error occurred while extracting companyName2: {e}")
                companyName2 = ""


            companyName3_list = driver.find_elements(By.XPATH, "//*[contains(@class, 'textwidget')]//a")
            try:
                companyName3 = (
                    companyName3_list[0].get_attribute("title").replace("go to ", "").replace("Go to ", "")
                    if companyName3_list else ""
                )
            except Exception as e:
                Actor.log.exception(f"An error occurred while extracting companyName3: {e}")
                companyName3 = ""


            companyName = companyName1 or companyName2 or companyName3


            companySolution_list = driver.find_elements(By.XPATH, "//*[contains(@class, 'general-deck')]")
            try:
                companySolution = companySolution_list[0].text.strip() if companySolution_list else "N/A"
            except Exception as e:
                Actor.log.exception(f"An error occurred while extracting companySolution: {e}")
                companySolution = "N/A"


            companyWebsite_list = driver.find_elements(By.CSS_SELECTOR, ".textwidget ul li a[href*='http']")
            companyWebsite = ""
            for website in companyWebsite_list:
                try:
                    if website.text.strip().lower() == "website":
                        companyWebsite = website.get_attribute("href")
                        if companyWebsite:
                            break  # Exit loop once the desired link is found
                except Exception as e:
                    Actor.log.exception(f"An error occurred while extracting companyWebsite: {e}")


            companyName = companyName or companyWebsite or "N/A"
            companyWebsite = companyWebsite or "#"
            
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

        driver.quit()
        
