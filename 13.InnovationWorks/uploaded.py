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
    {"url": "https://www.innovationworks.org/companies/specialty/energy/"},
    {"url": "https://www.innovationworks.org/companies/specialty/advanced-materials/"},
    {"url": "https://www.innovationworks.org/companies/specialty/hardware/"},
    {"url": "https://www.innovationworks.org/companies/specialty/robotics/"},
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
        
        companyNames = []

        for start_url_obj in start_urls:
            start_url = start_url_obj['url']
            
            try:
                driver.get(start_url)
                time.sleep(3)
            except Exception as e:
                Actor.log.exception(
                    f"An error occurred while navigating to the start URL: {e}"
                )
                continue
            
            company_infos = driver.find_elements(By.CSS_SELECTOR, "div.company-info")
            
            for company_info in company_infos:
                try:
                    companyName = company_info.find_element(By.TAG_NAME, "h2").text.strip()
                except Exception as e:
                    companyName = "N/A"
                    Actor.log.exception(f"Error retrieving company name: {e}")

                companySolution_list = []
                try:
                    for element in company_info.find_elements(By.XPATH, "./p"):
                        if not element.find_elements(By.TAG_NAME, "a"):
                            companySolution_list.append(element.text.strip())
                    companySolution = "\n".join(companySolution_list).strip()
                except Exception as e:
                    companySolution = "N/A"
                    Actor.log.exception(f"Error retrieving company solution: {e}")

                try:
                    companyWebsite = company_info.find_element(By.CSS_SELECTOR, "a.callout-link").get_attribute('href')
                except Exception as e:
                    companyWebsite = "#"
                    Actor.log.warn(f"Error retrieving company website: {e}")

                companyName = companyName or "N/A"
                companySolution = companySolution or "N/A"
                companyWebsite = companyWebsite or "#"
                
                if companyName != "N/A" and companyName in companyNames:
                    continue
                companyNames.append(companyName)
                
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

        driver.quit()
        