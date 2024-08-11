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
    {
        "url": "https://airtable.com/shrnrY299XgL7faqe/tblXwSVREDEJH7QLT"
    },
]


def ensure_https(url):
    if url and not url.startswith(('https://', 'http://')):
        return 'https://' + url
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
            time.sleep(5)
        except:
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
            return
            
        try:
            main_element = driver.find_element(By.CSS_SELECTOR, "div.light-scrollbar")
        except Exception as e:
            Actor.log.exception(f"An error occurred while finding the main element: {e}")
            main_element = None

        # Remove the 'light-scrollbar' class using JavaScript
        try:
            driver.execute_script("arguments[0].classList.remove('light-scrollbar');", main_element)
            time.sleep(1)  # Consider replacing this with an explicit wait
        except Exception as e:
            Actor.log.exception(f"An error occurred while removing the 'light-scrollbar' class: {e}")


        # Function to get the current scroll position and scroll height
        def get_scroll_info(element):
            return driver.execute_script("""
                return {
                    scrollTop: arguments[0].scrollTop,
                    scrollHeight: arguments[0].scrollHeight,
                    clientHeight: arguments[0].clientHeight
                };
            """, element)

        companyNameList = []
        Names, Solutions, Websites, Institutions = False, False, False, False

        # Scroll down 400px at a time until the bottom is reached
        while True:
            elements = main_element.find_elements(By.CSS_SELECTOR, "div.galleryCardContainer")
            for element in elements:
                element_list = element.find_elements(By.XPATH, ".//div[@role='presentation']/div/div")
                if len(element_list) == 5:
                    try:
                        companyName = element_list[1].text.strip() or ""
                    except Exception as e:
                        Actor.log.exception(f"An error occurred while extracting companyName: {e}")
                        companyName = ""
                    
                    try:
                        otherLink = element_list[1].find_element(By.TAG_NAME, "a").get_attribute("href") or ""
                    except Exception as e:
                        Actor.log.exception(f"An error occurred while extracting otherLink: {e}")
                        otherLink = ""
                    
                    try:
                        companySolution = element_list[2].find_element(By.CSS_SELECTOR, "div.cellContainer").text.strip() or ""
                    except Exception as e:
                        Actor.log.info(f"An error occurred while extracting companySolution: {e}")
                        companySolution = ""
                    
                    try:
                        companyWebsite = element_list[3].find_element(By.CSS_SELECTOR, "div.cellContainer").text.strip() or ""
                        companyWebsite = ensure_https(companyWebsite)
                    except Exception as e:
                        Actor.log.info(f"An error occurred while extracting companyWebsite: {e}")
                        companyWebsite = ""
                        
                    if companyName in companyNameList:
                        continue
                    
                    companyNameList.append(companyName)
                    
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
                                "otherLink": "",  # Not include because it's airtable link.
                            }
                        )
                        
                        Names = True if companyName else Names
                        Solutions = True if companySolution else Solutions
                        Websites = True if companyWebsite else Websites

                    except Exception as e:
                        Actor.log.exception(f"Error pushing results: {e}")
                else:
                    Actor.log.warning(f"Warning! The size of element-list is {len(element_list)}")
            
            scroll_info = get_scroll_info(main_element)
            scroll_top = scroll_info['scrollTop']
            scroll_height = scroll_info['scrollHeight']
            client_height = scroll_info['clientHeight']
            
            # Break the loop if we've reached the bottom
            if scroll_top + client_height >= scroll_height:
                break
            
            # Scroll down 400px
            driver.execute_script("arguments[0].scrollBy(0, 400);", main_element)
            time.sleep(0.5)

        driver.quit()
        
        if not (Names and Solutions and Websites):
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
