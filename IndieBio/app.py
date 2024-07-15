"""
app.py
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, WebDriverException

BASE_URL_LIST = [
    # "https://indiebio.co/companies/?_categories=industrial",
    # "https://indiebio.co/companies/?_categories=climatetech",
    # "https://indiebio.co/companies/?_categories=materials",
    "https://indiebio.co/companies/?_categories=ag",
    "https://indiebio.co/companies/?_categories=food",
]

# Set up Selenium WebDriver
chromedriver_path = "./chromedriver-32.exe"
service = Service(chromedriver_path)

# Set the path to the Portable Chrome executable
chrome_exe_path = "./chrome-win32/chrome.exe"
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = chrome_exe_path
# chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--blink-settings=imagesEnabled=false')

driver = webdriver.Chrome(service=service, options=chrome_options)

result_urls = set()

for URL in BASE_URL_LIST:
    driver.get(URL)
    time.sleep(10)

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
            print("Element with the specified CSS selector not found")
        except WebDriverException as e:
            href = None
            print(f"WebDriverException occurred: {e}")

        result_urls.add(href)

result_urls = list(result_urls)

for page_url in result_urls:
    driver.get(page_url)
    time.sleep(3)

    try:
        companyName = driver.find_element(By.CLASS_NAME, "indiebio-company__title").text.strip()
    except NoSuchElementException:
        companyName = "N/A"
        print("Company name element not found")

    try:
        companySolution = driver.find_element(By.CLASS_NAME, "indiebio-company__tagline").text.strip()
    except NoSuchElementException:
        companySolution = "N/A"
        print("Company solution element not found")

    try:
        companyWebsite = driver.find_element(By.CSS_SELECTOR, "a.indiebio-company__website").get_attribute('href')
    except NoSuchElementException:
        companyWebsite = "#"
        print("Company website element not found")
    except WebDriverException as e:
        companyWebsite = "#"
        print(f"WebDriverException occurred: {e}")
    
    print(f"Name: {companyName}, Solution: {companySolution}, Website: {companyWebsite}, otherLink: {page_url}")
