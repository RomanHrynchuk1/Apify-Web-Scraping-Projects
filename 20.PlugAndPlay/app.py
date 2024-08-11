import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


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
    # Set up Selenium WebDriver
    chromedriver_path = "./chromedriver-32.exe"
    service = Service(chromedriver_path)

    # Set the path to the Portable Chrome executable
    chrome_exe_path = "./chrome-win32/chrome.exe"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = chrome_exe_path
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument("--blink-settings=imagesEnabled=false")

    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

def click_element(driver, element):
    """Attempt to click an element, scrolling into view if necessary."""
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.3)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(element)).click()
    except TimeoutException:
        print("Element was not clickable in time, trying a direct click.")
        try:
            element.click()
        except Exception as e:
            print("An error occurred while clicking the element.")

def handle_cookies(driver):
    """Handle cookie acceptance."""
    try:
        driver.find_element(By.CSS_SELECTOR, "button#onetrust-accept-btn-handler").click()
        print("Accept All Cookies button is clicked.")
        time.sleep(1)
    except Exception as e:
        print("An error occurred while attempting to click on 'Accept cookies' button.")

def navigate_to_url(driver, url):
    """Navigate to the given URL and handle any exceptions."""
    try:
        driver.get(url)
        time.sleep(3)
    except Exception as e:
        print(f"An error occurred while navigating to {url}: {e}")
        return False
    return True

def extract_industry_links(driver):
    """Extract all industry-related links from the page."""
    other_links = []
    
    for industry, index in industries:
        try:
            industries_dropdown = driver.find_element(By.CSS_SELECTOR, "select#cbxIndustries")
            click_element(driver, industries_dropdown)
            time.sleep(2)
            options = industries_dropdown.find_elements(By.TAG_NAME, "option")
            option = options[index]  # Dynamically select option based on index
            click_element(driver, option)
            time.sleep(2)
            click_element(driver, industries_dropdown)
            time.sleep(0.3)
        except Exception as e:
            print(f"An error occurred while selecting industry ({industry}) : {e}")
            continue
        
        while True:
            try:
                other_link_elements = driver.find_elements(By.CSS_SELECTOR, "pnp-startup-card a")
                for element in other_link_elements:
                    other_links.append(element.get_attribute('href'))
                
                next_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Next ->')]")
                next_button.click()
                print("Next button (page navigation) button is clicked.")
                time.sleep(2)
            except Exception as e:
                print("An error occurred while navigating pages or extracting links. Maybe, it's the end of navigation")
                break
            
    return other_links

def extract_company_info(driver, url):
    """Extract company information from the given URL."""
    try:
        driver.get(url)
        time.sleep(0.3)
    except Exception as e:
        print(f"An error occurred while opening: {url}")
        return None

    try:
        company_name = driver.find_element(By.CSS_SELECTOR, "h1.pnp-text-primary").text.strip()
    except Exception as e:
        print(f"An error occurred while extracting company name: {e}")
        company_name = ""

    try:
        company_solution = driver.find_element(By.CSS_SELECTOR, "div.items-start p.pnp-text-primary").text.strip()
    except Exception as e:
        print(f"An error occurred while extracting company solution: {e}")
        company_solution = ""

    try:
        company_website = driver.find_element(By.CSS_SELECTOR, "a.nav-link.pnp-link").get_attribute('href')
    except Exception as e:
        print(f"An error occurred while extracting company website: {e}")
        company_website = ""

    return {
        "companyName": company_name,
        "companySolution": company_solution,
        "companyWebsite": company_website,
        "otherLink": url,
    }

if __name__ == "__main__":
    start_urls = BASE_URL_LIST
    print(f"Start URLs: {str(start_urls)}")

    print("Launching Chrome WebDriver...")
    driver = initialize_webdriver()

    start_url = start_urls[0]["url"]

    if not navigate_to_url(driver, start_url):
        print("Error navigating to the start url.")
        exit()
    
    time.sleep(3)

    handle_cookies(driver)

    other_links = extract_industry_links(driver)

    for other_link in other_links:
        company_info = extract_company_info(driver, other_link)
        if company_info:
            try:
                print(
                    f"Name: {company_info['companyName']}; "
                    f"Solution: {company_info['companySolution']}; "
                    f"Website: {company_info['companyWebsite']}; "
                    f"OtherLink: {company_info['otherLink']}"
                )
            except Exception as e:
                print(f"Error pushing results: {e}")
    
    driver.delete_all_cookies()
    driver.quit()

