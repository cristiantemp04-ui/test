"""Security tests for the local signup site (site/app.py).

Restart the site before each run (the rate limit is kept in memory):
                        py site/app.py
Then run:               py tests/test_signup.py
"""
import random
import string
import sys
import urllib.error
import urllib.parse
import urllib.request

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "http://127.0.0.1:5000/"
PASSWORD = "Topolino01"
ALLOWED_HOSTS = {"127.0.0.1", "localhost"}

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

results = []

def random_username():
    return "".join(random.choices(string.ascii_lowercase, k=6))

def fill_and_submit(driver, username, password, repeat=None):
    driver.get(BASE_URL)
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "repeat").send_keys(password if repeat is None else repeat)
    driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
    # A fresh form has no message, so wait for the response page to show one
    WebDriverWait(driver, 10).until(EC.any_of(
        EC.presence_of_element_located((By.ID, "success")),
        EC.presence_of_element_located((By.ID, "error")),
    ))

def message(driver):
    for msg_id in ("success", "error"):
        found = driver.find_elements(By.ID, msg_id)
        if found:
            return msg_id, found[0].text
    return None, ""

def check(name, ok, detail=""):
    results.append(ok)
    label = GREEN + "PASS" if ok else RED + "FAIL"
    print(f"{label}{RESET} {name}" + (f"  ({detail})" if detail else ""))

def test_valid_signup(driver):
    username = random_username()
    fill_and_submit(driver, username, PASSWORD)
    kind, text = message(driver)
    check("valid signup is accepted", kind == "success", text)
    return username

def test_duplicate(driver, username):
    fill_and_submit(driver, username.upper(), PASSWORD)
    kind, text = message(driver)
    check("duplicate email is rejected (case-insensitive)", "already taken" in text, text)

def test_password_mismatch(driver):
    fill_and_submit(driver, random_username(), PASSWORD, repeat="Topolino02")
    kind, text = message(driver)
    check("mismatched passwords are rejected", "do not match" in text, text)

def test_weak_password(driver):
    fill_and_submit(driver, random_username(), "topolino")
    kind, text = message(driver)
    check("weak password is rejected", "at least 10 characters" in text, text)

def test_xss_username(driver):
    fill_and_submit(driver, "<script>alert(1)</script>", PASSWORD)
    kind, text = message(driver)
    injected = driver.find_elements(By.XPATH, "//script[contains(., 'alert(1)')]")
    check("script in username is rejected and not executed", "Email must be" in text and not injected, text)

def test_csrf():
    data = urllib.parse.urlencode({
        "username": random_username(), "domain": "mailum.com",
        "password": PASSWORD, "repeat": PASSWORD,
    }).encode()
    try:
        urllib.request.urlopen(BASE_URL, data=data)
        status = 200
    except urllib.error.HTTPError as e:
        status = e.code
    check("POST without CSRF token is refused", status == 400, f"HTTP {status}")

def test_rate_limit(driver):
    # Every earlier test counts as an attempt; keep going until the limit hits
    for i in range(15):
        fill_and_submit(driver, random_username(), "weak")
        kind, text = message(driver)
        if "Too many attempts" in text:
            check("rate limit blocks repeated attempts", True, f"blocked after {i + 1} more")
            return
    check("rate limit blocks repeated attempts", False, "never blocked")

def main():
    host = urllib.parse.urlparse(BASE_URL).hostname
    if host not in ALLOWED_HOSTS:
        sys.exit("These tests only run against your local site.")

    options = webdriver.ChromeOptions()
    if "--headless" in sys.argv:
        options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    try:
        username = test_valid_signup(driver)
        test_duplicate(driver, username)
        test_password_mismatch(driver)
        test_weak_password(driver)
        test_xss_username(driver)
        test_csrf()
        test_rate_limit(driver)
    finally:
        driver.quit()

    print(f"\n{sum(results)}/{len(results)} tests passed")
    sys.exit(0 if all(results) else 1)

if __name__ == "__main__":
    main()
