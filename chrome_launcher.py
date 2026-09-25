import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

RED = "\033[91m"
RESET = "\033[0m"

DEFAULT_URL = "https://mailum.com/"
SIGN_UP_XPATH = "//a[normalize-space()='Sign Up']"
TIMEOUT = 20

def launch_chrome(url=DEFAULT_URL):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # Keep Chrome open after the script ends
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    print(RED + "\n[*] Opened: " + RESET + url)
    return driver

def click_sign_up(driver):
    button = WebDriverWait(driver, TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, SIGN_UP_XPATH))
    )
    button.click()
    print(RED + "[*] Clicked Sign Up" + RESET)

if __name__ == "__main__":
    driver = launch_chrome(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL)
    try:
        click_sign_up(driver)
    except Exception as e:
        print(RED + "[!] Sign Up button not found: " + RESET + str(e))
