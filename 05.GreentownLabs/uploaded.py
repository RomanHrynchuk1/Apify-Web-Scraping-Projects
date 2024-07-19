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

# To run this Actor locally, you need to have the Selenium Chromedriver installed.
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# When running on the Apify platform, it is already included in the Actor's Docker image.

BASE_URL_LIST = [
    {
        "url": "https://greentownlabs.com/members/page/1/?cat=all&location=houston&status=current"
    },
    {
        "url": "https://greentownlabs.com/members/page/1/?cat=all&location=boston&status=current"
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
        Actor.log.info("Launching Chrome WebDriver...")
        chrome_options = ChromeOptions()
        if Actor.config.headless:
            Actor.log.warning(
                "This script shouldn't be run in headless mode. So I didn't enabled headless mode.\n"
            )
            # chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")

        driver = webdriver.Chrome(options=chrome_options)

        driver.get("http://www.example.com")
        assert driver.title == "Example Domain"

        
        otherLinks_final = []
        
        for start_url in start_urls:

            Actor.log.info(start_url)

            try:
                driver.get(start_url["url"])
                time.sleep(3)
            except TimeoutException as e:
                Actor.log.exception(f"Timeout while trying to load the page: {e}")
            except NoSuchElementException as e:
                Actor.log.exception(f"Element not found: {e}")
            except WebDriverException as e:
                Actor.log.exception(f"WebDriver error: {e}")

            try:
                # Locate the host element
                shadow_host = driver.find_element(By.CSS_SELECTOR, "#usercentrics-root")
                try:
                    # Script to access Shadow Root and find the button
                    script = """
                    return arguments[0].shadowRoot.querySelector('button[data-testid="uc-accept-all-button"]');
                    """
                    # Execute script with the host element as argument
                    button_element = driver.execute_script(script, shadow_host)

                    try:
                        # Interact with the button_element (click on it)
                        button_element.click()
                        time.sleep(5)
                    except AttributeError as e:
                        Actor.log.info(f"Button element is not found: {e}")
                    except WebDriverException as e:
                        Actor.log.exception(
                            f"WebDriver error while clicking the button: {e}"
                        )

                except WebDriverException as e:
                    Actor.log.exception(f"WebDriver error while executing script: {e}")

            except NoSuchElementException as e:
                Actor.log.info(f"Shadow host element not found: {e}")
            except WebDriverException as e:
                Actor.log.exception(f"WebDriver error while locating shadow host: {e}")

            
            try:
                otherLinks = [
                    element.get_attribute("href")
                    for element in driver.find_elements(
                        By.XPATH, "//a[contains(@class, 'card') and @rel='bookmark']"
                    )
                ]
                otherLinks_final.extend(otherLinks)
            except NoSuchElementException as e:
                Actor.log.exception(f"No elements found with specified XPath: {e}")
            except WebDriverException as e:
                Actor.log.exception(f"WebDriver error while finding elements: {e}")

            try:
                # Scroll to the bottom to click the next button.
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            except WebDriverException as e:
                Actor.log.info(f"WebDriver error while scrolling: {e}")

            while True:
                try:
                    driver.find_element(
                        By.XPATH, "//a[@class='next page-numbers']"
                    ).click()
                    time.sleep(5)
                    try:
                        new_links = [
                            element.get_attribute("href")
                            for element in driver.find_elements(
                                By.XPATH,
                                "//a[contains(@class, 'card') and @rel='bookmark']",
                            )
                        ]
                        otherLinks_final.extend(new_links)
                    except NoSuchElementException as e:
                        Actor.log.exception(
                            f"No elements found with specified XPath: {e}"
                        )
                    except WebDriverException as e:
                        Actor.log.exception(
                            f"WebDriver error while finding elements: {e}"
                        )
                except NoSuchElementException:
                    Actor.log.info("Next button not found. Ending pagination.")
                    break
                except WebDriverException as e:
                    Actor.log.exception(f"WebDriver error: {e}")
                    break
                except Exception as e:
                    Actor.log.exception(f"An unexpected error occurred: {e}")
                    break

        driver.delete_all_cookies()
        driver.quit()
        
        chrome_options.add_experimental_option("prefs", {'profile.managed_default_content_settings.javascript': 2})
        driver = webdriver.Chrome(options=chrome_options)
        
        for other_link in otherLinks_final:

            try:
                driver.get(other_link)
                time.sleep(0.3)
            except TimeoutException as e:
                Actor.log.exception(f"Timeout while trying to load the page: {e}")
            except WebDriverException as e:
                Actor.log.exception(
                    f"WebDriver error while navigating to the link: {e}"
                )
            except Exception as e:
                Actor.log.exception(f"An unexpected error occurred: {e}")

            try:
                companyName = driver.find_element(
                    By.CSS_SELECTOR, "h1.entry-title"
                ).text
            except NoSuchElementException as e:
                Actor.log.info(f"Company name element not found: {e}")
                companyName = "N/A"
            except WebDriverException as e:
                Actor.log.exception(
                    f"WebDriver error while finding company name: {e}"
                )
                companyName = "N/A"

            try:
                companySolutionList1 = driver.find_elements(
                    By.CSS_SELECTOR, "div.response-answer"
                )
                companySolutionList2 = driver.find_elements(
                    By.CSS_SELECTOR, "div.entry-content > p"
                )
                companySolution = (
                    companySolutionList1[0].text
                    if companySolutionList1
                    else (
                        companySolutionList2[0].text
                        if companySolutionList2
                        else None
                    )
                )
                if not companySolution:
                    Actor.log.warning("Can't find the companySolution.")
            except NoSuchElementException as e:
                Actor.log.info(f"Fallback company solution element not found: {e}")
                companySolution = "N/A"
            except WebDriverException as e:
                Actor.log.exception(
                    f"WebDriver error while finding fallback company solution: {e}"
                )
                companySolution = "N/A"
            except Exception as e:
                Actor.log.exception(f"An unexpected error occurred: {e}")

            try:
                companyWebsite = driver.find_element(
                    By.XPATH,
                    "//div[@class = 'notch-content']//a[@class = 'button button-orange']",
                ).get_attribute("href")
            except NoSuchElementException as e:
                Actor.log.info(f"Company website element not found: {e}")
                companyWebsite = "#"
            except WebDriverException as e:
                Actor.log.exception(
                    f"WebDriver error while finding company website: {e}"
                )
                companyWebsite = "#"

            try:
                Actor.log.info(
                    f"Name: {companyName}, Solution: {companySolution}, Website: {companyWebsite}, Link: {other_link}"
                )
                await Actor.push_data(
                    {
                        "companyName": companyName,
                        "affiliatedInstitution": "",
                        "companySolution": companySolution,
                        "companyWebsite": companyWebsite,
                        "otherLink": other_link,
                    }
                )
            except Exception as e:
                Actor.log.exception(f"Error pushing results: {e}")

        driver.quit()
