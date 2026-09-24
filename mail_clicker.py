#!/usr/bin/env python3
"""
mail_clicker.py
-------------------------------------------------------------------------------
Piccolo tool di automazione UI: apre la webmail, clicca il pulsante di refresh
(il cerchio / freccia circolare in alto) e poi apre la prima mail della lista
(quella piu' in alto = l'ultima arrivata).

Non fa login "magico": per stare dentro il tuo account usi un file di sessione
(cookie/storage state) che generi una volta con --login.

Uso:
    # 1) La prima volta, login a mano e salvataggio sessione:
    python3 mail_clicker.py --login --url "https://tua-webmail.example"

    # 2) Poi l'automazione (refresh + apri ultima mail):
    python3 mail_clicker.py --url "https://tua-webmail.example"

Opzioni (anche via variabili d'ambiente):
    --url URL             pagina della inbox                (env URL)
    --refresh SELETTORE   selettore del pulsante refresh    (env REFRESH_SELECTOR)
    --email SELETTORE     selettore della riga mail         (env EMAIL_SELECTOR)
    --storage FILE        file sessione                     (default ./mail_state.json)
    --login               apre il browser per il login e salva la sessione
    --headed              mostra la finestra del browser
    --wait MS             attesa dopo il refresh            (default 1500)
    --keep-open           lascia il browser aperto a fine run

Requisiti: pip install playwright
-------------------------------------------------------------------------------
"""

import argparse
import glob
import os
import sys
import time

from playwright.sync_api import sync_playwright


# Default: primo selettore che trova qualcosa vince. Sovrascrivibili da CLI/env.
DEFAULT_REFRESH = ", ".join(
    [
        'button[aria-label*="refresh" i]',
        'button[title*="refresh" i]',
        '[aria-label*="aggiorna" i]',
        '[title*="aggiorna" i]',
        '[data-testid*="refresh" i]',
        'button:has(svg[class*="refresh" i])',
        "button:has(.icon-refresh)",
    ]
)

# Default: prende la PRIMA riga della lista (la mail piu' recente sta in cima).
DEFAULT_EMAIL = ", ".join(
    [
        '[role="listbox"] [role="option"]',
        '[role="list"] [role="listitem"]',
        '[data-testid*="message" i]',
        '[class*="mail-item" i]',
        '[class*="email-item" i]',
        "ul li a",
        "li[tabindex]",
    ]
)


def find_chromium() -> str | None:
    """Individua il binario Chromium pre-installato (build variabili)."""
    if os.environ.get("PW_CHROMIUM"):
        return os.environ["PW_CHROMIUM"]
    patterns = [
        "/opt/pw-browsers/chromium-*/chrome-linux/chrome",
        "/opt/pw-browsers/chromium/chrome-linux/chrome",
    ]
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]  # build piu' alta
    return None  # lascia decidere a Playwright


def first_visible(page, selector_list: str, timeout_ms: int = 8000):
    """Ritorna il primo locator visibile tra i selettori (separati da virgola)."""
    parts = [s.strip() for s in selector_list.split(",") if s.strip()]
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        for sel in parts:
            loc = page.locator(sel).first
            try:
                if loc.count() and loc.is_visible():
                    return loc
            except Exception:
                pass
        page.wait_for_timeout(200)
    return None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Refresh inbox e apri l'ultima mail.")
    p.add_argument("--url", default=os.environ.get("URL", ""))
    p.add_argument("--refresh", default=os.environ.get("REFRESH_SELECTOR", DEFAULT_REFRESH))
    p.add_argument("--email", default=os.environ.get("EMAIL_SELECTOR", DEFAULT_EMAIL))
    p.add_argument("--storage", default=os.environ.get("STORAGE", "./mail_state.json"))
    p.add_argument("--wait", type=int, default=int(os.environ.get("WAIT", "1500")))
    p.add_argument("--login", action="store_true")
    p.add_argument("--headed", action="store_true")
    p.add_argument("--keep-open", dest="keep_open", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not args.url:
        print('[!] Manca l\'URL. Usa --url "https://tua-webmail" (o env URL).', file=sys.stderr)
        return 2

    headed = args.headed or args.login
    chromium_path = find_chromium()

    with sync_playwright() as pw:
        launch_kwargs = {"headless": not headed}
        if chromium_path:
            launch_kwargs["executable_path"] = chromium_path
        browser = pw.chromium.launch(**launch_kwargs)

        ctx_kwargs = {}
        if os.path.exists(args.storage):
            ctx_kwargs["storage_state"] = args.storage
        context = browser.new_context(**ctx_kwargs)
        page = context.new_page()

        print(f"[*] Apro {args.url}")
        page.goto(args.url, wait_until="domcontentloaded")

        # --- modalita' login: aspetta l'utente, poi salva la sessione ----------
        if args.login:
            print("[*] Fai il login nella finestra del browser.")
            input("    Quando sei dentro la inbox, premi INVIO qui per salvare la sessione...")
            context.storage_state(path=args.storage)
            print(f"[+] Sessione salvata in {args.storage}")
            browser.close()
            return 0

        # --- 1) click sul cerchio / refresh ------------------------------------
        refresh_btn = first_visible(page, args.refresh)
        if refresh_btn is None:
            print('[!] Pulsante refresh non trovato. Passa il selettore con --refresh "...".',
                  file=sys.stderr)
            if not args.keep_open:
                browser.close()
            return 1
        refresh_btn.click()
        print("[+] Refresh cliccato.")

        page.wait_for_timeout(args.wait)
        try:
            page.wait_for_load_state("networkidle")
        except Exception:
            pass

        # --- 2) click sulla prima mail (la piu' recente) -----------------------
        first_mail = first_visible(page, args.email)
        if first_mail is None:
            print('[!] Nessuna mail trovata. Passa il selettore con --email "...".',
                  file=sys.stderr)
            if not args.keep_open:
                browser.close()
            return 1

        try:
            subject = (first_mail.inner_text() or "").split("\n")[0]
        except Exception:
            subject = ""
        first_mail.click()
        print(f"[+] Aperta l'ultima mail: {subject or '(oggetto non leggibile)'}")

        if args.keep_open:
            print("[*] --keep-open attivo: chiudi il browser a mano quando hai finito.")
            input("    Premi INVIO per chiudere...")
        else:
            page.wait_for_timeout(500)
        browser.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
