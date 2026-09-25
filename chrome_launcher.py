import os
import shutil
import subprocess
import sys

RED = "\033[91m"
RESET = "\033[0m"

DEFAULT_URL = "https://mailum.com/"

WINDOWS_PATHS = [
    r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
    r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
    r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
]

MAC_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
]

LINUX_COMMANDS = [
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
]

def find_chrome():
    if os.name == "nt":
        for path in WINDOWS_PATHS:
            path = os.path.expandvars(path)
            if os.path.isfile(path):
                return path
        return shutil.which("chrome")
    if sys.platform == "darwin":
        for path in MAC_PATHS:
            if os.path.isfile(path):
                return path
        return None
    for command in LINUX_COMMANDS:
        path = shutil.which(command)
        if path:
            return path
    return None

def launch_chrome(url=DEFAULT_URL):
    chrome = find_chrome()
    if not chrome:
        print(RED + "\n[!] Chrome not found." + RESET)
        return False
    args = [chrome]
    if url:
        args.append(url)
    subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    print(RED + "\n[*] Chrome launched: " + RESET + chrome)
    return True

if __name__ == "__main__":
    launch_chrome(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL)
