"""
This module defines the `main()` coroutine for the Apify Actor, executed from the `__main__.py` file.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

import re
import time
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from apify import Actor

# To run this Actor locally, you need to have the Selenium Chromedriver installed.
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# When running on the Apify platform, it is already included in the Actor's Docker image.

BASE_URL_LIST = [{"url": "https://www.innoenergy.com/discover-innovative-solutions/online-marketplace-for-energy-innovations/"}]

PAGE_URL = "{base_url}?page={page_id}"


def clean_url(url):
    # Define unwanted prefix
    unwanted_prefix = "https://www.innoenergy.com/"
    
    # Remove the unwanted prefix
    if url.startswith(unwanted_prefix):
        url = url[len(unwanted_prefix):]

    # Ensure the URL starts with http:// or https://
    if not re.match(r'http[s]?://', url):
        url = "https://" + url

    return url


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

        # # Process the requests in the queue one by one
        # while request := await default_queue.fetch_next_request():
        #     url = request['url']
        #     depth = request['userData']['depth']
        #     Actor.log.info(f'Scraping {url} ...')

        #     try:
        #         # Open the URL in the Selenium WebDriver
        #         driver.get(url)

        #         # If we haven't reached the max depth,
        #         # look for nested links and enqueue their targets
        #         if depth < max_depth:
        #             for link in driver.find_elements(By.TAG_NAME, 'a'):
        #                 link_href = link.get_attribute('href')
        #                 link_url = urljoin(url, link_href)
        #                 if link_url.startswith(('http://', 'https://')):
        #                     Actor.log.info(f'Enqueuing {link_url} ...')
        #                     await default_queue.add_request({
        #                         'url': link_url,
        #                         'userData': {'depth': depth + 1},
        #                     })

        #         # Push the title of the page into the default dataset
        #         title = driver.title
        #         await Actor.push_data({'url': url, 'title': title})
        #     except Exception:
        #         Actor.log.exception(f'Cannot extract data from {url}.')
        #     finally:
        #         await default_queue.mark_request_as_handled(request)

        base_url = start_urls[0]["url"]

        Actor.log.info(base_url)
        try:
            driver.get(base_url)
            time.sleep(3)
        except TimeoutException:
            print(f"Page load timed out while trying to navigate to {base_url}")
        except WebDriverException as e:
            print(f"WebDriverException occurred while trying to navigate to {base_url}: {e}")

        try:
            driver.find_element(By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click()
            Actor.log.info("Allow all cookies button is clicked.")
            time.sleep(3)
        except:
            pass

        try:
            page_count_element = driver.find_element(By.CSS_SELECTOR, "div[class^='ListPagination_listPaginationItem']")
            Actor.log.info(f"Page Count Str: {page_count_element.text.strip()}")
            page_count = int(page_count_element.text.strip())
            Actor.log.info(f"Page Count: {page_count}")
        except NoSuchElementException:
            page_count = 1
            Actor.log.exception("Page count element not found")
        except ValueError:
            page_count = 1
            Actor.log.exception("Unable to convert page count to integer")
        except WebDriverException as e:
            page_count = 1
            Actor.log.exception(f"WebDriverException occurred: {e}")

        other_link_list = []

        for page_number in range(1, page_count+1):
            page_url = PAGE_URL.format(base_url=base_url, page_id=page_number)

            Actor.log.info(f"Page URL: {page_url}")

            try:
                driver.get(page_url)
                time.sleep(3)
            except TimeoutException:
                print(f"Page load timed out while trying to navigate to {page_url}")
            except WebDriverException as e:
                print(f"WebDriverException occurred while trying to navigate to {page_url}: {e}")

            try:
                elements = driver.find_elements(By.CSS_SELECTOR, "a[class^='ProductListItem_itemTitle']")
                otherLinks = [element.get_attribute('href') for element in elements]
            except NoSuchElementException:
                otherLinks = []
                Actor.log.exception("Product list item elements not found")
            except WebDriverException as e:
                otherLinks = []
                Actor.log.exception(f"WebDriverException occurred: {e}")

            other_link_list.extend(otherLinks)
        
        for otherLink in other_link_list:

            Actor.log.info(f"Other Link: {otherLink}")

            try:
                driver.get(otherLink)
                time.sleep(3)
            except TimeoutException:
                print(f"Page load timed out while trying to navigate to {otherLink}")
            except WebDriverException as e:
                print(f"WebDriverException occurred while trying to navigate to {otherLink}: {e}")

            try:
                companyName = driver.find_element(By.CSS_SELECTOR, "h1[class^='HeroProduct_title']").text.strip()
            except NoSuchElementException:
                companyName = "N/A"
                Actor.log.exception("Company name element not found")
            except WebDriverException as e:
                companyName = "N/A"
                Actor.log.exception(f"WebDriverException occurred while fetching company name: {e}")

            try:
                companySolution = driver.find_element(By.CSS_SELECTOR, "div[class^='HeroProduct_description']").text.strip()
            except NoSuchElementException:
                companySolution = "N/A"
                Actor.log.exception("Company solution element not found")
            except WebDriverException as e:
                companySolution = "N/A"
                Actor.log.exception(f"WebDriverException occurred while fetching company solution: {e}")

            try:
                companyWebsite = driver.find_element(By.CSS_SELECTOR, "a[class^='CommercializedBy_url']").get_attribute('href')
                companyWebsite = clean_url(companyWebsite)
            except NoSuchElementException:
                companyWebsite = "#"
                Actor.log.exception("Company website element not found")
            except WebDriverException as e:
                companyWebsite = "#"
                Actor.log.exception(f"WebDriverException occurred while fetching company website: {e}")

            try:
                Actor.log.info(f"Name: {companyName}, Solution: {companySolution}, Website: {companyWebsite}, Link: {otherLink}")
                await Actor.push_data({"companyName": companyName, "affiliatedInstitution":"", "companySolution": companySolution, "companyWebsite": companyWebsite, "otherLink": otherLink})
            except Exception as e:
                Actor.log.exception(f"Error pushing results: {e}")

        driver.quit()
