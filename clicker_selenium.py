"""
Generic Selenium button clicker.

Apre una pagina web e clicca un bottone (o qualsiasi elemento) individuato
tramite un selettore. Utile per automatizzare/testare le tue pagine.

Uso:
    python clicker_selenium.py --url https://example.com --text "Verify"
    python clicker_selenium.py --url https://example.com --css "button.submit"
    python clicker_selenium.py --url https://example.com --xpath "//button[@id='ok']"
    python clicker_selenium.py --url https://example.com --text "Verify" --keep-open

Dipendenze:
    pip install selenium
    (Selenium 4.6+ scarica automaticamente il driver del browser)
"""

import argparse
import sys
import time

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
except ImportError:
    sys.exit("Manca selenium. Installa con: pip install selenium")


def build_locator(args):
    """Ritorna una tupla (By, valore) dal selettore scelto."""
    if args.css:
        return (By.CSS_SELECTOR, args.css)
    if args.xpath:
        return (By.XPATH, args.xpath)
    if args.id:
        return (By.ID, args.id)
    if args.text:
        # Bottone/elemento che contiene il testo indicato (case-sensitive).
        return (By.XPATH, f"//*[normalize-space(text())='{args.text}']")
    sys.exit("Specifica un selettore: --text, --css, --xpath o --id")


def click_element(driver, locator, timeout):
    """Aspetta che l'elemento sia cliccabile e ci clicca."""
    wait = WebDriverWait(driver, timeout)
    element = wait.until(EC.element_to_be_clickable(locator))
    element.click()
    return element


def make_driver(headless):
    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=opts)


def main():
    p = argparse.ArgumentParser(description="Clicca un elemento web con Selenium.")
    p.add_argument("--url", required=True, help="URL della pagina da aprire.")
    g = p.add_argument_group("selettore (scegline uno)")
    g.add_argument("--text", help="Elemento con questo testo esatto.")
    g.add_argument("--css", help="Selettore CSS, es. 'button.submit'.")
    g.add_argument("--xpath", help="Espressione XPath.")
    g.add_argument("--id", help="Attributo id dell'elemento.")
    p.add_argument("--timeout", type=float, default=15,
                   help="Secondi di attesa max per l'elemento. Default 15.")
    p.add_argument("--headless", action="store_true",
                   help="Esegui senza finestra del browser.")
    p.add_argument("--keep-open", action="store_true",
                   help="Lascia il browser aperto alla fine (per vedere il risultato).")
    args = p.parse_args()

    locator = build_locator(args)
    driver = make_driver(args.headless)
    try:
        driver.get(args.url)
        click_element(driver, locator, args.timeout)
        print(f"[+] Cliccato: {locator}")
        if args.keep_open:
            input("Premi Enter per chiudere il browser...")
        return 0
    except TimeoutException:
        print(f"[!] Elemento non trovato/cliccabile entro {args.timeout}s: {locator}")
        return 1
    finally:
        if not args.keep_open:
            driver.quit()


if __name__ == "__main__":
    sys.exit(main())
