import os
import sys

from chrome_launcher import launch_chrome

RED = "\033[91m"
RESET = "\033[0m"
DARK_RED = "\033[31m"

LOGO = r"""
   ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗███████╗██████╗
  ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗
  ██║     ███████║█████╗  ██║     █████╔╝ █████╗  ██████╔╝
  ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ ██╔══╝  ██╔══██╗
  ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗███████╗██║  ██║
   ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
"""

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def print_menu():
    clear()
    print(RED + LOGO + RESET)
    print(RED + "         Template Checker ~ 1.0.0 ~ Developed by Nakateru" + RESET)
    print()
    print(RED + "[1]" + RESET + " Start Checker")
    print(RED + "[2]" + RESET + " Scrape Proxies")
    print(RED + "[3]" + RESET + " Launch Chrome")
    print(RED + "[4]" + RESET + " Exit")
    print()

def start_checker():
    print(RED + "\n[*] Starting Checker..." + RESET)
    input("\nPress Enter to return to menu...")

def scrape_proxies():
    print(RED + "\n[*] Scraping Proxies..." + RESET)
    input("\nPress Enter to return to menu...")

def open_chrome():
    url = input("URL (leave empty for none): ").strip()
    launch_chrome(url or None)
    input("\nPress Enter to return to menu...")

def main():
    while True:
        print_menu()
        choice = input("Select option: ").strip()
        if choice == "1":
            start_checker()
        elif choice == "2":
            scrape_proxies()
        elif choice == "3":
            open_chrome()
        elif choice == "4":
            print(RED + "\n[*] Exiting..." + RESET)
            sys.exit(0)
        else:
            print(RED + "\n[!] Invalid option." + RESET)
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
