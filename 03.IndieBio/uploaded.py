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
from selenium.common.exceptions import NoSuchElementException, WebDriverException

from apify import Actor
from apify_shared.consts import ActorExitCodes

# To run this Actor locally, you need to have the Selenium Chromedriver installed.
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# When running on the Apify platform, it is already included in the Actor's Docker image.

BASE_URL_LIST = [
    {"url": "https://indiebio.co/companies/?_categories=industrial"},
    {"url": "https://indiebio.co/companies/?_categories=climatetech"},
    {"url": "https://indiebio.co/companies/?_categories=materials"},
    {"url": "https://indiebio.co/companies/?_categories=ag"},
    {"url": "https://indiebio.co/companies/?_categories=food"},
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

        # if not start_urls:
        #     Actor.log.info('No start URLs specified in actor input, exiting...')
        #     await Actor.exit()

        # # Enqueue the starting URLs in the default request queue
        # default_queue = await Actor.open_request_queue()
        # for start_url in start_urls:
        #     url = start_url.get('url')
        #     Actor.log.info(f'Enqueuing {url} ...')
        #     await default_queue.add_request({'url': url, 'userData': {'depth': 0}})

        # Launch a new Selenium Chrome WebDriver
        Actor.log.info('Launching Chrome WebDriver...')
        chrome_options = ChromeOptions()
        if Actor.config.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        
        driver = webdriver.Chrome(options=chrome_options)

        driver.get('http://www.example.com')
        assert driver.title == 'Example Domain'

        result_urls = set()
        
        for URL in BASE_URL_LIST:
            Actor.log.info(f"Working on {URL['url']}")
        
            try:
                driver.get(url=URL["url"])
                time.sleep(10)
            except:
                e = Exception("The website is changed!")
                await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
                return

            try:
                driver.find_element(By.CLASS_NAME, 'pum-close').click()
                time.sleep(3)
            except:
                pass

            try:
                driver.find_element(By.ID, 'wt-cli-accept-all-btn').click()
                time.sleep(3)
            except:
                pass

            data_list = driver.find_elements(By.CSS_SELECTOR, "#companies > div > div.cell.companies-list__content > div.companies-list__items.facetwp-template > div")

            while True:
                length = len(data_list)
                try:
                    driver.find_element(By.CLASS_NAME, "facetwp-load-more").click()
                    Actor.log.info("Clicked 'Load More' button.")
                except:
                    break
                time.sleep(10)

                data_list = driver.find_elements(By.CSS_SELECTOR, "#companies > div > div.cell.companies-list__content > div.companies-list__items.facetwp-template > div")
                if length == len(data_list):
                    break
            
            for data_element in data_list:
                try:
                    href = data_element.find_element(By.CSS_SELECTOR, "div.companies-list__item-title > a").get_attribute('href')
                except NoSuchElementException:
                    href = None
                    Actor.log.exception("Element with the specified CSS selector not found")
                except WebDriverException as e:
                    href = None
                    Actor.log.exception(f"WebDriverException occurred: {e}")

                result_urls.add(href)

        result_urls = list(result_urls)
        
        Names, Solutions, Websites, Institutions = False, False, False, False

        for page_url in result_urls:
            driver.get(page_url)
            time.sleep(3)

            try:
                companyName = driver.find_element(By.CLASS_NAME, "indiebio-company__title").text.strip()
            except NoSuchElementException:
                companyName = ""
                Actor.log.exception("Company name element not found")

            try:
                companySolution = driver.find_element(By.CLASS_NAME, "indiebio-company__tagline").text.strip()
            except NoSuchElementException:
                companySolution = ""
                Actor.log.exception("Company solution element not found")

            try:
                companyWebsite = driver.find_element(By.CSS_SELECTOR, "a.indiebio-company__website").get_attribute('href')
            except NoSuchElementException:
                companyWebsite = ""
                Actor.log.exception("Company website element not found")
            except WebDriverException as e:
                companyWebsite = ""
                Actor.log.exception(f"WebDriverException occurred: {e}")
            
            # print(f"Name: {companyName}, Solution: {companySolution}, Website: {companyWebsite}, otherLink: {page_url}")

            try:
                Actor.log.info(f"Name: {companyName}, Solution: {companySolution}, Website: {companyWebsite}, Link: {page_url}")
                await Actor.push_data({"companyName": companyName, "affiliatedInstitution":"", "companySolution": companySolution, "companyWebsite": companyWebsite, "otherLink": page_url})
                
                Names = True if companyName else Names
                Solutions = True if companySolution else Solutions
                Websites = True if companyWebsite else Websites
                
            except Exception as e:
                print(f"Error pushing results: {e}")

        driver.quit()
        
        if not (Names and Solutions and Websites and Institutions):
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
