from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException

browser = webdriver.Firefox(executable_path="geckodriver.exe")
browser.get("https://scholar.google.com.mx/citations?user=6Dn91MwAAAAJ&hl=en")

# Waiting till link is clickable
work = browser.find_element_by_link_text("Climate change 2014: mitigation of climate change")
work.click()
work2 = browser.find_element_by_link_text("Using logarithmic mean Divisia index to analyze changes in energy use and carbon dioxide emissions in Mexico's iron and steel industry")

while True:
    try:
        work2.click()
        break
    except ElementClickInterceptedException:
        continue

# close_button = browser.find_element_by_id('gs_md_cita-d-x')
# close_button.click()



