"""
This module defines the `main()` coroutine for the Apify Actor, executed from the `__main__.py` file.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from apify import Actor
from apify_shared.consts import ActorExitCodes


BASE_URL_LIST = [
    {"url": "https://www.plugandplaytechcenter.com/innovation-services/startups/our-startups"},
]

industries = [
    ("Advanced Manufacturing", 1),  # 1
    ("Aerospace & Defense", 1),  # 2
    ("Agtech", 1),  # 3
    ("Deeptech", 4),  # 7
    ("Energy", 1),  # 8
    ("Maritime", 7),  # 15
    ("Mobility", 3),  # 18
    ("New Materials & Packaging", 1),  # 19
    ("Semiconductors", 2),  # 21
    ("Smart Cities", 1),  # 22
    ("Sustainability", 3),  # 25
]


def initialize_webdriver():
    """Initialize the Selenium WebDriver with appropriate options."""
    chrome_options = ChromeOptions()
    if Actor.config.headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    
    return webdriver.Chrome(options=chrome_options)

def click_element_not_working(driver, element):
    """Attempt to click an element, scrolling into view if necessary."""
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element)).click()
    except TimeoutException:
        Actor.log.warning("Element was not clickable in time, trying a direct click.")
        try:
            element.click()
        except Exception as e:
            Actor.log.exception("An error occurred while clicking the element.")
    except Exception as e:
        Actor.log.exception(f"Error in click_element: {e}")
        
def click_element(driver, element):
    """Attempt to click an element, scrolling into view if necessary."""
    try:
        # Scroll the element into view
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        
        # Wait for the element to be clickable
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element))
        
        # Use ActionChains to move to the element and click
        actions = ActionChains(driver)
        actions.move_to_element(element).click().perform()
        
    except TimeoutException:
        Actor.log.warning("Element was not clickable in time, trying a direct click.")
        try:
            # As a fallback, try clicking the element directly
            element.click()
        except Exception as e:
            Actor.log.exception("An error occurred while clicking the element.")
            
    except Exception as e:
        Actor.log.exception(f"Error in click_element: {e}")
    
    return
    
    # Fallback to click using JavaScript if all else fails
    try:
        driver.execute_script("arguments[0].click();", element)
    except Exception as e:
        Actor.log.exception(f"JavaScript click also failed: {e}")

def handle_cookies(driver):
    """Handle cookie acceptance."""
    try:
        driver.find_element(By.CSS_SELECTOR, "button#onetrust-accept-btn-handler").click()
        Actor.log.info("Accept All Cookies button is clicked.")
        time.sleep(1)
    except Exception as e:
        Actor.log.warn("An error occurred while attempting to click on 'Accept cookies' button.")

def navigate_to_url(driver, url):
    """Navigate to the given URL and handle any exceptions."""
    try:
        driver.get(url)
        time.sleep(3)
    except Exception as e:
        Actor.log.exception(f"An error occurred while navigating to {url}: {e}")
        return False
    return True

def extract_industry_links(driver):
    """Extract all industry-related links from the page."""
    other_links = []
    
    for industry, index_diff in industries:
        try:
            industries_dropdown = driver.find_element(By.CSS_SELECTOR, "select#cbxIndustries")
            click_element(driver, industries_dropdown)
            time.sleep(1)
            for _ in range(index_diff):
                industries_dropdown.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.3)
            time.sleep(1)
            industries_dropdown.send_keys(Keys.ENTER)
            time.sleep(1)
        except Exception as e:
            Actor.log.exception(f"An error occurred while selecting industry ({industry}) : {e}")
            continue
        
        while True:
            try:
                other_link_elements = driver.find_elements(By.CSS_SELECTOR, "pnp-startup-card a")
                for element in other_link_elements:
                    other_links.append(element.get_attribute('href'))
                
                next_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Next ->')]")
                next_button.click()
                Actor.log.info("Next button (page navigation) button is clicked.")
                time.sleep(2)
            except Exception as e:
                Actor.log.warn("An error occurred while navigating pages or extracting links. Maybe, it's the end of navigation")
                break
            
    return other_links

def extract_company_info(driver, url):
    """Extract company information from the given URL."""
    try:
        driver.get(url)
        time.sleep(0.3)
    except Exception as e:
        Actor.log.exception(f"An error occurred while opening: {url}")
        return None

    company_name = ""
    
    for is_second_iter in (False, True):
        try:
            company_name = driver.find_element(By.CSS_SELECTOR, "h1.pnp-text-primary").text.strip()
            break
        except Exception as e:
            if is_second_iter: 
                Actor.log.warning(f"An error occurred while extracting company name: {e}")
                company_name = ""
            else:
                time.sleep(0.3)

    try:
        company_solution = driver.find_element(By.CSS_SELECTOR, "div.items-start p.pnp-text-primary").text.strip()
    except Exception as e:
        Actor.log.warning(f"An error occurred while extracting company solution: {e}")
        company_solution = ""

    if not company_name:
        try:
            Actor.log.info("Get Company Name from Company Solution.")
            solution_list = company_solution.split()
            company_name = solution_list[0]
            for i in range(1, len(solution_list)):
                if solution_list[i][0].islower():
                    break
                company_name += f" {solution_list[i]}"
            Actor.log.info(f"Company Name: {company_name}")
        except Exception as e:
            Actor.log.warning(f"Getting Company Name from Company Solution is faild.")
    
    try:
        company_website = driver.find_element(By.CSS_SELECTOR, "a.nav-link.pnp-link").get_attribute('href')
    except Exception as e:
        Actor.log.warning(f"An error occurred while extracting company website: {e}")
        company_website = ""

    return {
        "companyName": company_name,
        "affiliatedInstitution": "",
        "companySolution": company_solution,
        "companyWebsite": company_website,
        "otherLink": url,
    }

async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() or {}
        start_urls = BASE_URL_LIST
        Actor.log.info(f"Start URLs: {str(start_urls)}")

        Actor.log.info("Launching Chrome WebDriver...")
        driver = initialize_webdriver()
        
        start_url = start_urls[0]["url"]

        if not navigate_to_url(driver, start_url):
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
            return
        
        handle_cookies(driver)

        other_links = extract_industry_links(driver)

        Names, Solutions, Websites, Institutions = False, False, False, False

        for other_link in other_links:
            company_info = extract_company_info(driver, other_link)
            if company_info:
                try:
                    Actor.log.info(
                        f"Name: {company_info['companyName']}; "
                        f"Solution: {company_info['companySolution']}; "
                        f"Website: {company_info['companyWebsite']}; "
                        f"OtherLink: {company_info['otherLink']}"
                    )
                    await Actor.push_data(company_info)
                    
                    Names = True if company_info["companyName"] else Names
                    Solutions = True if company_info["companySolution"] else Solutions
                    Websites = True if company_info["companyWebsite"] else Websites
                    
                except Exception as e:
                    Actor.log.exception(f"Error pushing results: {e}")

        driver.quit()

        if not (Names and Solutions and Websites):
            e = Exception("The website is changed!")
            await Actor.fail(exit_code=ActorExitCodes.ERROR_USER_FUNCTION_THREW, exception=e)
