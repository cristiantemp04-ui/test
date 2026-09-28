"""
Generic button clicker.

Cerca un bottone sullo schermo a partire da un'immagine di riferimento
(uno screenshot ritagliato del bottone) e ci clicca sopra.

Uso:
    python clicker.py button.png
    python clicker.py button.png --confidence 0.85 --wait 30
    python clicker.py button.png --double

Dipendenze:
    pip install pyautogui pillow opencv-python
    (opencv serve solo per il parametro --confidence)
"""

import argparse
import sys
import time

try:
    import pyautogui
except ImportError:
    sys.exit("Manca pyautogui. Installa con: pip install pyautogui pillow opencv-python")


def find_button(image_path, confidence=0.9):
    """Ritorna il centro (x, y) del bottone, o None se non lo trova."""
    try:
        return pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
    except pyautogui.ImageNotFoundException:
        return None
    except TypeError:
        # confidence richiede opencv; se manca, riprova senza
        try:
            return pyautogui.locateCenterOnScreen(image_path)
        except pyautogui.ImageNotFoundException:
            return None


def wait_and_click(image_path, confidence=0.9, timeout=0, double=False, poll=0.5):
    """
    Cerca il bottone e clicca. Se timeout > 0, riprova finché appare
    (utile per bottoni che compaiono dopo un caricamento).
    """
    deadline = time.time() + timeout
    while True:
        pos = find_button(image_path, confidence)
        if pos is not None:
            if double:
                pyautogui.doubleClick(pos)
            else:
                pyautogui.click(pos)
            print(f"[+] Cliccato su {pos}")
            return True

        if timeout <= 0 or time.time() >= deadline:
            print("[!] Bottone non trovato sullo schermo.")
            return False

        time.sleep(poll)


def main():
    p = argparse.ArgumentParser(description="Clicca un bottone individuato via immagine.")
    p.add_argument("image", help="PNG del bottone da cercare (screenshot ritagliato).")
    p.add_argument("--confidence", type=float, default=0.9,
                   help="Soglia di somiglianza 0-1 (richiede opencv-python). Default 0.9")
    p.add_argument("--wait", type=float, default=0,
                   help="Secondi di attesa max finché il bottone compare. Default 0 (subito).")
    p.add_argument("--double", action="store_true", help="Doppio click invece di singolo.")
    args = p.parse_args()

    ok = wait_and_click(args.image, args.confidence, args.wait, args.double)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
