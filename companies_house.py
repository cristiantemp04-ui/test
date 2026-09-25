from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

RED = "\033[91m"
RESET = "\033[0m"

URL = "https://find-and-update.company-information.service.gov.uk/"
ADVANCED_SEARCH = (By.CSS_SELECTOR, "a[data-id='advanced-company-search']")
REJECT_COOKIES = (By.ID, "reject-cookies-button")
TIMEOUT = 20

def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # Keep Chrome open after the script ends
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, TIMEOUT)

    driver.get(URL)
    print(RED + "[*] Opened: " + RESET + URL)

    # The cookie banner can cover the page; close it if it shows up
    for button in driver.find_elements(*REJECT_COOKIES):
        if button.is_displayed():
            button.click()

    link = wait.until(EC.element_to_be_clickable(ADVANCED_SEARCH))
    tabs = len(driver.window_handles)
    link.click()

    # The link opens a new tab by itself (target="_blank"); open one if it didn't
    try:
        WebDriverWait(driver, 5).until(EC.number_of_windows_to_be(tabs + 1))
    except TimeoutException:
        driver.execute_script("window.open(arguments[0], '_blank');", link.get_attribute("href"))
        wait.until(EC.number_of_windows_to_be(tabs + 1))

    driver.switch_to.window(driver.window_handles[-1])
    wait.until(EC.url_contains("advanced-search"))
    print(RED + "[*] Advanced company search opened in a new tab: " + RESET + driver.current_url)

if __name__ == "__main__":
    main()
