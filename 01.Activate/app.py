"""app.ipynb"""

# %pip install selenium bs4

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://activate-companies.softr.app/"

# Set up Selenium WebDriver
chromedriver_path = "./chromedriver-32.exe"
service = Service(chromedriver_path)

# Set the path to the Portable Chrome executable
chrome_exe_path = "./chrome-win32/chrome.exe"
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = chrome_exe_path
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--blink-settings=imagesEnabled=false')
driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get(url=URL)
time.sleep(10)

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

content_sections = driver.find_elements(By.CSS_SELECTOR, "div.content-section > div > div > div")

for one_section in content_sections:
    try:
        companyName = one_section.find_element(By.TAG_NAME, "h3").text.strip()
    except Exception as e:
        companyName = "N/A"
        print(f"Error retrieving company name: {e}")

    try:
        companyDescription = one_section.find_element(By.CSS_SELECTOR, "div.list-field-element > div > p").text.strip()
    except Exception as e:
        companyDescription = "N/A"
        print(f"Error retrieving company description: {e}")

    try:
        companyWebsite = one_section.find_element(By.CSS_SELECTOR, "div.list-field-element > div > div > p > a").get_attribute("href").strip()
    except Exception as e:
        companyWebsite = "N/A"
        print(f"Error retrieving company website: {e}")

    print(f"Name: {companyName}, Description: {companyDescription}, Website: {companyWebsite}")

driver.delete_all_cookies()
driver.quit()

