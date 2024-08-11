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
from selenium.webdriver.chrome.service import Service

from apify import Actor
from apify_shared.consts import ActorExitCodes

# To run this Actor locally, you need to have the Selenium Chromedriver installed.
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# When running on the Apify platform, it is already included in the Actor's Docker image.

URL = "https://activate-companies.softr.app/"

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
        
        try:
            driver.get(url=URL)
            time.sleep(10)
        except:
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
            return

        # Scroll to the bottom to load more content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(10)

        # Wait for the dynamically loaded elements
        try:
            seemore_element = driver.find_element(By.CSS_SELECTOR, "div.filters-bottom-section button")
            seemore_element.click()
            time.sleep(10)
        except:
            print("No 'see more' element found")

        time.sleep(5)

        # companyName, companySolution, companyWebsite
        Names, Solutions, Websites, Institutions, Otherlinks = False, False, False, False, False

        content_sections = driver.find_elements(By.CSS_SELECTOR, "div.content-section > div > div > div")

        for one_section in content_sections:
            try:
                companyName = one_section.find_element(By.TAG_NAME, "h3").text.strip()
            except Exception as e:
                companyName = ""
                print(f"Error retrieving company name: {e}")

            try:
                companySolution = one_section.find_element(By.CSS_SELECTOR, "div.list-field-element > div > p").text.strip()
            except Exception as e:
                companySolution = ""
                print(f"Error retrieving company description: {e}")

            try:
                companyWebsite = one_section.find_element(By.CSS_SELECTOR, "div.list-field-element > div > div > p > a").get_attribute("href").strip()
            except Exception as e:
                companyWebsite = ""
                print(f"Error retrieving company website: {e}")

            try:
                Actor.log.info(f"Name: {companyName}, Description: {companySolution}, Website: {companyWebsite}")
                await Actor.push_data(
                    {
                        "companyName": companyName,
                        "affiliatedInstitution": "",
                        "companySolution": companySolution,
                        "companyWebsite": companyWebsite,
                        "otherLink": "",
                    }
                )
                Names = True if companyName else Names
                Solutions = True if companySolution else Solutions
                Websites = True if companyWebsite else Websites
            except Exception as e:
                print(f"Error pushing results: {e}")

        if not (Names and Solutions and Websites):
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
        
        driver.quit()
