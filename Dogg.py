#!/usr/bin/env python3
# encoding=utf-8
# 執行方式：python chrome_tixcraft.py 或 python3 chrome_tixcraft.py
# import jieba
# from DrissionPage import ChromiumPage
import re
import argparse
import requests
import pyautogui
import base64
import json
import logging
import os
import platform
import random
import ssl
import subprocess
import sys
import threading
import time
import warnings
import webbrowser
from datetime import datetime
from bs4 import BeautifulSoup

import chromedriver_autoinstaller_max
from selenium import webdriver
from selenium.common.exceptions import (NoAlertPresentException,
                                        NoSuchWindowException,
                                        UnexpectedAlertPresentException,
                                        WebDriverException)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from urllib3.exceptions import InsecureRequestWarning

import util
from NonBrowser import NonBrowser

try:
    import ddddocr
    import Dog_ocr
except Exception as exc:
    print(exc)
    pass

CONST_APP_VERSION = "MaxBot (2025.06.11)"

CONST_MAXBOT_ANSWER_ONLINE_FILE = "MAXBOT_ONLINE_ANSWER.txt"
CONST_MAXBOT_CONFIG_FILE = "settings.json"
CONST_MAXBOT_EXTENSION_STATUS_JSON = "status.json"
CONST_MAXBOT_EXTENSION_NAME = "Maxbotplus_1.0.0"
CONST_MAXBOT_INT28_FILE = "MAXBOT_INT28_IDLE.txt"
CONST_MAXBOT_LAST_URL_FILE = "MAXBOT_LAST_URL.txt"
CONST_MAXBOT_QUESTION_FILE = "MAXBOT_QUESTION.txt"
CONST_MAXBLOCK_EXTENSION_NAME = "Maxblockplus_1.0.0"
CONST_MAXBLOCK_EXTENSION_FILTER = [
    "*.doubleclick.net/*",
    "*.ssp.hinet.net/*",
    "*a.amnet.tw/*",
    "*anymind360.com/*",
    "*adx.c.appier.net/*",
    "*cdn.cookielaw.org/*",
    "*clarity.ms/*",
    "*cloudfront.com/*",
    "*cms.analytics.yahoo.com/*",
    "*e2elog.fetnet.net/*",
    "*fundingchoicesmessages.google.com/*",
    "*ghtinc.com/*",
    "*google-analytics.com/*",
    "*googletagmanager.com/*",
    "*googletagservices.com/*",
    "*img.uniicreative.com/*",
    "*lndata.com/*",
    "*match.adsrvr.org/*",
    "*onead.onevision.com.tw/*",
    "*play.google.com/log?*",
    "*popin.cc/*",
    "*rollbar.com/*",
    "*sb.scorecardresearch.com/*",
    "*tagtoo.co/*",
    "*ticketmaster.sg/js/adblock*",
    "*ticketmaster.sg/js/ads.*",
    "*tixcraft.com/js/analytics.js*",
    "*tixcraft.com/js/common.js*",
    "*tixcraft.com/js/custom.js*",
    "*treasuredata.com/*",
    "*www.youtube.com/youtubei/v1/player/heartbeat*",
]

CONST_CHROME_VERSION_NOT_MATCH_EN = "Please download the WebDriver version to match your browser version."
CONST_CHROME_VERSION_NOT_MATCH_TW = "請下載與您瀏覽器相同版本的WebDriver版本，或更新您的瀏覽器版本。"
CONST_CHROME_DRIVER_WEBSITE = 'https://chromedriver.chromium.org/'

CONST_CITYLINE_SIGN_IN_URL = "https://www.cityline.com/Login.html?targetUrl=https%3A%2F%2Fwww.cityline.com%2FEvents.html"
CONST_FAMI_SIGN_IN_URL = "https://www.famiticket.com.tw/Home/User/SignIn"
CONST_HKTICKETING_SIGN_IN_URL = "https://premier.hkticketing.com/Secure/ShowLogin.aspx"
CONST_KHAM_SIGN_IN_URL = "https://kham.com.tw/application/UTK13/UTK1306_.aspx"
CONST_KKTIX_SIGN_IN_URL = "https://kktix.com/users/sign_in?back_to=%s"
CONST_TICKET_SIGN_IN_URL = "https://ticket.com.tw/application/utk13/utk1306_.aspx"
CONST_URBTIX_SIGN_IN_URL = "https://www.urbtix.hk/member-login"

CONST_FROM_TOP_TO_BOTTOM = "from top to bottom"
CONST_FROM_BOTTOM_TO_TOP = "from bottom to top"
CONST_CENTER = "center"
CONST_RANDOM = "random"

CONT_STRING_1_SEATS_REMAINING = ['@1 seat(s) remaining', '剩餘 1@', '@1 席残り']

CONST_OCR_CAPTCH_IMAGE_SOURCE_NON_BROWSER = "NonBrowser"
CONST_OCR_CAPTCH_IMAGE_SOURCE_CANVAS = "canvas"

CONST_WEBDRIVER_TYPE_SELENIUM = "selenium"
CONST_WEBDRIVER_TYPE_UC = "undetected_chromedriver"
CONST_WEBDRIVER_TYPE_DP = "DrissionPage"
CONST_WEBDRIVER_TYPE_NODRIVER = "nodriver"
CONST_CHROME_FAMILY = ["chrome", "edge", "brave"]
CONST_PREFS_DICT = {
    "credentials_enable_service": False,
    "in_product_help.snoozed_feature.IPH_LiveCaption.is_dismissed": True,
    "in_product_help.snoozed_feature.IPH_LiveCaption.last_dismissed_by": 4,
    "media_router.show_cast_sessions_started_by_other_devices.enabled": False,
    "net.network_prediction_options": 3,
    "privacy_guide.viewed": True,
    "profile.default_content_setting_values.notifications": 2,
    "profile.default_content_setting_values.sound": 2,
    "profile.name": CONST_APP_VERSION,
    "profile.password_manager_enabled": False,
    "safebrowsing.enabled": False,
    "safebrowsing.enhanced": False,
    "sync.autofill_wallet_import_enabled_migrated": False,
    "translate": {"enabled": False}}

warnings.simplefilter('ignore', InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
logging.basicConfig()
logger = logging.getLogger('logger')


def send_telegram_message(message, config_dict):
    """
    發送 Telegram 通知 (優化版)
    """
    # 1. [基礎防呆] 檢查設定檔是否存在
    if not config_dict or "advanced" not in config_dict:
        return

    # 2. [開關檢查] 檢查是否啟用，沒啟用直接結束 (預設為 False)
    # 這裡對應 GUI 的勾選框
    if not config_dict["advanced"].get("telegram_enable", False):
        # print("Telegram 通知未啟用") # 註解掉以保持 Log 乾淨
        return

    # 3. [讀取資料] 從設定檔讀取 Token 與 ID
    bot_token = config_dict["advanced"].get("telegram_bot_token", "")
    chat_id = config_dict["advanced"].get("telegram_chat_id", "")

    # 4. [資料檢查] 檢查是否設定完整 (避免空字串報錯)
    if not bot_token or not chat_id:
        # print("⚠️ Telegram 設定不完整 (GUI未填寫)，跳過通知")
        return

    # 5. [發送請求]
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        # 設定 timeout=3 秒，避免網路卡頓影響搶票主流程
        response = requests.post(url, data=payload, timeout=6)

        if response.status_code == 200:
            print("✅ Telegram 通知發送成功！")
        else:
            print(
                f"❌ Telegram 發送失敗 (代碼 {response.status_code}): {response.text}")

    except Exception as e:
        # 這裡只印出錯誤，不拋出例外，確保不會因為發訊息失敗而中斷搶票
        print(f"❌ Telegram 連線錯誤: {e}")


def sleep_with_random_interval(config_dict):
    """
    根據設定檔執行隨機等待
    邏輯：基礎秒數 +/- 隨機範圍
    例如：基礎 6 秒, 範圍 2 秒 => 隨機在 4.0 ~ 8.0 秒之間
    """
    base_interval = 0.0
    if config_dict and "advanced" in config_dict:
        base_interval = float(config_dict["advanced"].get(
            "auto_reload_page_interval", 0.0))

    # 如果基礎秒數是 0，就不需要等待 (也不用隨機)
    if base_interval <= 0:
        return

    # 讀取是否啟用隨機模式
    random_mode = False
    if config_dict and "advanced" in config_dict:
        random_mode = config_dict["advanced"].get(
            "auto_reload_random_mode", False)

    if random_mode:
        try:
            # 讀取隨機範圍 (例如使用者輸入 2)
            random_range_val = float(config_dict["advanced"].get(
                "auto_reload_random_range", 0.0))

            if random_range_val > 0:
                # 計算上下限 (確保不小於 0)
                min_sec = max(0.1, base_interval - random_range_val)
                max_sec = base_interval + random_range_val

                # 產生隨機秒數
                sleep_time = random.uniform(min_sec, max_sec)

                print(
                    f"🎲 隨機刷新: 基礎 {base_interval}s ± {random_range_val}s -> 本次等待 {sleep_time:.2f}s")
                time.sleep(sleep_time)
                return  # 執行完畢，直接返回
        except Exception as e:
            print(f"隨機參數讀取錯誤，使用固定間隔: {e}")
            pass

    # 如果沒啟用隨機，或是參數有問題，就執行原本的固定等待
    time.sleep(base_interval)


def get_config_dict(args):
    app_root = util.get_app_root()

    # 1. 預設是 settings.json
    target_config_name = CONST_MAXBOT_CONFIG_FILE

    # ================= [新增] 讀取 GUI 留下的橋樑檔案 =================
    pointer_filepath = os.path.join(app_root, "MAXBOT_CURRENT_PROFILE.txt")
    if os.path.exists(pointer_filepath):
        try:
            with open(pointer_filepath, "r", encoding="utf-8") as f:
                saved_name = f.read().strip()
                if saved_name and saved_name.endswith(".json"):
                    target_config_name = saved_name
        except Exception:
            pass
    # =================================================================

    config_filepath = os.path.join(app_root, target_config_name)

    # 如果命令列依然有傳入 --input，則擁有最高優先權 (相容舊有設計)
    if args.input:
        config_filepath = args.input

    config_dict = None
    if os.path.isfile(config_filepath):
        with open(config_filepath, 'r', encoding='utf-8') as json_data:
            config_dict = json.load(json_data)

            # ================= [新增] 記住當前路徑，給首頁熱重載使用 =================
            config_dict["_internal_config_path"] = config_filepath
            # =========================================================================

            if args.headless is not None:
                config_dict["advanced"]["headless"] = util.t_or_f(
                    args.headless)

            if args.homepage:
                config_dict["homepage"] = args.homepage

            if args.ticket_number:
                config_dict["ticket_number"] = args.ticket_number

            if args.browser:
                config_dict["browser"] = args.browser

            if args.tixcraft_sid:
                config_dict["advanced"]["tixcraft_sid"] = args.tixcraft_sid

            if args.ibonqware:
                config_dict["advanced"]["ibonqware"] = args.ibonqware

            if args.kktix_account:
                config_dict["advanced"]["kktix_account"] = args.kktix_account
            if args.kktix_password:
                config_dict["advanced"]["kktix_password_plaintext"] = args.kktix_password

            if args.proxy_server:
                config_dict["advanced"]["proxy_server_port"] = args.proxy_server

            if args.window_size:
                config_dict["advanced"]["window_size"] = args.window_size

            # special case for headless to enable away from keyboard mode.
            is_headless_enable_ocr = False
            if config_dict["advanced"]["headless"]:
                # for tixcraft headless.
                # print("If you are runnig headless mode on tixcraft, you need input your cookie SID.")
                if len(config_dict["advanced"]["tixcraft_sid"]) > 1:
                    is_headless_enable_ocr = True

            if is_headless_enable_ocr:
                config_dict["ocr_captcha"]["enable"] = True
                config_dict["ocr_captcha"]["force_submit"] = True

    return config_dict


def reload_critical_settings(config_dict):
    """
    動態重新讀取 settings.json (或指定的設定檔) 中的關鍵設定 
    """
    # ================= [新增] 檢查是否停用熱重載 =================
    # 取得使用者是否勾選了「取消自動更新設定檔設定」 (預設為 False)
    disable_auto_update = config_dict.get("advanced", {}).get(
        "disable_auto_update_config", False)

    if disable_auto_update:
        # 如果勾選了取消自動更新，直接提早結束函式，不做後續的硬碟讀取
        return
    # ==============================================================

    try:
        app_root = util.get_app_root()

        # 動態抓取要熱重載的設定檔
        target_config_name = "settings.json"  # 預設值
        pointer_filepath = os.path.join(app_root, "MAXBOT_CURRENT_PROFILE.txt")

        # 讀取 GUI 儲存的橋樑檔案，確認目前該用哪一個設定檔
        if os.path.exists(pointer_filepath):
            try:
                with open(pointer_filepath, "r", encoding="utf-8") as f:
                    saved_name = f.read().strip()
                    if saved_name and saved_name.endswith(".json"):
                        target_config_name = saved_name
            except Exception:
                pass

        config_filepath = os.path.join(app_root, target_config_name)

        if os.path.isfile(config_filepath):
            with open(config_filepath, 'r', encoding='utf-8') as json_data:
                new_config = json.load(json_data)

                # 1. 更新張數
                if "ticket_number" in new_config:
                    config_dict["ticket_number"] = new_config["ticket_number"]

                # 2. 更新日期選擇策略與關鍵字
                if "date_auto_select" in new_config:
                    config_dict["date_auto_select"] = new_config["date_auto_select"]

                # 3. 更新區域選擇策略與關鍵字
                if "area_auto_select" in new_config:
                    config_dict["area_auto_select"] = new_config["area_auto_select"]

                # 4. 更新 "進階設定 (Advanced)" 內的項目
                if "advanced" in new_config:
                    # 4-1. 更新自動刷新間隔 (秒數)
                    if "auto_reload_page_interval" in new_config["advanced"]:
                        config_dict["advanced"]["auto_reload_page_interval"] = new_config["advanced"]["auto_reload_page_interval"]

                    # 4-1-b. 更新隨機模式與範圍
                    if "auto_reload_random_mode" in new_config["advanced"]:
                        config_dict["advanced"]["auto_reload_random_mode"] = new_config["advanced"]["auto_reload_random_mode"]

                    if "auto_reload_random_range" in new_config["advanced"]:
                        config_dict["advanced"]["auto_reload_random_range"] = new_config["advanced"]["auto_reload_random_range"]

                    # 4-2. 更新使用者自定義字典 (驗證碼答案/關鍵字)
                    # if "user_guess_string" in new_config["advanced"]:
                    #    config_dict["advanced"]["user_guess_string"] = new_config["advanced"]["user_guess_string"]

    except Exception as e:
        pass


def write_question_to_file(question_text):
    working_dir = os.path.dirname(os.path.realpath(__file__))
    target_path = os.path.join(working_dir, CONST_MAXBOT_QUESTION_FILE)
    util.write_string_to_file(target_path, question_text)


def write_last_url_to_file(url):
    working_dir = os.path.dirname(os.path.realpath(__file__))
    target_path = os.path.join(working_dir, CONST_MAXBOT_LAST_URL_FILE)
    util.write_string_to_file(target_path, url)


def read_last_url_from_file():
    ret = ""
    with open(CONST_MAXBOT_LAST_URL_FILE, "r") as text_file:
        ret = text_file.readline()
    return ret


def get_favoriate_extension_path(webdriver_path, config_dict):
    # print("webdriver_path:", webdriver_path)
    extension_list = []
    extension_list.append(os.path.join(
        webdriver_path, CONST_MAXBOT_EXTENSION_NAME + ".crx"))
    extension_list.append(os.path.join(
        webdriver_path, CONST_MAXBLOCK_EXTENSION_NAME + ".crx"))
    return extension_list


def sync_status_to_extension(status):
    # sync generated ext status.
    Root_Dir = util.get_app_root()
    webdriver_folder = os.path.join(Root_Dir, "webdriver")
    target_folder_list = os.listdir(webdriver_folder)
    for item in target_folder_list:
        if item.startswith("tmp_" + CONST_MAXBOT_EXTENSION_NAME):
            target_path = os.path.join(webdriver_folder, item)
            target_path = os.path.join(target_path, "data")
            if os.path.exists(target_path):
                target_path = os.path.join(
                    target_path, CONST_MAXBOT_EXTENSION_STATUS_JSON)
                # print("save as to:", target_path)
                status_json = {}
                status_json["status"] = status
                # print("dump json to path:", target_path)
                try:
                    with open(target_path, 'w') as outfile:
                        json.dump(status_json, outfile)
                except Exception as e:
                    pass


def get_chromedriver_path(webdriver_path):
    chromedriver_path = os.path.join(webdriver_path, "chromedriver")
    if platform.system().lower() == "windows":
        chromedriver_path = os.path.join(webdriver_path, "chromedriver.exe")
    return chromedriver_path


def get_chrome_options(webdriver_path, config_dict):
    chrome_options = webdriver.ChromeOptions()
    if config_dict["browser"] == "edge":
        chrome_options = webdriver.EdgeOptions()
    if config_dict["browser"] == "safari":
        chrome_options = webdriver.SafariOptions()

    is_log_performace = False
    performace_site = ['ticketplus']
    for site in performace_site:
        if site in config_dict["homepage"]:
            is_log_performace = True
            break

    if is_log_performace:
        if config_dict["browser"] in CONST_CHROME_FAMILY:
            chrome_options.set_capability(
                "goog:loggingPrefs", {"performance": "ALL"})

    # PS: this is crx version.
    extension_list = []
    if config_dict["advanced"]["chrome_extension"]:
        extension_list = get_favoriate_extension_path(
            webdriver_path, config_dict)
    for ext in extension_list:
        if os.path.exists(ext):
            chrome_options.add_extension(ext)

    if config_dict["advanced"]["headless"]:
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--headless=new')

    chrome_options.add_argument("--disable-animations")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-bookmark-reordering")
    chrome_options.add_argument("--disable-boot-animation")
    chrome_options.add_argument("--disable-breakpad")
    chrome_options.add_argument("--disable-canvas-aa")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-cloud-import")
    chrome_options.add_argument("--disable-component-cloud-policy")
    chrome_options.add_argument("--disable-component-update")
    chrome_options.add_argument("--disable-composited-antialiasing")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-device-discovery-notifications")
    chrome_options.add_argument("--disable-dinosaur-easter-egg")
    chrome_options.add_argument("--disable-domain-reliability")
    chrome_options.add_argument(
        "--disable-features=IsolateOrigins,site-per-process,TranslateUI,PrivacySandboxSettings4")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-login-animations")
    chrome_options.add_argument("--disable-login-screen-apps")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-print-preview")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-session-crashed-bubble")
    chrome_options.add_argument("--disable-smooth-scrolling")
    chrome_options.add_argument("--disable-suggestions-ui")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--hide-crash-restore-bubble")
    chrome_options.add_argument("--lang=zh-TW")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-pings")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--no-service-autorun")
    chrome_options.add_argument("--password-store=basic")

    # for navigator.webdriver
    chrome_options.add_experimental_option(
        "excludeSwitches", ['enable-automation'])
    # Deprecated chrome option is ignored: useAutomationExtension
    # chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("prefs", CONST_PREFS_DICT)

    if len(config_dict["advanced"]["proxy_server_port"]) > 2:
        chrome_options.add_argument(
            '--proxy-server=%s' % config_dict["advanced"]["proxy_server_port"])

    if config_dict["browser"] == "brave":
        brave_path = util.get_brave_bin_path()
        if os.path.exists(brave_path):
            chrome_options.binary_location = brave_path

    chrome_options.page_load_strategy = 'eager'
    # chrome_options.page_load_strategy = 'none'

    # 彈窗設定關閉 accept=開啟
    chrome_options.unhandled_prompt_behavior = "ignore"

    return chrome_options


def load_chromdriver_normal(config_dict, driver_type):
    show_debug_message = config_dict["advanced"]["verbose"]

    driver = None

    Root_Dir = util.get_app_root()
    webdriver_path = os.path.join(Root_Dir, "webdriver")
    chromedriver_path = get_chromedriver_path(webdriver_path)

    os.makedirs(webdriver_path, exist_ok=True)

    if not os.path.exists(chromedriver_path):
        print("WebDriver not exist, try to download to:", webdriver_path)
        chromedriver_autoinstaller_max.install(
            path=webdriver_path, make_version_dir=False)

    if not os.path.exists(chromedriver_path):
        print("Please download chromedriver and extract zip to webdriver folder from this url:")
        print("請下在面的網址下載與你chrome瀏覽器相同版本的chromedriver,解壓縮後放到webdriver目錄裡：")
        print(CONST_CHROME_DRIVER_WEBSITE)
    else:
        chrome_service = Service(chromedriver_path)
        chrome_options = get_chrome_options(webdriver_path, config_dict)
        try:
            driver = webdriver.Chrome(
                service=chrome_service, options=chrome_options)
        except WebDriverException as exc:
            error_message = str(exc)
            if show_debug_message:
                print(exc)
            left_part = error_message.split("Stacktrace:")[
                0] if "Stacktrace:" in error_message else None
            if "This version of ChromeDriver only supports Chrome version" in error_message:
                print(CONST_CHROME_VERSION_NOT_MATCH_EN)
                print(CONST_CHROME_VERSION_NOT_MATCH_TW)

                # remove exist chromedriver, download again.
                try:
                    print("Deleting exist and download ChromeDriver again.")
                    os.unlink(chromedriver_path)
                except Exception as exc2:
                    print(exc2)
                    pass

                chromedriver_autoinstaller_max.install(
                    path=webdriver_path, make_version_dir=False)
                chrome_service = Service(chromedriver_path)
                try:
                    chrome_options = get_chrome_options(
                        webdriver_path, config_dict)
                    driver = webdriver.Chrome(
                        service=chrome_service, options=chrome_options)
                except WebDriverException as exc2:
                    print("Selenium 4.11.0 Release with Chrome For Testing Browser.")
                    try:
                        chrome_options = get_chrome_options(
                            webdriver_path, config_dict)
                        driver = webdriver.Chrome(
                            service=Service(), options=chrome_options)
                    except WebDriverException as exc3:
                        print(exc3)
                        pass
    return driver


def get_uc_options(uc, config_dict, webdriver_path):
    options = uc.ChromeOptions()
    options.page_load_strategy = 'eager'
    # options.page_load_strategy = 'none'

    # 彈窗設定關閉 accept=開啟  ignore=關閉
    options.unhandled_prompt_behavior = "ignore"
    # print("strategy", options.page_load_strategy)

    is_log_performace = False
    performace_site = ['ticketplus']
    for site in performace_site:
        if site in config_dict["homepage"]:
            is_log_performace = True
            break

    if is_log_performace:
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    load_extension_path = ""
    extension_list = []
    if config_dict["advanced"]["chrome_extension"]:
        extension_list = get_favoriate_extension_path(
            webdriver_path, config_dict)
    for ext in extension_list:
        if ext.endswith(".crx"):
            ext = ext.replace('.crx', '')
        if os.path.exists(ext):
            # sync config.
            if CONST_MAXBOT_EXTENSION_NAME in ext:
                clone_ext = ext.replace(CONST_MAXBOT_EXTENSION_NAME, "tmp_" +
                                        CONST_MAXBOT_EXTENSION_NAME + "_" + config_dict["token"])
                if not os.path.exists(clone_ext):
                    os.mkdir(clone_ext)
                util.copytree(ext, clone_ext)
                ext = clone_ext
                util.dump_settings_to_maxbot_plus_extension(
                    ext, config_dict, CONST_MAXBOT_CONFIG_FILE)
            if CONST_MAXBLOCK_EXTENSION_NAME in ext:
                clone_ext = ext.replace(CONST_MAXBLOCK_EXTENSION_NAME, "tmp_" +
                                        CONST_MAXBLOCK_EXTENSION_NAME + "_" + config_dict["token"])
                if not os.path.exists(clone_ext):
                    os.mkdir(clone_ext)
                util.copytree(ext, clone_ext)
                ext = clone_ext
                util.dump_settings_to_maxblock_plus_extension(
                    ext, config_dict, CONST_MAXBOT_CONFIG_FILE, CONST_MAXBLOCK_EXTENSION_FILTER)
            load_extension_path += ("," + os.path.abspath(ext))
            # print("load_extension_path:", load_extension_path)

    if len(load_extension_path) > 0:
        # print('load-extension:', load_extension_path[1:])
        options.add_argument('--load-extension=' + load_extension_path[1:])

    if config_dict["advanced"]["headless"]:
        # options.add_argument('--headless')
        options.add_argument('--headless=new')

    options.add_argument("--disable-animations")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-bookmark-reordering")
    options.add_argument("--disable-boot-animation")
    options.add_argument("--disable-breakpad")
    options.add_argument("--disable-canvas-aa")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-cloud-import")
    options.add_argument("--disable-component-cloud-policy")
    options.add_argument("--disable-component-update")
    options.add_argument("--disable-composited-antialiasing")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-device-discovery-notifications")
    options.add_argument("--disable-dinosaur-easter-egg")
    options.add_argument("--disable-domain-reliability")
    options.add_argument(
        "--disable-features=IsolateOrigins,site-per-process,TranslateUI,PrivacySandboxSettings4")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-login-animations")
    options.add_argument("--disable-login-screen-apps")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-print-preview")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-session-crashed-bubble")
    options.add_argument("--disable-smooth-scrolling")
    options.add_argument("--disable-suggestions-ui")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--hide-crash-restore-bubble")
    options.add_argument("--lang=zh-TW")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--no-first-run")
    options.add_argument("--no-pings")
    options.add_argument("--no-sandbox")
    options.add_argument("--no-service-autorun")
    options.add_argument("--password-store=basic")
    options.add_experimental_option("prefs", CONST_PREFS_DICT)

    if len(config_dict["advanced"]["proxy_server_port"]) > 2:
        options.add_argument('--proxy-server=%s' %
                             config_dict["advanced"]["proxy_server_port"])

    if config_dict["browser"] == "brave":
        brave_path = util.get_brave_bin_path()
        if os.path.exists(brave_path):
            options.binary_location = brave_path

    return options


def load_chromdriver_uc(config_dict):
    import undetected_chromedriver as uc

    show_debug_message = True       # debug.
    show_debug_message = False      # online

    if config_dict["advanced"]["verbose"]:
        show_debug_message = True

    Root_Dir = util.get_app_root()
    webdriver_path = os.path.join(Root_Dir, "webdriver")
    chromedriver_path = get_chromedriver_path(webdriver_path)

    if not os.path.exists(webdriver_path):
        os.mkdir(webdriver_path)

    if not os.path.exists(chromedriver_path):
        print("ChromeDriver not exist, try to download to:", webdriver_path)
        try:
            chromedriver_autoinstaller_max.install(
                path=webdriver_path, make_version_dir=False)
            if not os.path.exists(chromedriver_path):
                print(
                    "check installed chrome version fail, download last known good version.")
                chromedriver_autoinstaller_max.install(
                    path=webdriver_path, make_version_dir=False, detect_installed_version=False)
        except Exception as exc:
            print(exc)
    else:
        print("ChromeDriver exist:", chromedriver_path)

    driver = None
    if os.path.exists(chromedriver_path):
        # use chromedriver_autodownload instead of uc auto download.
        is_cache_exist = util.clean_uc_exe_cache()

        fail_1 = False
        lanch_uc_with_path = True
        if "macos" in platform.platform().lower():
            if "arm64" in platform.platform().lower():
                lanch_uc_with_path = False

        if lanch_uc_with_path:
            try:
                options = get_uc_options(uc, config_dict, webdriver_path)
                driver = uc.Chrome(driver_executable_path=chromedriver_path,
                                   options=options, headless=config_dict["advanced"]["headless"])
            except Exception as exc:
                print(exc)
                error_message = str(exc)
                left_part = None
                if "Stacktrace:" in error_message:
                    left_part = error_message.split("Stacktrace:")[0]
                    print(left_part)

                if "This version of ChromeDriver only supports Chrome version" in error_message:
                    print(CONST_CHROME_VERSION_NOT_MATCH_EN)
                    print(CONST_CHROME_VERSION_NOT_MATCH_TW)
                fail_1 = True
        else:
            fail_1 = True

        fail_2 = False
        if fail_1:
            try:
                options = get_uc_options(uc, config_dict, webdriver_path)
                driver = uc.Chrome(options=options)
            except Exception as exc:
                print(exc)
                fail_2 = True

        if fail_2:
            # remove exist chromedriver, download again.
            try:
                print("Deleting exist and download ChromeDriver again.")
                os.unlink(chromedriver_path)
            except Exception as exc2:
                print(exc2)
                pass

            try:
                chromedriver_autoinstaller_max.install(
                    path=webdriver_path, make_version_dir=False)
                options = get_uc_options(uc, config_dict, webdriver_path)
                driver = uc.Chrome(
                    driver_executable_path=chromedriver_path, options=options)
            except Exception as exc2:
                print(exc2)
                pass
    else:
        print("WebDriver not found at path:", chromedriver_path)

    if driver is None:
        print('WebDriver object is still None..., try download by uc.')
        try:
            options = get_uc_options(uc, config_dict, webdriver_path)
            driver = uc.Chrome(options=options)
        except Exception as exc:
            print(exc)
            error_message = str(exc)
            left_part = None
            if "Stacktrace:" in error_message:
                left_part = error_message.split("Stacktrace:")[0]
                print(left_part)

            if "This version of ChromeDriver only supports Chrome version" in error_message:
                print(CONST_CHROME_VERSION_NOT_MATCH_EN)
                print(CONST_CHROME_VERSION_NOT_MATCH_TW)
            pass

    if driver is None:
        print("create web drive object by undetected_chromedriver fail!")

        if os.path.exists(chromedriver_path):
            print("Unable to use undetected_chromedriver, ")
            print("try to use local chromedriver to launch chrome browser.")
            driver_type = "selenium"
            driver = load_chromdriver_normal(config_dict, driver_type)
        else:
            print("建議您自行下載 ChromeDriver 到 webdriver 的資料夾下")
            print("you need manually download ChromeDriver to webdriver folder.")

    return driver


def close_browser_tabs(driver):
    if not driver is None:
        try:
            window_handles_count = len(driver.window_handles)
            if window_handles_count > 1:
                driver.switch_to.window(driver.window_handles[1])
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
        except Exception as excSwithFail:
            pass


def get_driver_by_config(config_dict):
    driver = None

    # read config.
    homepage = config_dict["homepage"]

    # output config:
    print("current time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("maxbot app version:", CONST_APP_VERSION)
    print("python version:", platform.python_version())
    print("platform:", platform.platform())
    print("homepage:", homepage)
    print("browser:", config_dict["browser"])
    # print("headless:", config_dict["advanced"]["headless"])
    # print("ticket_number:", str(config_dict["ticket_number"]))

    # print(config_dict["tixcraft"])
    # print("==[advanced config]==")
    if config_dict["advanced"]["verbose"]:
        print(config_dict["advanced"])
    print("webdriver_type:", config_dict["webdriver_type"])

    # entry point
    if homepage is None:
        homepage = ""

    Root_Dir = util.get_app_root()
    webdriver_path = os.path.join(Root_Dir, "webdriver")
    # print("platform.system().lower():", platform.system().lower())

    if config_dict["browser"] in ["chrome", "brave"]:
        # method 6: Selenium Stealth
        if config_dict["webdriver_type"] == CONST_WEBDRIVER_TYPE_SELENIUM:
            driver = load_chromdriver_normal(
                config_dict, config_dict["webdriver_type"])
        if config_dict["webdriver_type"] == CONST_WEBDRIVER_TYPE_UC:
            # method 5: uc
            # multiprocessing not work bug.
            if platform.system().lower() == "windows":
                if hasattr(sys, 'frozen'):
                    from multiprocessing import freeze_support
                    freeze_support()
            driver = load_chromdriver_uc(config_dict)

        # [新增] 讓 Dogocr_tixcraft 也使用 uc (undetected_chromedriver) 啟動
        if config_dict["webdriver_type"] == "Dogg":
            if platform.system().lower() == "windows":
                if hasattr(sys, 'frozen'):
                    from multiprocessing import freeze_support
                    freeze_support()
            driver = load_chromdriver_uc(config_dict)

        if config_dict["webdriver_type"] == CONST_WEBDRIVER_TYPE_DP:
            # driver = ChromiumPage()
            pass

    if config_dict["browser"] == "firefox":
        # default os is linux/mac
        # download url: https://github.com/mozilla/geckodriver/releases
        chromedriver_path = os.path.join(webdriver_path, "geckodriver")
        if platform.system().lower() == "windows":
            chromedriver_path = os.path.join(webdriver_path, "geckodriver.exe")

        if "macos" in platform.platform().lower():
            if "arm64" in platform.platform().lower():
                chromedriver_path = os.path.join(
                    webdriver_path, "geckodriver_arm")

        webdriver_service = Service(chromedriver_path)
        driver = None
        try:
            from selenium.webdriver.firefox.options import Options
            options = Options()
            if config_dict["advanced"]["headless"]:
                options.add_argument('--headless')
                # options.add_argument('--headless=new')
            if platform.system().lower() == "windows":
                binary_path = "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
                if not os.path.exists(binary_path):
                    binary_path = os.path.expanduser(
                        '~') + "\\AppData\\Local\\Mozilla Firefox\\firefox.exe"
                if not os.path.exists(binary_path):
                    binary_path = "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"
                if not os.path.exists(binary_path):
                    binary_path = "D:\\Program Files\\Mozilla Firefox\\firefox.exe"
                options.binary_location = binary_path

            driver = webdriver.Firefox(
                service=webdriver_service, options=options)
        except Exception as exc:
            error_message = str(exc)
            left_part = None
            if "Stacktrace:" in error_message:
                left_part = error_message.split("Stacktrace:")[0]
                print(left_part)
            else:
                print(exc)

    if config_dict["browser"] == "edge":
        # default os is linux/mac
        # download url: https://developer.microsoft.com/zh-tw/microsoft-edge/tools/webdriver/
        chromedriver_path = os.path.join(webdriver_path, "msedgedriver")
        if platform.system().lower() == "windows":
            chromedriver_path = os.path.join(
                webdriver_path, "msedgedriver.exe")

        webdriver_service = Service(chromedriver_path)
        chrome_options = get_chrome_options(webdriver_path, config_dict)

        driver = None
        try:
            driver = webdriver.Edge(
                service=webdriver_service, options=chrome_options)
        except Exception as exc:
            error_message = str(exc)
            # print(error_message)
            left_part = None
            if "Stacktrace:" in error_message:
                left_part = error_message.split("Stacktrace:")[0]
                print(left_part)

    if config_dict["browser"] == "safari":
        driver = None
        try:
            driver = webdriver.Safari()
        except Exception as exc:
            error_message = str(exc)
            # print(error_message)
            left_part = None
            if "Stacktrace:" in error_message:
                left_part = error_message.split("Stacktrace:")[0]
                print(left_part)

    if driver is None:
        print("create web driver object fail @_@;")
    else:
        try:
            NETWORK_BLOCKED_URLS = []

            if config_dict["advanced"]["adblock"]:
                NETWORK_BLOCKED_URLS = [
                    '*.clarity.ms/*',
                    '*.doubleclick.net/*',
                    '*.lndata.com/*',
                    '*.rollbar.com/*',
                    '*.twitter.com/i/*',
                    '*/adblock.js',
                    '*/ads.js',
                    '*/google_ad_block.js',
                    '*anymind360.com/*',
                    '*cdn.cookielaw.org/*',
                    '*e2elog.fetnet.net*',
                    '*fundingchoicesmessages.google.com/*',
                    '*google-analytics.*',
                    '*googlesyndication.*',
                    '*googletagmanager.*',
                    '*googletagservices.*',
                    '*img.uniicreative.com/*',
                    '*platform.twitter.com/*',
                    '*play.google.com/*',
                    '*player.youku.*',
                    '*syndication.twitter.com/*',
                    '*youtube.com/*',
                ]

            if config_dict["advanced"]["hide_some_image"]:
                NETWORK_BLOCKED_URLS.append('*.woff')
                NETWORK_BLOCKED_URLS.append('*.woff2')
                NETWORK_BLOCKED_URLS.append('*.ttf')
                NETWORK_BLOCKED_URLS.append('*.otf')
                NETWORK_BLOCKED_URLS.append(
                    '*fonts.googleapis.com/earlyaccess/*')
                NETWORK_BLOCKED_URLS.append('*/ajax/libs/font-awesome/*')
                NETWORK_BLOCKED_URLS.append('*.ico')
                NETWORK_BLOCKED_URLS.append(
                    '*ticketimg2.azureedge.net/image/ActivityImage/*')
                NETWORK_BLOCKED_URLS.append(
                    '*static.tixcraft.com/images/activity/*')
                NETWORK_BLOCKED_URLS.append(
                    '*static.ticketmaster.sg/images/activity/*')
                NETWORK_BLOCKED_URLS.append(
                    '*static.ticketmaster.com/images/activity/*')
                NETWORK_BLOCKED_URLS.append(
                    '*ticketimg2.azureedge.net/image/ActivityImage/ActivityImage_*')
                NETWORK_BLOCKED_URLS.append(
                    '*.azureedge.net/QWARE_TICKET//images/*')
                NETWORK_BLOCKED_URLS.append(
                    '*static.ticketplus.com.tw/event/*')
                NETWORK_BLOCKED_URLS.append('*.css')  # 直接全擋樣式表，畫面會醜到爆，但載入極快

                # NETWORK_BLOCKED_URLS.append('https://kktix.cc/change_locale?locale=*')
                NETWORK_BLOCKED_URLS.append(
                    'https://t.kfs.io/assets/logo_*.png')
                NETWORK_BLOCKED_URLS.append(
                    'https://t.kfs.io/assets/icon-*.png')
                NETWORK_BLOCKED_URLS.append(
                    'https://t.kfs.io/upload_images/*.jpg')

            if config_dict["advanced"]["block_facebook_network"]:
                NETWORK_BLOCKED_URLS.append('*facebook.com/*')
                NETWORK_BLOCKED_URLS.append('*.fbcdn.net/*')

            # Chrome DevTools Protocal
            if config_dict["browser"] in CONST_CHROME_FAMILY:
                driver.execute_cdp_cmd('Network.setBlockedURLs', {
                                       "urls": NETWORK_BLOCKED_URLS})
                driver.execute_cdp_cmd('Network.enable', {})

            if 'kktix.c' in homepage:
                if len(config_dict["advanced"]["kktix_account"]) > 0:
                    # for like human.
                    try:
                        driver.get(homepage)
                        time.sleep(5)
                    except Exception as e:
                        pass
                    if not 'https://kktix.com/users/sign_in?' in homepage:
                        homepage = CONST_KKTIX_SIGN_IN_URL % (homepage)

            if 'famiticket.com' in homepage:
                if len(config_dict["advanced"]["fami_account"]) > 0:
                    homepage = CONST_FAMI_SIGN_IN_URL

            if 'kham.com' in homepage:
                if len(config_dict["advanced"]["kham_account"]) > 0:
                    homepage = CONST_KHAM_SIGN_IN_URL

            if 'ticket.com.tw' in homepage:
                if len(config_dict["advanced"]["ticket_account"]) > 0:
                    homepage = CONST_TICKET_SIGN_IN_URL

            if 'urbtix.hk' in homepage:
                if len(config_dict["advanced"]["urbtix_account"]) > 0:
                    homepage = CONST_URBTIX_SIGN_IN_URL

            if 'cityline.com' in homepage:
                if len(config_dict["advanced"]["cityline_account"]) > 0:
                    homepage = CONST_CITYLINE_SIGN_IN_URL

            if 'hkticketing.com' in homepage:
                if len(config_dict["advanced"]["hkticketing_account"]) > 0:
                    homepage = CONST_HKTICKETING_SIGN_IN_URL

            if 'ticketplus.com.tw' in homepage:
                if len(config_dict["advanced"]["ticketplus_account"]) > 1:
                    homepage = "https://ticketplus.com.tw/"

            print("goto url:", homepage)
            driver.get(homepage)
            time.sleep(3.0)

            tixcraft_family = False
            if 'tixcraft.com' in homepage:
                tixcraft_family = True

            if tixcraft_family:
                tixcraft_sid = config_dict["advanced"]["tixcraft_sid"]
                if len(tixcraft_sid) > 1:
                    driver.delete_cookie("SID")
                    domain_name = homepage.split('/')[2]
                    driver.add_cookie({"name": "SID", "value": tixcraft_sid,
                                      "domain": domain_name, "path": "/", "secure": True})
                    driver.refresh()

        except WebDriverException as exce2:
            print('oh no not again, WebDriverException')
            print('WebDriverException:', exce2)
        except Exception as exce1:
            print('get URL Exception:', exce1)
            pass

    return driver


def force_press_button_iframe(driver, f, select_by, select_query, force_submit=True):
    if not f:
        # ensure we are on main content frame
        try:
            driver.switch_to.default_content()
        except Exception as exc:
            pass
    else:
        try:
            driver.switch_to.frame(f)
        except Exception as exc:
            pass

    is_clicked = press_button(driver, select_by, select_query, force_submit)

    if f:
        # switch back to main content, otherwise we will get StaleElementReferenceException
        try:
            driver.switch_to.default_content()
        except Exception as exc:
            pass

    return is_clicked


def remove_attribute_tag_by_selector(driver, select_query, class_name, more_script=""):
    element_script = "eachItem.removeAttribute('" + class_name + "');"
    javascript_tag_by_selector(
        driver, select_query, element_script, more_script=more_script)


def remove_class_tag_by_selector(driver, select_query, class_name, more_script=""):
    element_script = "eachItem.classList.remove('" + class_name + "');"
    javascript_tag_by_selector(
        driver, select_query, element_script, more_script=more_script)


def hide_tag_by_selector(driver, select_query, more_script=""):
    element_script = "eachItem.style='display:none;';"
    javascript_tag_by_selector(
        driver, select_query, element_script, more_script=more_script)


def clean_tag_by_selector(driver, select_query, more_script=""):
    element_script = "eachItem.outerHTML='';"
    javascript_tag_by_selector(
        driver, select_query, element_script, more_script=more_script)

# PS: selector query string must without single quota.


def javascript_tag_by_selector(driver, select_query, element_script, more_script=""):
    try:
        driver.set_script_timeout(1)
        js = """var selectSoldoutItems = document.querySelectorAll('%s');
selectSoldoutItems.forEach((eachItem) =>
{%s});
%s""" % (select_query, element_script, more_script)

        # print("javascript:", js)
        driver.execute_script(js)
        ret = True
    except Exception as exc:
        # print(exc)
        pass


def press_button(driver, select_by, select_query, force_submit=True):
    ret = False
    next_step_button = None
    try:
        next_step_button = driver.find_element(select_by, select_query)
        if not next_step_button is None:
            if next_step_button.is_enabled():
                next_step_button.click()
                ret = True
    except Exception as exc:
        # print("find %s clickable Exception:" % (select_query))
        # print(exc)
        pass

        if force_submit:
            if not next_step_button is None:
                is_visible = False
                try:
                    if next_step_button.is_enabled():
                        is_visible = True
                except Exception as exc:
                    pass

                if is_visible:
                    try:
                        driver.set_script_timeout(1)
                        driver.execute_script(
                            "arguments[0].click();", next_step_button)
                        ret = True
                    except Exception as exc:
                        pass
    return ret

# close some div on home url.


def tixcraft_home_close_window(driver):
    accept_all_cookies_btn = None
    try:
        accept_all_cookies_btn = driver.find_element(
            By.CSS_SELECTOR, '#onetrust-accept-btn-handler')
        if accept_all_cookies_btn:
            accept_all_cookies_btn.click()
    except Exception as exc:
        # print(exc)
        pass

# from detail to game


def tixcraft_redirect(driver, url):
    ret = False
    game_name = ""
    url_split = url.split("/")
    if len(url_split) >= 6:
        game_name = url_split[5]
    if len(game_name) > 0:
        if "/activity/detail/%s" % (game_name,) in url:
            entry_url = url.replace("/activity/detail/", "/activity/game/")
            print("redirec to new url:", entry_url)
            try:
                driver.get(entry_url)
                ret = True
            except Exception as exec1:
                pass
    return ret


def tixcraft_date_auto_select(driver, url, config_dict, domain_name):
    # 自動刷新程式設定檔
    reload_critical_settings(config_dict)

    show_debug_message = True    # debug.
    show_debug_message = False   # online

    if config_dict["advanced"]["verbose"]:
        show_debug_message = True

    # read config.
    auto_select_mode = config_dict["date_auto_select"]["mode"]
    date_keyword = config_dict["date_auto_select"]["date_keyword"].strip()
    pass_date_is_sold_out_enable = config_dict["tixcraft"]["pass_date_is_sold_out"]
    auto_reload_coming_soon_page_enable = config_dict["tixcraft"]["auto_reload_coming_soon_page"]

    # PS: for big events, check sold out text maybe not helpful, due to database is too busy.
    sold_out_text_list = ["選購一空", "已售完",
                          "No tickets available", "Sold out", "空席なし", "完売した"]
    # PS: "Start ordering" for indievox.com.
    find_ticket_text_list = [
        '立即訂購', 'Find tickets', 'Start ordering', 'お申込みへ進む']

    game_name = ""

    if "/activity/game/" in url:
        url_split = url.split("/")
        if len(url_split) >= 6:
            game_name = url_split[5]

    if show_debug_message:
        print('get date game_name:', game_name)
        print("date_auto_select_mode:", auto_select_mode)
        print("date_keyword:", date_keyword)

    check_game_detail = False
    # choose date
    if "/activity/game/%s" % (game_name,) in url:
        if show_debug_message:
            if len(date_keyword) == 0:
                print("date keyword is empty.")
            else:
                print("date keyword:", date_keyword)
        check_game_detail = True

    area_list = None
    if check_game_detail:
        if show_debug_message:
            print("start to query #gameList info.")
        my_css_selector = '#gameList > table > tbody > tr'
        try:
            area_list = driver.find_elements(By.CSS_SELECTOR, my_css_selector)
            if not area_list is None:
                if len(area_list) == 0:
                    # only headless mode detected now.
                    if config_dict["advanced"]["headless"]:
                        html_body = driver.page_source
                        if not html_body is None:
                            if len(html_body) > 0:
                                html_text = util.remove_html_tags(html_body)
                                bot_detected_string_list = ['Your Session Has Been Suspended', 'Something about your browsing behavior or network made us think you were a bot', 'Your browser hit a snag and we need to make sure you'
                                                            ]
                                for each_string in bot_detected_string_list:
                                    print(html_text)
                                    break
        except Exception as exc:
            print("find #gameList fail")

    is_coming_soon = False
    coming_soon_condictions_list_en = [
        ' day(s)', ' hrs.', ' min', ' sec', ' till sale starts!', '0', ':']
    coming_soon_condictions_list_tw = [
        '開賣', '剩餘', ' 天', ' 小時', ' 分鐘', ' 秒', '0', ':', '20']
    coming_soon_condictions_list_ja = [
        '発売開始', ' 日', ' 時間', ' 分', ' 秒', '0', ':', '20']
    coming_soon_condictions_list = coming_soon_condictions_list_en
    html_lang = "en-US"
    try:
        html_body = driver.page_source
        if not html_body is None:
            if len(html_body) > 0:
                if '<head' in html_body:
                    html = html_body.split("<head")[0]
                    html_lang = html.split('"')[1]
                    if show_debug_message:
                        print("html lang:", html_lang)
                    if html_lang == "zh-TW":
                        coming_soon_condictions_list = coming_soon_condictions_list_tw
                    if html_lang == "ja":
                        coming_soon_condictions_list = coming_soon_condictions_list_ja
    except Exception as e:
        pass

    matched_blocks = None
    formated_area_list = None

    if not area_list is None:
        area_list_count = len(area_list)
        if show_debug_message:
            print("date_list_count:", area_list_count)

        if area_list_count > 0:
            formated_area_list = []
            for row in area_list:
                row_text = ""
                row_html = ""
                try:
                    # row_text = row.text
                    row_html = row.get_attribute('innerHTML')
                    row_text = util.remove_html_tags(row_html)
                except Exception as exc:
                    if show_debug_message:
                        print(exc)
                    # error, exit loop
                    break

                if len(row_text) > 0:
                    if util.reset_row_text_if_match_keyword_exclude(config_dict, row_text):
                        row_text = ""

                if len(row_text) > 0:

                    # check is coming soon events in list.
                    is_match_all_coming_soon_condiction = True
                    for condiction_string in coming_soon_condictions_list:
                        if not condiction_string in row_text:
                            is_match_all_coming_soon_condiction = False
                            break
                    is_coming_soon = False
                    if is_match_all_coming_soon_condiction:
                        if show_debug_message:
                            print("match coming soon condiction at row:", row_text)
                        is_coming_soon = True

                    if is_coming_soon:
                        if auto_reload_coming_soon_page_enable:
                            continue

                    row_is_enabled = False
                    for text_item in find_ticket_text_list:
                        if text_item in row_text:
                            row_is_enabled = True
                            break

                    # check sold out text.
                    if row_is_enabled:
                        if pass_date_is_sold_out_enable:
                            for sold_out_item in sold_out_text_list:
                                row_text_right_part = row_text[(
                                    len(sold_out_item)+5)*-1:]
                                if show_debug_message:
                                    # print("check right part text:", row_text_right_part)
                                    pass
                                if sold_out_item in row_text_right_part:
                                    row_is_enabled = False
                                    if show_debug_message:
                                        print("match sold out text: %s, skip this row." % (
                                            sold_out_item))
                                    break

                    if row_is_enabled:
                        formated_area_list.append(row)

            if show_debug_message:
                print("formated_area_list count:", len(formated_area_list))

            if len(date_keyword) == 0:
                matched_blocks = formated_area_list
            else:
                # match keyword.
                if show_debug_message:
                    print("start to match formated keyword:", date_keyword)

                matched_blocks = util.get_matched_blocks_by_keyword(
                    config_dict, auto_select_mode, date_keyword, formated_area_list)

                if show_debug_message:
                    if not matched_blocks is None:
                        print("after match keyword, found count:",
                              len(matched_blocks))
        else:
            print("not found date-time-position")
            pass
    else:
        print("date date-time-position is None")
        pass

    target_area = util.get_target_item_from_matched_list(
        matched_blocks, auto_select_mode)

    is_date_clicked = False
    if not target_area is None:
        if show_debug_message:
            print("取得目標日期 , 點擊立即購票")

        # ================= [計時起點 1] =================
        global tixcraft_dict
        if 'tixcraft_dict' in globals():
            tixcraft_dict["click_start_time"] = time.time()
            print("開始記時")
        # ===============================================

        is_date_clicked = press_button(target_area, By.CSS_SELECTOR, 'button')
        if not is_date_clicked:
            if show_debug_message:
                print("press button fail, try to click hyperlink.")

            if "tixcraft" in domain_name:
                try:
                    data_href = target_area.get_attribute("data-href")
                    if not data_href is None:
                        print("goto url:", data_href)
                        driver.get(data_href)
                    else:
                        if show_debug_message:
                            print("data-href not ready")

                        # delay 200ms to click.
                        # driver.set_script_timeout(0.3)
                        # js="""setTimeout(function(){arguments[0].click()},200);"""
                        # driver.execute_script(js, target_area)
                except Exception as exc:
                    pass

            # for: ticketmaster.sg
            is_date_clicked = press_button(target_area, By.CSS_SELECTOR, 'a')

    # [PS]: current reload condition only when
    if auto_reload_coming_soon_page_enable:
        if is_coming_soon:
            if show_debug_message:
                print("match is_coming_soon, start to reload page.")

            # case 2: match one row is coming soon.
            try:
                driver.refresh()
            except Exception as exc:
                pass

            if config_dict["advanced"]["auto_reload_page_interval"] > 0:
                time.sleep(config_dict["advanced"]
                           ["auto_reload_page_interval"])
        else:
            if not is_date_clicked:
                if not formated_area_list is None:
                    if len(formated_area_list) == 0:
                        print('start to refresh page.')
                        try:
                            driver.refresh()
                            time.sleep(0.3)
                        except Exception as exc:
                            pass

                        if config_dict["advanced"]["auto_reload_page_interval"] > 0:
                            time.sleep(
                                config_dict["advanced"]["auto_reload_page_interval"])

    return is_date_clicked


def get_tixcraft_target_area(el, config_dict, area_keyword_item):
    show_debug_message = True       # debug.
    show_debug_message = False      # online

    if config_dict["advanced"]["verbose"]:
        show_debug_message = True

    # read config.
    area_auto_select_mode = config_dict["area_auto_select"]["mode"]

    is_need_refresh = False
    matched_blocks = None

    area_list = None
    area_list_count = 0
    if not el is None:
        try:
            area_list = el.find_elements(By.TAG_NAME, 'a')
        except Exception as exc:
            # print("find area list a tag fail")
            pass

        if not area_list is None:
            area_list_count = len(area_list)
            if area_list_count == 0:
                print("area list is empty, do refresh!")
                is_need_refresh = True
        else:
            print("area list is None, do refresh!")
            is_need_refresh = True

    if area_list_count > 0:
        matched_blocks = []
        for row in area_list:
            row_text = ""
            row_html = ""
            try:
                # row_text = row.text
                row_html = row.get_attribute('innerHTML')
                row_text = util.remove_html_tags(row_html)
            except Exception as exc:
                if show_debug_message:
                    print(exc)
                # error, exit loop
                break

            if len(row_text) > 0:
                if util.reset_row_text_if_match_keyword_exclude(config_dict, row_text):
                    row_text = ""

            if len(row_text) > 0:
                # clean stop word.
                row_text = util.format_keyword_string(row_text)

                is_append_this_row = False

                if len(area_keyword_item) > 0:
                    # must match keyword.
                    is_append_this_row = True
                    area_keyword_array = area_keyword_item.split(' ')
                    for area_keyword in area_keyword_array:
                        area_keyword = util.format_keyword_string(area_keyword)
                        if not area_keyword in row_text:
                            is_append_this_row = False
                            break
                else:
                    # without keyword.
                    is_append_this_row = True

                if is_append_this_row:
                    if config_dict["ticket_number"] > 1:
                        area_item_font_el = None
                        try:
                            # print('try to find font tag at row:', row_text)
                            area_item_font_el = row.find_element(
                                By.TAG_NAME, 'font')
                            if not area_item_font_el is None:
                                font_el_text = area_item_font_el.text
                                if font_el_text is None:
                                    font_el_text = ""
                                font_el_text = "@%s@" % (font_el_text)
                                if show_debug_message:
                                    print('font tag text:', font_el_text)
                                    pass
                                for check_item in CONT_STRING_1_SEATS_REMAINING:
                                    if check_item in font_el_text:
                                        if show_debug_message:
                                            print(
                                                "match pass 1 seats remaining 1 full text:", row_text)
                                            print(
                                                "match pass 1 seats remaining 2 font text:", font_el_text)
                                        is_append_this_row = False
                            else:
                                # print("row withou font tag.")
                                pass
                        except Exception as exc:
                            # print("find font text in a tag fail:", exc)
                            pass

                if show_debug_message:
                    print("is_append_this_row:", is_append_this_row)

                if is_append_this_row:
                    matched_blocks.append(row)

                    if area_auto_select_mode == CONST_FROM_TOP_TO_BOTTOM:
                        # print("only need first item, break area list loop.")
                        break

        if len(matched_blocks) == 0:
            matched_blocks = None
            is_need_refresh = True

    return is_need_refresh, matched_blocks


def tixcraft_area_auto_select(driver, url, config_dict):
    show_debug_message = True       # debug.
    show_debug_message = False      # online

    if config_dict["advanced"]["verbose"]:
        show_debug_message = True

    # read config.
    area_keyword = config_dict["area_auto_select"]["area_keyword"].strip()
    auto_select_mode = config_dict["area_auto_select"]["mode"]

    ticket_number = config_dict["ticket_number"]

    if show_debug_message:
        print("area_keyword:", area_keyword)

    el = None
    try:
        el = driver.find_element(By.CSS_SELECTOR, '.zone')
    except Exception as exc:
        print("find .zone fail, do nothing.")

    # ================= 風控冷卻機制 =================
        # 當連續找不到區域列表時，代表可能已經進入 404 或被鎖 IP 狀態
        # 這裡不直接結束，而是進入長等待，嘗試解鎖
        try:
            # 使用分段等待，每 10 秒印一次 Log，避免以為程式當機
            wait_seconds = 90
            for i in range(wait_seconds, 0, -10):
                print(f" 冷卻中... 剩餘 {i} 秒")
                time.sleep(10)

            print("✅ 冷卻結束，執行網頁重整...")
            driver.refresh()

            # 重整後稍微等待一下網頁載入，避免瞬間又抓不到
            time.sleep(3.0)

        except Exception as e:
            print(f"冷卻重整過程發生錯誤: {e}")
    # ===============================================================

    if not el is None:
        is_need_refresh = False
        matched_blocks = None

        if len(area_keyword) > 0:
            area_keyword_array = []
            try:
                area_keyword_array = json.loads("[" + area_keyword + "]")
            except Exception as exc:
                area_keyword_array = []
            for area_keyword_item in area_keyword_array:
                is_need_refresh, matched_blocks = get_tixcraft_target_area(
                    el, config_dict, area_keyword_item)
                if not is_need_refresh:
                    break
                else:
                    print("is_need_refresh for keyword:", area_keyword_item)
        else:
            # empty keyword, match all.
            is_need_refresh, matched_blocks = get_tixcraft_target_area(
                el, config_dict, "")

        target_area = util.get_target_item_from_matched_list(
            matched_blocks, auto_select_mode)

        if not target_area is None:
            # ================= [新增] 抓取並印出點擊的區域名稱 =================
            try:
                # 使用跟上面一樣的解碼方式，把 HTML 標籤濾掉只留純文字
                clicked_area_html = target_area.get_attribute('innerHTML')
                clicked_area_name = util.remove_html_tags(
                    clicked_area_html).strip()
                # 為了畫面整潔，將多餘的空白或換行符號拿掉
                clicked_area_name = " ".join(clicked_area_name.split())
                print(f"🎯 [區域選擇] 成功鎖定並點擊區域: {clicked_area_name}")
            except Exception as e:
                print("🎯 [區域選擇] 準備點擊目標區域...")
            # =================================================================

            try:
                target_area.click()
            except Exception as exc:
                print("click area a link fail, start to retry...")
                try:
                    driver.execute_script("arguments[0].click();", target_area)
                except Exception as exc:
                    print("click area a link fail, after reftry still fail.")
                    print(exc)
                    pass

        # auto refresh for area list page.
        if is_need_refresh:
            try:
                driver.refresh()
            except Exception as exc:
                pass

            # ================= 隨機刷新邏輯 =================
            try:
                # 1. 取得基礎設定秒數 (例如 6.0)
                base_interval = float(config_dict["advanced"].get(
                    "auto_reload_page_interval", 0))

                if base_interval > 0:
                    final_sleep_time = base_interval

                    # 2. 檢查是否啟用隨機模式
                    random_mode = config_dict["advanced"].get(
                        "auto_reload_random_mode", False)

                    if random_mode:
                        try:
                            # 讀取設定檔中的 "x.0秒數"
                            range_val = float(config_dict["advanced"].get(
                                "auto_reload_random_range", 0))

                            if range_val > 0:
                                min_sec = max(0.1, base_interval - range_val)
                                max_sec = base_interval + range_val

                                final_sleep_time = random.uniform(
                                    min_sec, max_sec)

                                print(
                                    f"🎲 [區域刷新] 基礎 {base_interval}s ± {range_val}s -> 本次等待 {final_sleep_time:.2f} 秒")
                        except Exception as e:
                            print(f"⚠️ 隨機參數解析錯誤 (請確認輸入的是單一數字): {e}")

                    # 4. 執行等待
                    time.sleep(final_sleep_time)

            except Exception as e:
                # 萬一發生任何錯誤，回退到最原始的固定等待
                print(f"刷新等待邏輯錯誤: {e}")
                if config_dict["advanced"]["auto_reload_page_interval"] > 0:
                    time.sleep(config_dict["advanced"]
                               ["auto_reload_page_interval"])
            # =================================================


def ticket_number_select_fill(driver, select_obj, ticket_number):
    is_ticket_number_assigned = False
    if not select_obj is None:
        try:
            # target ticket number
            select_obj.select_by_visible_text(ticket_number)
            # select.select_by_value(ticket_number)
            # select.select_by_index(int(ticket_number))
            is_ticket_number_assigned = True
        except Exception as exc:
            print("select_by_visible_text ticket_number fail")
            print(exc)

            try:
                # target ticket number
                select_obj.select_by_visible_text(ticket_number)
                # select.select_by_value(ticket_number)
                # select.select_by_index(int(ticket_number))
                is_ticket_number_assigned = True
            except Exception as exc:
                print("select_by_visible_text ticket_number fail...2")
                print(exc)

                # try buy one ticket
                try:
                    select_obj.select_by_visible_text("1")
                    # select.select_by_value("1")
                    # select.select_by_index(int(ticket_number))
                    is_ticket_number_assigned = True
                except Exception as exc:
                    print("select_by_visible_text 1 fail")
                    pass

    # Plan B.
    # if not is_ticket_number_assigned:
    if False:
        if not select is None:
            try:
                # target ticket number
                # select.select_by_visible_text(ticket_number)
                print("assign ticker number by jQuery:", ticket_number)
                driver.execute_script(
                    "$(\"input[type='select']\").val(\"" + ticket_number + "\");")
                is_ticket_number_assigned = True
            except Exception as exc:
                print("jQuery select_by_visible_text ticket_number fail (after click.)")
                print(exc)

    return is_ticket_number_assigned


def get_text_by_selector(driver, my_css_selector, attribute='innerHTML'):
    div_element = None
    try:
        div_element = driver.find_element(By.CSS_SELECTOR, my_css_selector)
    except Exception as exc:
        # print("find element fail")
        pass

    row_text = ""
    if not div_element is None:
        try:
            if attribute == 'innerText':
                row_html = div_element.get_attribute('innerHTML')
                row_text = util.remove_html_tags(row_html)
            else:
                row_text = div_element.get_attribute(attribute)
        except Exception as exc:
            print("get text fail:", my_css_selector)
    return row_text


def fill_common_verify_form(driver, config_dict, inferred_answer_string, fail_list, input_text_css, next_step_button_css, submit_by_enter, check_input_interval):
    show_debug_message = True       # debug.
    show_debug_message = False      # online

    if config_dict["advanced"]["verbose"]:
        show_debug_message = True

    form_input_list = []
    try:
        form_input_list = driver.find_elements(By.CSS_SELECTOR, input_text_css)
    except Exception as exc:
        if show_debug_message:
            print("find verify code input textbox fail")
        pass
    if form_input_list is None:
        form_input_list = []

    form_input_count = len(form_input_list)
    if show_debug_message:
        print("input textbox count:", form_input_count)

    is_do_press_next_button = False

    form_input_1 = None
    form_input_2 = None
    if form_input_count > 0:
        form_input_1 = form_input_list[0]
        if form_input_count > 1:
            form_input_2 = form_input_list[1]

    is_multi_question_mode = False
    answer_list = util.get_answer_list_from_user_guess_string(
        config_dict, CONST_MAXBOT_ANSWER_ONLINE_FILE)
    if form_input_count == 1:
        is_do_press_next_button = True
    else:
        if form_input_count == 2:
            if not form_input_2 is None:
                if len(answer_list) >= 2:
                    if (len(answer_list[0]) > 0):
                        if (len(answer_list[1]) > 0):
                            is_multi_question_mode = True

    inputed_value_1 = None
    if not form_input_1 is None:
        try:
            inputed_value_1 = form_input_1.get_attribute('value')
        except Exception as exc:
            if show_debug_message:
                print("get_attribute of verify code fail")
            pass
    if inputed_value_1 is None:
        inputed_value_1 = ""

    inputed_value_2 = None
    if not form_input_2 is None:
        try:
            inputed_value_2 = form_input_2.get_attribute('value')
        except Exception as exc:
            if show_debug_message:
                print("get_attribute of verify code fail")
            pass
    if inputed_value_2 is None:
        inputed_value_2 = ""

    is_answer_sent = False
    if not is_multi_question_mode:
        if not form_input_1 is None:
            if len(inferred_answer_string) > 0:
                if inputed_value_1 != inferred_answer_string:
                    try:
                        # PS: sometime may send key twice...
                        form_input_1.clear()
                        form_input_1.send_keys(inferred_answer_string)
                    except Exception as exc:
                        if show_debug_message:
                            print(exc)
                        pass

                is_button_clicked = False
                try:
                    if is_do_press_next_button:
                        if submit_by_enter:
                            form_input_1.send_keys(Keys.ENTER)
                            is_button_clicked = True
                        else:
                            if len(next_step_button_css) > 0:
                                is_button_clicked = press_button(
                                    driver, By.CSS_SELECTOR, next_step_button_css)
                except Exception as exc:
                    if show_debug_message:
                        print(exc)
                    pass

                if is_button_clicked:
                    is_answer_sent = True
                    fail_list.append(inferred_answer_string)
                    if show_debug_message:
                        print("sent password by bot:",
                              inferred_answer_string, " at #", len(fail_list))

                if is_answer_sent:
                    for i in range(3):
                        time.sleep(0.1)
                        alert_ret = check_pop_alert(driver)
                        if alert_ret:
                            if show_debug_message:
                                print("press accept button at time #", i+1)
                            break
            else:
                # no answer to fill.
                if len(inputed_value_1) == 0:
                    try:
                        # solution 1: js.
                        driver.execute_script(
                            "if(!(document.activeElement === arguments[0])){arguments[0].focus();}", form_input_1)
                        # solution 2: selenium.
                        # form_input_1.click()
                        time.sleep(check_input_interval)
                    except Exception as exc:
                        pass
    else:
        # multi question mode.
        try:
            if inputed_value_1 != answer_list[0]:
                form_input_1.clear()
                form_input_1.send_keys(answer_list[0])

            if inputed_value_2 != answer_list[1]:
                form_input_2.clear()
                form_input_2.send_keys(answer_list[1])

            is_button_clicked = False
            form_input_2.send_keys(Keys.ENTER)
            if len(next_step_button_css) > 0:
                is_button_clicked = press_button(
                    driver, By.CSS_SELECTOR, next_step_button_css)

            if is_button_clicked:
                is_answer_sent = True
                fail_list.append(answer_list[0])
                fail_list.append(answer_list[1])
                if show_debug_message:
                    print("sent password by bot:",
                          inferred_answer_string, " at #", len(fail_list))
        except Exception as exc:
            pass

    return is_answer_sent, fail_list


def tixcraft_verify(driver, config_dict, fail_list):
    question_selector = '.zone-verify'
    return tixcraft_input_check_code(driver, config_dict, fail_list, question_selector)


def tixcraft_input_check_code(driver, config_dict, fail_list, question_selector):
    show_debug_message = True       # debug.
    show_debug_message = False      # online

    if config_dict["advanced"]["verbose"]:
        show_debug_message = True

    answer_list = []

    question_text = get_text_by_selector(
        driver, question_selector, 'innerText')
    if show_debug_message:
        print("question_text:", question_text)
    if len(question_text) > 0:
        write_question_to_file(question_text)

        answer_list = util.get_answer_list_from_user_guess_string(
            config_dict, CONST_MAXBOT_ANSWER_ONLINE_FILE)
        if len(answer_list) == 0:
            if config_dict["advanced"]["auto_guess_options"]:
                answer_list = util.guess_tixcraft_question(
                    driver, question_text)

        inferred_answer_string = ""
        for answer_item in answer_list:
            if not answer_item in fail_list:
                inferred_answer_string = answer_item
                break

        if show_debug_message:
            print("inferred_answer_string:", inferred_answer_string)
            print("answer_list:", answer_list)

        # PS: auto-focus() when empty inferred_answer_string with empty inputed text value.
        input_text_css = "input[name='checkCode']"
        next_step_button_css = ""
        submit_by_enter = True
        check_input_interval = 0.2
        is_answer_sent, fail_list = fill_common_verify_form(
            driver, config_dict, inferred_answer_string, fail_list, input_text_css, next_step_button_css, submit_by_enter, check_input_interval)

    return fail_list


def tixcraft_change_captcha(driver, url):
    try:
        driver.execute_script(
            f"document.querySelector('.verify-img').children[0].setAttribute('src','{url}');")
    except Exception as exc:
        print("edit captcha element fail")


def tixcraft_toast(driver, message):
    toast_element = None
    try:
        my_css_selector = "p.remark-word"
        toast_element = driver.find_element(By.CSS_SELECTOR, my_css_selector)
        if not toast_element is None:
            driver.execute_script(
                "arguments[0].innerHTML='%s';" % message, toast_element)
    except Exception as exc:
        # print("find toast element fail")
        pass


def tixcraft_keyin_captcha_code(driver, answer="", auto_submit=False):
    is_verifyCode_editing = False
    is_form_sumbited = False

    # manually keyin verify code.
    # start to input verify code.
    form_verifyCode = None
    try:
        form_verifyCode = driver.find_element(
            By.CSS_SELECTOR, '#TicketForm_verifyCode')
    except Exception as exc:
        print("find form_verifyCode fail")

    if not form_verifyCode is None:
        is_visible = False
        try:
            if form_verifyCode.is_enabled():
                is_visible = True
        except Exception as exc:
            pass

        inputed_value = None
        try:
            inputed_value = form_verifyCode.get_attribute('value')
        except Exception as exc:
            print("find verify code fail")
            pass

        if inputed_value is None:
            inputed_value = ""
            is_visible = False

        if is_visible:
            is_text_clicked = False

            if inputed_value == "":
                try:
                    form_verifyCode.click()
                    is_text_clicked = True
                    is_verifyCode_editing = True
                except Exception as exc:
                    print("click form_verifyCode fail, trying to use javascript.")
                    # plan B
                    try:
                        driver.execute_script(
                            "document.getElementById(\"TicketForm_verifyCode\").focus();")
                        is_verifyCode_editing = True
                    except Exception as exc:
                        # print("click form_verifyCode fail.")
                        pass

            if len(answer) > 0:
                # print("start to fill answer.")
                try:
                    if not is_text_clicked:
                        form_verifyCode.click()
                    form_verifyCode.clear()
                    form_verifyCode.send_keys(answer)

                    if auto_submit:
                        form_verifyCode.send_keys(Keys.ENTER)
                        is_verifyCode_editing = False
                        is_form_sumbited = True

                    else:
                        driver.execute_script(
                            "document.getElementById(\"TicketForm_verifyCode\").select();")
                        # TODO: show text message on ticketmaster web page.
                        tixcraft_toast(driver, "※ 按 Enter 如果答案是: " + answer)
                except Exception as exc:
                    print("send_keys ocr answer fail.")

    return is_verifyCode_editing, is_form_sumbited


def tixcraft_reload_captcha(driver, domain_name):
    # manually keyin verify code.
    # start to input verify code.
    ret = False
    form_captcha = None
    try:
        image_id = 'TicketForm_verifyCode-image'
        if 'indievox.com' in domain_name:
            image_id = 'TicketForm_verifyCode-image'
        form_captcha = driver.find_element(By.CSS_SELECTOR, "#" + image_id)
        if not form_captcha is None:
            form_captcha.click()
            ret = True
    except Exception as exc:
        print("find form_captcha fail")

    return ret


def tixcraft_get_ocr_answer(driver, ocr, ocr_captcha_image_source, Captcha_Browser, domain_name):
    show_debug_message = True       # debug.
    show_debug_message = False      # online

    ocr_answer = None
    if not ocr is None:
        img_base64 = None

        # 1. 如果是透過 NonBrowser (requests) 抓取的
        if ocr_captcha_image_source == CONST_OCR_CAPTCH_IMAGE_SOURCE_NON_BROWSER:
            if not Captcha_Browser is None:
                img_base64 = base64.b64decode(
                    Captcha_Browser.request_captcha())

        # 2. 如果是透過 Canvas 截圖抓取的
        if ocr_captcha_image_source == CONST_OCR_CAPTCH_IMAGE_SOURCE_CANVAS:
            image_id = 'TicketForm_verifyCode-image'
            image_element = None
            try:
                my_css_selector = "#" + image_id
                image_element = driver.find_elements(
                    By.CSS_SELECTOR, my_css_selector)
            except Exception as exc:
                pass

            if not image_element is None:
                if 'indievox.com' in domain_name:
                    # image_id = 'TicketForm_verifyCode-image'
                    pass
                try:
                    driver.set_script_timeout(1)
                    form_verifyCode_base64 = driver.execute_async_script("""
                        var canvas = document.createElement('canvas');
                        var context = canvas.getContext('2d');
                        var img = document.getElementById('%s');
                        var callback = arguments[arguments.length - 1]; // 宣告移到外面
                        
                        // 判斷圖片是否已經確實載入完畢且有高度
                        if(img != null && img.complete && img.naturalHeight !== 0) {
                            canvas.height = img.naturalHeight;
                            canvas.width = img.naturalWidth;
                            context.drawImage(img, 0, 0);
                            callback(canvas.toDataURL()); 
                        } else {
                            callback(null); // ⚠️ 圖片還沒好就立刻放行，絕對不卡死等待！
                        }
                    """ % (image_id))

                    if not form_verifyCode_base64 is None:
                        # 這裡解碼後得到的已經是 bytes (二進制資料)
                        img_base64 = base64.b64decode(
                            form_verifyCode_base64.split(',')[1])

                except Exception as exc:
                    if show_debug_message:
                        print("canvas exception:", str(exc))
                    pass

                    if img_base64 is None:
                        if not Captcha_Browser is None:
                            print("canvas get image fail, use plan_b: NonBrowser")
                            img_base64 = base64.b64decode(
                                Captcha_Browser.request_captcha())
                except Exception as exc:
                    if show_debug_message:
                        print("canvas exception:", str(exc))
                    pass

        # 3. 進行辨識
        if not img_base64 is None:
            try:
                print("\n[驗證] 🐶 汪！正在呼叫 DogOCR 模型進行辨識...")
                # [修改] 使用 Dog_ocr 的 predict 方法
                # 注意：img_base64 變數內容雖然叫 base64，但經過上面的 b64decode 後，
                # 它實際上已經是二進制資料 (bytes)，所以直接傳進去即可。
                ocr_answer = ocr.predict(img_base64)
                print(f"[驗證] ✅ DogOCR 辨識結果: {ocr_answer}\n")

            except Exception as exc:
                print(f"OCR 辨識錯誤: {exc}")  # 建議印出來，方便除錯
                pass

    return ocr_answer


def tixcraft_auto_ocr(driver, config_dict, current_url, ocr, away_from_keyboard_enable, previous_answer, Captcha_Browser, ocr_captcha_image_source, domain_name):
    show_debug_message = True       # debug.
    show_debug_message = False      # online

    is_need_redo_ocr = False
    is_form_sumbited = False

    is_input_box_exist = False
    if not ocr is None:
        form_verifyCode = None
        try:
            form_verifyCode = driver.find_element(
                By.CSS_SELECTOR, '#TicketForm_verifyCode')
            is_input_box_exist = True
        except Exception as exc:
            pass
    else:
        print("ddddocr component is not able to use, you may running in arm environment.")

    if is_input_box_exist:
        if show_debug_message:
            print("away_from_keyboard_enable:", away_from_keyboard_enable)
            print("previous_answer:", previous_answer)
            print("ocr_captcha_image_source:", ocr_captcha_image_source)

        ocr_start_time = time.time()
        ocr_answer = tixcraft_get_ocr_answer(
            driver, ocr, ocr_captcha_image_source, Captcha_Browser, domain_name)
        ocr_done_time = time.time()
        ocr_elapsed_time = ocr_done_time - ocr_start_time
        if show_debug_message:
            print("ocr elapsed time:", "{:.3f}".format(ocr_elapsed_time))

        if ocr_answer is None:
            if away_from_keyboard_enable:
                # page is not ready, retry again.
                is_need_redo_ocr = True
                time.sleep(0.1)
            else:
                tixcraft_keyin_captcha_code(driver)
        else:
            ocr_answer = ocr_answer.strip()
            if show_debug_message:
                print("ocr_answer:", ocr_answer)

            if len(ocr_answer) == 4:
                if away_from_keyboard_enable:
                    # =========================================================
                    # 🚀 [光速送單啟動] 放棄慢速的鍵盤模擬，改用 API 直接砸向伺服器
                    # =========================================================
                    is_form_sumbited = api_fast_submit(
                        driver, current_url, ocr_answer, config_dict["ticket_number"])

                    if not is_form_sumbited:
                        # 如果 API 送單回傳 False，代表驗證碼錯誤或無票，需要重新辨識
                        is_need_redo_ocr = True
                        if previous_answer != ocr_answer:
                            previous_answer = ocr_answer
                            if show_debug_message:
                                print("API送單失敗，重新整理驗證碼...")
                            tixcraft_reload_captcha(driver, domain_name)
                else:
                    # 手動模式，依然維持原本慢慢打字
                    who_care_var, is_form_sumbited = tixcraft_keyin_captcha_code(
                        driver, answer=ocr_answer, auto_submit=away_from_keyboard_enable)
            else:
                if not away_from_keyboard_enable:
                    tixcraft_keyin_captcha_code(driver)
                else:
                    is_need_redo_ocr = True
                    if previous_answer != ocr_answer:
                        previous_answer = ocr_answer
                        if show_debug_message:
                            print("click captcha again.")

                        tixcraft_reload_captcha(driver, domain_name)

                        if ocr_captcha_image_source == CONST_OCR_CAPTCH_IMAGE_SOURCE_CANVAS:
                            time.sleep(0.1)
                        # Non_Browser solution 已經被你優化掉了，所以維持這樣即可
    else:
        print("input box not exist, quit ocr...")

    return is_need_redo_ocr, previous_answer, is_form_sumbited


def get_tixcraft_ticket_select_by_keyword(driver, config_dict, area_keyword_item):
    show_debug_message = True       # debug.
    show_debug_message = False      # online

    if config_dict["advanced"]["verbose"]:
        show_debug_message = True

    area_auto_select_mode = config_dict["area_auto_select"]["mode"]

    is_need_refresh = False
    matched_blocks = None

    area_list = None
    area_list_count = 0

    try:
        my_css_selector = "table#ticketPriceList > tbody > tr"
        area_list = driver.find_elements(By.CSS_SELECTOR, my_css_selector)
    except Exception as exc:
        # print("find area list a tag fail")
        pass

    if not area_list is None:
        area_list_count = len(area_list)
        if area_list_count == 0:
            print("area list is empty, do refresh!")
            is_need_refresh = True
    else:
        print("area list is None, do refresh!")
        is_need_refresh = True

    if area_list_count > 0:
        matched_blocks = []
        for row in area_list:
            row_text = ""
            row_html = ""
            try:
                # row_text = row.text
                row_html = row.get_attribute('innerHTML')
                row_text = util.remove_html_tags(row_html)
            except Exception as exc:
                if show_debug_message:
                    print(exc)
                # error, exit loop
                break

            if len(row_text) > 0:
                if util.reset_row_text_if_match_keyword_exclude(config_dict, row_text):
                    row_text = ""

            if len(row_text) > 0:
                # clean stop word.
                row_text = util.format_keyword_string(row_text)

                is_append_this_row = False

                if len(area_keyword_item) > 0:
                    # must match keyword.
                    is_append_this_row = True
                    area_keyword_array = area_keyword_item.split(' ')
                    for area_keyword in area_keyword_array:
                        area_keyword = util.format_keyword_string(area_keyword)
                        if not area_keyword in row_text:
                            is_append_this_row = False
                            break
                else:
                    # without keyword.
                    is_append_this_row = True

                if show_debug_message:
                    print("is_append_this_row:", is_append_this_row, row_text)

                if is_append_this_row:
                    matched_blocks.append(row)

                    if area_auto_select_mode == CONST_FROM_TOP_TO_BOTTOM:
                        # print("only need first item, break area list loop.")
                        break

        if len(matched_blocks) == 0:
            matched_blocks = None
            is_need_refresh = True

    return is_need_refresh, matched_blocks


def get_tixcraft_ticket_select(driver, config_dict):
    area_keyword = config_dict["area_auto_select"]["area_keyword"].strip()

    form_select = None
    matched_blocks = None
    if len(area_keyword) > 0:
        area_keyword_array = []
        try:
            area_keyword_array = json.loads("[" + area_keyword + "]")
        except Exception as exc:
            area_keyword_array = []
        for area_keyword_item in area_keyword_array:
            is_need_refresh, matched_blocks = get_tixcraft_ticket_select_by_keyword(
                driver, config_dict, area_keyword_item)
            if not is_need_refresh:
                break
            else:
                print("is_need_refresh for keyword:", area_keyword_item)
    else:
        # empty keyword, match all.
        is_need_refresh, matched_blocks = get_tixcraft_target_area(
            driver, config_dict, "")

    auto_select_mode = config_dict["area_auto_select"]["mode"]
    target_area = util.get_target_item_from_matched_list(
        matched_blocks, auto_select_mode)
    if not target_area is None:
        try:
            form_select = target_area.find_element(By.TAG_NAME, 'select')
        except Exception as exc:
            # print("find area list a tag fail")
            form_select = None
            pass

    return form_select


def tixcraft_assign_ticket_number(driver, config_dict):
    is_ticket_number_assigned = False

    # allow agree not enable to assign ticket number.
    form_select_list = None
    try:
        form_select_list = driver.find_elements(
            By.CSS_SELECTOR, '.mobile-select')
    except Exception as exc:
        print("find select fail")
        pass

    form_select = None
    form_select_count = 0
    if not form_select_list is None:
        form_select_count = len(form_select_list)
        if form_select_count >= 1:
            form_select = form_select_list[0]

    # multi select box
    if form_select_count > 1:
        if config_dict["area_auto_select"]["enable"]:
            # for tixcraft
            form_select_temp = get_tixcraft_ticket_select(driver, config_dict)
            if not form_select_temp is None:
                form_select = form_select_temp

    # for ticketmaster
    if form_select is None:
        try:
            form_select = driver.find_element(
                By.CSS_SELECTOR, 'td > select.form-select')
        except Exception as exc:
            print("find form-select fail")
            pass

    select_obj = None
    if not form_select is None:
        try:
            select_obj = Select(form_select)
        except Exception as exc:
            pass

    if not select_obj is None:
        row_text = None
        try:
            selected_option = select_obj.first_selected_option
            row_text = selected_option.text
        except Exception as exc:
            pass
        if not row_text is None:
            if len(row_text) > 0:
                if row_text != "0":
                    if row_text.isnumeric():
                        # ticket assign.
                        is_ticket_number_assigned = True

    return is_ticket_number_assigned, select_obj


def api_fast_submit(driver, current_url, ocr_verify_code, ticket_count=1):
    print(" [API 模式] 啟動光速送單...")
    import time  # 👈 補上這行，確保整個函式都能用 time
    import os    # 👈 補上這行，確保整個函式都能用 os

    # 1. 轉移 Selenium 的身份證明 (Cookies) 給 requests
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])

    # 2. 瞬間解析當前頁面 (不靠滑鼠，靠純文字掃描)
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, 'html.parser')

    try:
        # 抓取動態的 CSRF 防偽標記
        # 拓元通常藏在 <meta name="csrf-token" content="..."> 裡面
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        if csrf_meta:
            csrf_token = csrf_meta['content']
        else:
            # 如果 meta 找不到，找隱藏的 input
            csrf_token = soup.find('input', {'name': '_csrf'})['value']

        #  神級抓取：用正規表達式找出隱藏的 [05] 或 [02]
        # 尋找 name 屬性為 TicketForm[ticketPrice][數字] 的下拉選單或輸入框
        ticket_element = soup.find(lambda tag: tag.has_attr('name') and re.search(
            r"TicketForm\[ticketPrice\]\[\d+\]", tag['name']))

        if not ticket_element:
            print(" 找不到票種輸入框，可能是該區已售完 (無足夠數量)。")
            return False

        # 取得 "TicketForm[ticketPrice][05]"
        ticket_name = ticket_element['name']
        # 替換字串產生另一個必填欄位
        price_size_name = ticket_name.replace(
            'ticketPrice', 'priceSize')  # 變成 "TicketForm[priceSize][05]"

    except Exception as e:
        print(f" 解析頁面動態 Token 失敗: {e}")
        return False

    # 3. 組合終極 Payload (完全吻合你抓到的資料)
    payload = {
        '_csrf': csrf_token,
        ticket_name: str(ticket_count),
        price_size_name: str(ticket_count),
        'TicketForm[verifyCode]': ocr_verify_code,
        'TicketForm[agree]': '1'
    }

    # 4. 偽裝成真人瀏覽器
    headers = {
        'User-Agent': driver.execute_script("return navigator.userAgent;"),
        'Referer': current_url,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://tixcraft.com'
    }

    print(
        f" [API 模式] 送出參數: {ticket_name}={ticket_count}, 驗證碼={ocr_verify_code}")

    # 5. 光速發射 POST 請求 (禁止 requests 自動跳轉，我們要在程式裡攔截網址)
    try:
        response = session.post(current_url, data=payload,
                                headers=headers, allow_redirects=False, timeout=3)
    except Exception as e:
        print(f"網路請求失敗: {e}")
        return False

    # 6. 判斷勝負 (處理你抓到的 301 或 302 跳轉)
    if response.status_code in [301, 302]:
        redirect_url = response.headers.get('Location', '')

        # ================= [中繼計時：拿到票瞬間] =================
        global tixcraft_dict
        if 'tixcraft_dict' in globals() and tixcraft_dict.get("click_start_time") is not None:
            mid_elapsed = time.time() - tixcraft_dict["click_start_time"]
            print(f"⏱️ [中繼計時] (距起點耗時: {mid_elapsed:.3f} 秒)")
        # ==========================================================

        print(f"送單成功！伺服器回應: {response.status_code}，準備跳轉 -> {redirect_url}")

        # 將最新的 Cookie 同步回 Selenium
        for name, value in session.cookies.get_dict().items():
            driver.add_cookie({'name': name, 'value': value})

        # 讓畫面上的瀏覽器直接進入結帳頁面！
        if redirect_url.startswith('/'):
            driver.get(f"https://tixcraft.com{redirect_url}")
        else:
            driver.get(redirect_url)

        # 🌟 [新增] 成功買到票，跳出 002 迴圈，解除鎖定
        try:
            import os
            if os.path.exists("MAXBOT_002_LOCK.txt"):
                os.remove("MAXBOT_002_LOCK.txt")
        except Exception:
            pass

        return True

    elif response.status_code == 200:

        response_text = response.text
        if "E0002" in response_text or "無足夠數量" in response_text:
            print(f"[API 攔截] 發現 [#E0002] 或無足夠數量！啟動清票等待機制...")

            # ====================================================
            # 🌟 [修改] 建立「動態時間鎖」，設定基礎保護期為 60 秒
            # ====================================================
            try:
                import time
                with open("MAXBOT_002_LOCK.txt", "w") as f:
                    f.write(str(time.time() + 60))
            except Exception:
                pass
            # ====================================================

            # 計算 01, 15, 30, 45 秒邏輯
            try:
                from datetime import datetime
                import time

                target_seconds = [1, 15, 30, 45]
                now = datetime.now()
                current_s = now.second + now.microsecond / 1_000_000

                next_target = None
                for t in target_seconds:
                    if t > current_s:
                        next_target = t
                        break

                if next_target is None:
                    next_target = 60 + target_seconds[0]

                wait_seconds = next_target - current_s
                if wait_seconds < 0:
                    wait_seconds = 0

                print(
                    f"🕒 目前 {now.strftime('%H:%M:%S')}，等待 {wait_seconds:.2f} 秒，將於 {int(next_target % 60):02d} 秒時刷新...")
                time.sleep(wait_seconds)

            except Exception as e:
                print(f"時間計算錯誤: {e}")
                time.sleep(0.5)

            print("執行頁面刷新 (模擬物理按鍵 F5)！")
            try:
                import pyautogui
                pyautogui.press('f5')
            except Exception as e:
                print(f"pyautogui F5 失敗: {e}")

            time.sleep(0.5)

            try:
                new_alert = driver.switch_to.alert
                new_alert_text = str(new_alert.text)

                if "[#E0002]" in new_alert_text or "[#E0003]" in new_alert_text:
                    print("⚠️ F5 後視窗仍是 #E0002，為了安全，不執行點擊！(等下個週期)")
                else:
                    new_alert.accept()
                    print("✅ 已確認重新提交表單 (Resubmission Accepted)！")

            except NoAlertPresentException:
                print("✅ 已按下 F5 (無須確認重新提交)")
            except Exception:
                pass

            # ====================================================
            # 🌟 [修改] ！！！關鍵防護！！！
            # F5 之後不要刪除檔案，而是將鎖定時間更新為「未來 15 秒」
            # 完美掩護網頁重整時的空窗期，防止 GUI 趁虛而入暫停程式
            # ====================================================
            try:
                import time
                with open("MAXBOT_002_LOCK.txt", "w") as f:
                    f.write(str(time.time() + 15))
            except Exception:
                pass
            # ====================================================

            return False

        else:
            # 🌟 [新增] 單純驗證碼猜錯，沒有 E0002，安全解除鎖定
            try:
                import os
                if os.path.exists("MAXBOT_002_LOCK.txt"):
                    os.remove("MAXBOT_002_LOCK.txt")
            except Exception:
                pass

            print(" API 送單被拒絕 (無 E0002)。可能是驗證碼錯誤。準備重新辨識...")
            return False

    else:
        print(f" 未知狀態碼: {response.status_code}")
        return False


def tixcraft_ticket_main(driver, config_dict, ocr, Captcha_Browser, domain_name):

    has_captcha = False
    try:
        captcha_inputs = driver.find_elements(
            By.CSS_SELECTOR, '#TicketForm_verifyCode')
        if len(captcha_inputs) > 0:
            has_captcha = True
    except Exception as exc:
        pass

    # 如果連驗證碼都不用打，就直接按鈕送單 (冷門節目專屬)
    if not has_captcha:
        next_step_button_css = "button[type='submit'].btn"
        press_button(driver, By.CSS_SELECTOR, next_step_button_css)
    else:
        # 直接進入我們剛寫好的 OCR + API 核心迴圈 (熱門節目主力武器)
        tixcraft_ticket_main_ocr(
            driver, config_dict, ocr, Captcha_Browser, domain_name)


def tixcraft_ticket_main_ocr(driver, config_dict, ocr, Captcha_Browser, domain_name):
    away_from_keyboard_enable = config_dict["ocr_captcha"]["force_submit"]
    if not config_dict["ocr_captcha"]["enable"]:
        away_from_keyboard_enable = False
    ocr_captcha_image_source = config_dict["ocr_captcha"]["image_source"]

    if not config_dict["ocr_captcha"]["enable"]:
        tixcraft_keyin_captcha_code(driver)
    else:
        previous_answer = None
        last_url, is_quit_bot = get_current_url(driver)

        # 取得當前網址，準備餵給 API
        current_url = last_url

        for redo_ocr in range(19):
            # 注意這裡多傳了 config_dict 和 current_url 進去
            is_need_redo_ocr, previous_answer, is_form_sumbited = tixcraft_auto_ocr(
                driver, config_dict, current_url, ocr, away_from_keyboard_enable, previous_answer, Captcha_Browser, ocr_captcha_image_source, domain_name)

            if is_form_sumbited:
                # start next loop. (代表 API 成功，已經跳到結帳頁了)
                break

            if not away_from_keyboard_enable:
                break

            if not is_need_redo_ocr:
                break

            current_url, is_quit_bot = get_current_url(driver)
            if current_url != last_url:
                break


def check_checkbox(driver, by, query):
    show_debug_message = True       # debug.
    show_debug_message = False      # online

    agree_checkbox = None
    try:
        agree_checkbox = driver.find_element(by, query)
    except Exception as exc:
        if show_debug_message:
            print(exc)
        pass
    is_checkbox_checked = False
    if not agree_checkbox is None:
        is_checkbox_checked = force_check_checkbox(driver, agree_checkbox)
    return is_checkbox_checked


def force_check_checkbox(driver, agree_checkbox):
    is_finish_checkbox_click = False
    if not agree_checkbox is None:
        is_visible = False
        try:
            if agree_checkbox.is_enabled():
                is_visible = True
        except Exception as exc:
            pass

        if is_visible:
            is_checkbox_checked = False
            try:
                if agree_checkbox.is_selected():
                    is_checkbox_checked = True
            except Exception as exc:
                pass

            if not is_checkbox_checked:
                # print('send check to checkbox')
                try:
                    agree_checkbox.click()
                    is_finish_checkbox_click = True
                except Exception as exc:
                    try:
                        driver.execute_script(
                            "arguments[0].click();", agree_checkbox)
                        is_finish_checkbox_click = True
                    except Exception as exc:
                        pass
            else:
                is_finish_checkbox_click = True
    return is_finish_checkbox_click


def assign_ticket_number_by_select(driver, config_dict, by_method, selector_string):
    show_debug_message = True       # debug.
    show_debug_message = False      # online

    if config_dict["advanced"]["verbose"]:
        show_debug_message = True

    ticket_number = str(config_dict["ticket_number"])

    form_select = None
    try:
        form_select = driver.find_element(by_method, selector_string)
    except Exception as exc:
        if show_debug_message:
            print("find ticket_number select fail")
            print(exc)
        pass

    select_obj = None
    if not form_select is None:
        is_visible = False
        try:
            is_visible = form_select.is_enabled()
        except Exception as exc:
            pass
        if is_visible:
            try:
                select_obj = Select(form_select)
            except Exception as exc:
                pass

    is_ticket_number_assigned = False
    if not select_obj is None:
        row_text = None
        try:
            row_text = select_obj.first_selected_option.text
        except Exception as exc:
            pass
        if not row_text is None:
            if len(row_text) > 0:
                if row_text != "0":
                    # ticket assign.
                    is_ticket_number_assigned = True

        if not is_ticket_number_assigned:
            is_ticket_number_assigned = ticket_number_select_fill(
                driver, select_obj, ticket_number)
        else:
            if show_debug_message:
                print("ticket_number assigned by previous action.")

    return is_ticket_number_assigned


def assign_text(driver, by, query, val, overwrite=False, submit=False, overwrite_when=""):
    show_debug_message = True    # debug.
    show_debug_message = False   # online

    if val is None:
        val = ""

    is_visible = False

    if len(val) > 0:
        el_text = None
        try:
            el_text = driver.find_element(by, query)
        except Exception as exc:
            if show_debug_message:
                print(exc)
            pass

        if not el_text is None:
            try:
                if el_text.is_enabled() and el_text.is_displayed():
                    is_visible = True
            except Exception as exc:
                if show_debug_message:
                    print(exc)
                pass

    is_text_sent = False
    if is_visible:
        try:
            inputed_text = el_text.get_attribute('value')
            if not inputed_text is None:
                is_do_keyin = False
                if len(inputed_text) == 0:
                    is_do_keyin = True
                else:
                    if inputed_text == val:
                        is_text_sent = True
                    else:
                        if len(overwrite_when) > 0:
                            if overwrite_when == inputed_text:
                                overwrite = True
                        if overwrite:
                            is_do_keyin = True

                if is_do_keyin:
                    if len(inputed_text) > 0:
                        builder = ActionChains(driver)
                        builder.move_to_element(el_text)
                        builder.click(el_text)
                        if platform.system() == 'Darwin':
                            builder.key_down(Keys.COMMAND)
                        else:
                            builder.key_down(Keys.CONTROL)
                        builder.send_keys("a")
                        if platform.system() == 'Darwin':
                            builder.key_up(Keys.COMMAND)
                        else:
                            builder.key_up(Keys.CONTROL)
                        builder.send_keys(val)
                        if submit:
                            builder.send_keys(Keys.ENTER)
                        builder.perform()
                    else:
                        el_text.click()
                        el_text.send_keys(val)
                        if submit:
                            el_text.send_keys(Keys.ENTER)
                    is_text_sent = True
        except Exception as exc:
            if show_debug_message:
                print(exc)
            pass

    return is_text_sent


def facebook_login(driver, account, password):
    is_email_sent = assign_text(driver, By.CSS_SELECTOR, '#email', account)
    is_password_sent = False
    if is_email_sent:
        is_password_sent = assign_text(
            driver, By.CSS_SELECTOR, '#pass', password, submit=True)
    return is_password_sent


def play_sound_while_ordering(config_dict):
    app_root = util.get_app_root()
    captcha_sound_filename = os.path.join(
        app_root, config_dict["advanced"]["play_sound"]["filename"].strip())
    util.play_mp3_async(captcha_sound_filename)

# purpose: check alert poped.
# PS: current version not enable...


def check_pop_alert(driver):
    is_alert_popup = False

    # 這裡保留原本的設定，雖然目前是空字串
    default_close_alert_text = [""]

    try:
        # [修改] 移除 WebDriverWait，直接嘗試切換到 Alert
        # 如果當下沒有 Alert，Selenium 會立刻拋出 NoAlertPresentException，我們就直接跳到 except，耗時趨近於 0
        alert = driver.switch_to.alert

        # 程式執行到這裡代表「真的有彈窗」
        alert_text = str(alert.text)
        print(f"[check_pop_alert] 偵測到彈窗內容: {alert_text}")

        # [關鍵保護] 絕對不關閉清票相關的彈窗，回傳 False 讓 get_current_url 去處理 F5
        ignore_keywords = ["[#E0002]", "無足夠數量", "sold out", "售完", "流量管制"]
        for keyword in ignore_keywords:
            if keyword in alert_text:
                print(f"⚠️ 發現關鍵字 '{keyword}'，忽略此彈窗 (不關閉)，交給主程序處理。")
                return False

        # 如果是一般彈窗 (例如: 同意條款未勾選)，則執行關閉
        alert.accept()
        print("✅ 一般彈窗已自動關閉")
        is_alert_popup = True

    except NoAlertPresentException:
        # 這是最常發生的情況（代表沒有彈窗），直接略過，不浪費時間
        pass
    except Exception as exc:
        # print(f"check_pop_alert error: {exc}")
        pass

    return is_alert_popup


def list_all_cookies(driver):
    cookies_dict = {}
    if not driver is None:
        try:
            all_cookies = driver.get_cookies()
            for cookie in all_cookies:
                cookies_dict[cookie['name']] = cookie['value']
        except Exception as e:
            pass
    return cookies_dict
    # print(cookies_dict)


def set_non_browser_cookies(driver, url, Captcha_Browser):
    if not driver is None:
        domain_name = url.split('/')[2]
        # PS: need set cookies once, if user change domain.
        if not Captcha_Browser is None:
            try:
                Captcha_Browser.set_cookies(driver.get_cookies())
            except Exception as e:
                pass
            Captcha_Browser.set_domain(domain_name)


def tixcraft_main(driver, url, config_dict, ocr, Captcha_Browser):
    global tixcraft_dict
    if not 'tixcraft_dict' in globals():
        tixcraft_dict = {}
        tixcraft_dict["fail_list"] = []
        tixcraft_dict["fail_promo_list"] = []
        tixcraft_dict["start_time"] = None
        tixcraft_dict["done_time"] = None
        tixcraft_dict["elapsed_time"] = None
        tixcraft_dict["is_popup_checkout"] = False
        tixcraft_dict["area_retry_count"] = 0
        tixcraft_dict["played_sound_ticket"] = False
        tixcraft_dict["played_sound_order"] = False
        tixcraft_dict["last_sent_minute"] = None

    tixcraft_home_close_window(driver)

    home_url_list = ['https://tixcraft.com/', 'https://indievox.com/', 'https://www.indievox.com/', 'https://teamear.tixcraft.com/activity', 'https://ticketmaster.sg/', 'https://ticketmaster.com/'
                     ]
    for each_url in home_url_list:
        if each_url == url:
            if config_dict["ocr_captcha"]["enable"]:
                set_non_browser_cookies(driver, url, Captcha_Browser)
                pass
            break

    # for event soldout or abnormal, url should redirect to user's homepage.
    if 'https://tixcraft.com/' == url or 'https://tixcraft.com/activity' == url:
        if "/activity/game/" in config_dict["homepage"] or "/activity/detail/" in config_dict["homepage"]:
            try:
                driver.get(config_dict["homepage"])
            except Exception as e:
                pass

    if "/activity/detail/" in url:
        tixcraft_dict["start_time"] = time.time()
        is_redirected = tixcraft_redirect(driver, url)

    is_date_selected = False
    if "/activity/game/" in url:
        tixcraft_dict["start_time"] = time.time()
        if config_dict["date_auto_select"]["enable"]:
            domain_name = url.split('/')[2]
            is_date_selected = tixcraft_date_auto_select(
                driver, url, config_dict, domain_name)

    # choose area
    if '/ticket/area/' in url:
        domain_name = url.split('/')[2]
        if config_dict["area_auto_select"]["enable"]:
            if not 'ticketmaster' in domain_name:
                # for tixcraft
                tixcraft_area_auto_select(driver, url, config_dict)
                tixcraft_dict["area_retry_count"] += 1
                # print("count:", tixcraft_dict["area_retry_count"])
                if tixcraft_dict["area_retry_count"] >= (60 * 15):
                    # Cool-down
                    tixcraft_dict["area_retry_count"] = 0
                    time.sleep(5)

    else:
        tixcraft_dict["fail_promo_list"] = []
        tixcraft_dict["area_retry_count"] = 0

    if '/ticket/verify/' in url:
        tixcraft_dict["fail_list"] = tixcraft_verify(
            driver, config_dict, tixcraft_dict["fail_list"])
    else:
        tixcraft_dict["fail_list"] = []

    # main app, to select ticket number.
    if '/ticket/ticket/' in url:
        domain_name = url.split('/')[2]
        tixcraft_ticket_main(driver, config_dict, ocr,
                             Captcha_Browser, domain_name)
        tixcraft_dict["done_time"] = time.time()

        if config_dict["advanced"]["play_sound"]["ticket"]:
            if not tixcraft_dict["played_sound_ticket"]:
                play_sound_while_ordering(config_dict)
            tixcraft_dict["played_sound_ticket"] = True

        tixcraft_dict["last_sent_minute"] = util.optimized_email_sending(
            config_dict, "ticket", tixcraft_dict["last_sent_minute"], url)
    else:
        tixcraft_dict["played_sound_ticket"] = False

    if '/ticket/order' in url:
        tixcraft_dict["done_time"] = time.time()

    is_quit_bot = False

    if '/ticket/order' in url:
        tixcraft_dict["done_time"] = time.time()

    is_quit_bot = False

    # ▼▼▼▼▼ 請從這裡開始選取並取代 ▼▼▼▼▼
    if '/ticket/checkout' in url:

        # ================= [計算秒數終點] =================
        current_elapsed = 0.0
        # 只要有起點時間，就算出相差秒數
        if tixcraft_dict.get("click_start_time") is not None:
            current_elapsed = time.time() - tixcraft_dict["click_start_time"]
            print(f"\n🚀 [光速計時] 從點擊購票到進入結帳頁，總耗時: {current_elapsed:.3f} 秒！\n")

            # 把成績存起來給 TG 用，然後立刻清空起點 (算過一次就丟掉，避免洗畫面)
            tixcraft_dict["final_exact_time"] = current_elapsed
            tixcraft_dict["click_start_time"] = None
        else:
            # 拿剛剛存起來的最終成績
            current_elapsed = tixcraft_dict.get("final_exact_time", 0.0)
        # ===================================================

        if not tixcraft_dict.get("is_telegram_sent", False):
            try:
                from datetime import datetime
                msg_content = (
                    f"🎉 <b>搶票成功！(Checkout)</b>\n"
                    f"--------------------------------\n"
                    f"🔗 <a href='{url}'>點此前往結帳</a>\n"
                    f"⏱️ 光速耗時: {current_elapsed:.3f} 秒\n"
                    f"📅 時間: {datetime.now().strftime('%H:%M:%S')}"
                )

                send_telegram_message(msg_content, config_dict)
                tixcraft_dict["is_telegram_sent"] = True
            except Exception as e:
                print(f"⚠️ Telegram 通知準備失敗: {e}")

        if config_dict["advanced"]["headless"]:
            if not tixcraft_dict.get("is_popup_checkout", False):
                domain_name = url.split('/')[2]
                checkout_url = "https://%s/ticket/checkout" % (domain_name)
                print("搶票成功, 請前往該帳號訂單查看: %s" % (checkout_url))
                import webbrowser
                webbrowser.open_new(checkout_url)
                tixcraft_dict["is_popup_checkout"] = True
                is_quit_bot = True

        if config_dict["advanced"]["play_sound"]["order"]:
            if not tixcraft_dict.get("played_sound_order", False):
                play_sound_while_ordering(config_dict)
            tixcraft_dict["played_sound_order"] = True

        util.optimized_email_sending(config_dict, "order", None, url)

    else:
        # 當離開 checkout 頁面時，只要重置這三個開關就好
        tixcraft_dict["is_popup_checkout"] = False
        tixcraft_dict["played_sound_order"] = False
        tixcraft_dict["is_telegram_sent"] = False

    return is_quit_bot


def get_performance_log(driver, url_keyword):
    url_list = []
    try:
        logs = driver.get_log("performance")

        for log in logs:
            network_log = json.loads(log["message"])["message"]
            if ("Network.response" in network_log["method"]
                or "Network.request" in network_log["method"]
                    or "Network.webSocket" in network_log["method"]):
                if 'request' in network_log["params"]:
                    if 'url' in network_log["params"]["request"]:
                        if url_keyword in network_log["params"]["request"]["url"]:
                            url_list.append(
                                network_log["params"]["request"]["url"])
    except Exception as e:
        # raise e
        pass

    return url_list


def facebook_main(driver, config_dict):
    facebook_account = config_dict["advanced"]["facebook_account"].strip()
    facebook_password = config_dict["advanced"]["facebook_password_plaintext"].strip(
    )
    if facebook_password == "":
        facebook_password = util.decrypt_me(
            config_dict["advanced"]["facebook_password"])
    if len(facebook_account) > 4:
        facebook_login(driver, facebook_account, facebook_password)
        time.sleep(2)


# [修改] 增加 config_dict 參數
def get_current_url(driver, config_dict=None):
    # 定義暫停檔路徑
    CONST_MAXBOT_INT28_FILE = "MAXBOT_INT28_IDLE.txt"

    url = ""
    is_quit_bot = False

    try:
        url = driver.current_url
    except NoSuchWindowException:
        # ... (視窗關閉處理，保持原樣) ...
        window_handles_count = 0
        try:
            window_handles_count = len(driver.window_handles)
            if window_handles_count >= 1:
                driver.switch_to.window(driver.window_handles[0])
                driver.switch_to.default_content()
                time.sleep(0.2)
        except Exception:
            pass
        if window_handles_count == 0:
            is_quit_bot = True
            return url, is_quit_bot

    # [關鍵修改] 針對拓元 #E0002 清票機制的處理
    except UnexpectedAlertPresentException as exc1:
        try:
            # 1. 嘗試讀取彈窗文字
            alert_text = str(exc1.alert_text)
            if not alert_text:
                try:
                    alert_text = driver.switch_to.alert.text
                except:
                    pass

            print(f"======== [偵測到彈窗] ========")
            print(f"內容: {alert_text}")
            print(f"==============================")

            # [查哨點] 暫停檢查
            if os.path.exists(CONST_MAXBOT_INT28_FILE):
                print("⏸️ 程式已暫停，忽略彈窗處理")
                return url, is_quit_bot

            # 2. 判斷是否為目標錯誤代碼 [#E0002] 或 [無足夠數量]
            if "[#E0002]" in alert_text:
                print(f"🎯 命中 [#E0002] 清票模式！準備強制重整...")

                # ====================================================
                # [核心修改] 計算時間，只在 01, 15, 30, 45 秒執行刷新
                # ====================================================
                try:
                    target_seconds = [1, 15, 30, 45]
                    now = datetime.now()
                    current_s = now.second + now.microsecond / 1_000_000

                    # 尋找下一個最近的目標秒數
                    next_target = None
                    for t in target_seconds:
                        if t > current_s:
                            next_target = t
                            break

                    # 如果當前秒數已經超過 45 (例如 50秒)，下一個目標就是下一分鐘的 1 秒 (即 61秒)
                    if next_target is None:
                        next_target = 60 + target_seconds[0]

                    wait_seconds = next_target - current_s

                    # 確保等待時間非負值
                    if wait_seconds < 0:
                        wait_seconds = 0

                    print(
                        f"🕒 目前 {now.strftime('%H:%M:%S')}，等待 {wait_seconds:.2f} 秒，將於 {int(next_target % 60):02d} 秒時刷新...")
                    time.sleep(wait_seconds)

                except Exception as e:
                    print(f"時間計算錯誤: {e}")
                    time.sleep(0.1)  # 發生錯誤時的保底等待

                # ====================================================

                # 3. 使用 pyautogui 模擬物理按鍵 F5
                try:
                    import pyautogui
                    pyautogui.press('f5')

                    # 按下 F5 後，等待瀏覽器反應 (原本的 #E0002 應該會消失，跳出確認重送)
                    time.sleep(0.2)

                    # 4. [雙重保險檢查] 檢查 F5 後的視窗狀態
                    try:
                        new_alert = driver.switch_to.alert
                        new_alert_text = str(new_alert.text)

                        # 嚴格檢查：如果視窗內容依然是 #E0002 (代表 F5 沒成功，或者網頁又跳了一次錯誤)
                        if "[#E0002]" in new_alert_text:
                            print("⚠️ F5 後視窗仍是 #E0002，為了安全，不執行點擊！(將於下個時間點重試)")
                            # 這裡不做任何動作，函式結束，回到 main 迴圈，等待下一次 15秒 的週期
                        else:
                            # 內容變了 (通常是「確認重新提交表單」)，這時候才按下確定
                            new_alert.accept()
                            print("✅ 已確認重新提交表單 (Resubmission Accepted)")

                    except NoAlertPresentException:
                        print("✅ 已按下 F5 (無須確認重新提交)")
                        pass
                    except Exception:
                        pass

                except Exception as e:
                    print(f"F5 刷新過程發生錯誤: {e}")
                    pass

            else:
                # 情況 B：其他的彈窗 (例如驗證碼錯誤、未勾選同意條款)
                try:
                    print("非目標彈窗，執行關閉...")
                    driver.switch_to.alert.accept()
                except:
                    pass

        except Exception as e:
            pass

    except Exception as exc:
        pass

    return url, is_quit_bot


def reset_webdriver(driver, config_dict, url):
    new_driver = None
    try:
        cookies = driver.get_cookies()
        driver.close()
        config_dict["homepage"] = url
        new_driver = get_driver_by_config(config_dict)
        for cookie in cookies:
            new_driver.add_cookie(cookie)
        new_driver.get(url)
        driver = new_driver
    except Exception as e:
        pass
    return new_driver


def resize_window(driver, config_dict):
    if len(config_dict["advanced"]["window_size"]) > 0:
        if "," in config_dict["advanced"]["window_size"]:
            size_array = config_dict["advanced"]["window_size"].split(",")
            position_left = 0
            if len(size_array) >= 3:
                position_left = int(size_array[0]) * int(size_array[2])
            driver.set_window_size(int(size_array[0]), int(size_array[1]))
            driver.set_window_position(position_left, 30)


def check_refresh_datetime_occur(driver, target_time):
    is_refresh_datetime_sent = False

    system_clock_data = datetime.now()
    current_time = system_clock_data.strftime('%H:%M:%S')
    if target_time == current_time:
        try:
            driver.refresh()
            is_refresh_datetime_sent = True
            print("send refresh at time:", current_time)
        except Exception as exc:
            pass

    return is_refresh_datetime_sent


def sendkey_to_browser(driver, config_dict, url):
    tmp_filepath = ""
    if "token" in config_dict:
        app_root = util.get_app_root()
        tmp_file = config_dict["token"] + "_sendkey.tmp"
        tmp_filepath = os.path.join(app_root, tmp_file)

    if os.path.exists(tmp_filepath):
        sendkey_dict = None
        try:
            with open(tmp_filepath) as json_data:
                sendkey_dict = json.load(json_data)
                print(sendkey_dict)
        except Exception as e:
            print("error on open file")
            print(e)
            pass

        if sendkey_dict:
            all_command_done = sendkey_to_browser_exist(
                driver, sendkey_dict, url)
            # must all command success to delete tmp file.
            if all_command_done:
                try:
                    os.unlink(tmp_filepath)
                    # print("remove file:", tmp_filepath)
                except Exception as e:
                    pass


def sendkey_to_browser_exist(driver, sendkey_dict, url):
    all_command_done = True
    if "command" in sendkey_dict:
        for cmd_dict in sendkey_dict["command"]:
            # print("cmd_dict", cmd_dict)
            matched_location = True
            if "location" in cmd_dict:
                if cmd_dict["location"] != url:
                    matched_location = False

            if matched_location:
                if cmd_dict["type"] == "sendkey":
                    print("sendkey")
                    target_text = cmd_dict["text"]
                    try:
                        form_input_1 = driver.find_element(
                            By.CSS_SELECTOR, cmd_dict["selector"])
                        inputed_value_1 = form_input_1.get_attribute('value')
                        if not inputed_value_1 == target_text:
                            form_input_1.clear()
                            form_input_1.click()
                            form_input_1.send_keys(target_text)
                    except Exception as exc:
                        all_command_done = False
                        print("error on sendkey")
                        print(exc)
                        pass

                if cmd_dict["type"] == "click":
                    print("click")
                    try:
                        form_input_1 = driver.find_element(
                            By.CSS_SELECTOR, cmd_dict["selector"])
                        form_input_1.click()
                    except Exception as exc:
                        all_command_done = False
                        print("error on click")
                        print(exc)
                        pass
            time.sleep(0.05)
    return all_command_done


def main(args):
    config_dict = get_config_dict(args)
    config_dict["token"] = util.get_token()

    driver = None
    if not config_dict is None:
        driver = get_driver_by_config(config_dict)
        if not driver is None:
            if not config_dict["advanced"]["headless"]:
                resize_window(driver, config_dict)
        else:
            print("無法使用web driver，程式無法繼續工作")
            sys.exit()
    else:
        print("Load config error!")

    url = ""
    last_url = ""

    ocr = None
    Captcha_Browser = None
    try:
        # [修改] 雖然設定檔還是叫 "ocr_captcha"，但我們現在改用 Dog_ocr
        if config_dict["ocr_captcha"]["enable"]:

            # [修改] 這裡改用 Dog_ocr 初始化
            # print("Loading Dog OCR model...")

            ocr = Dog_ocr.Ocr()

            # 原本的 ddddocr 相關參數 (show_ad, beta) 在這裡用不到了，直接略過

            Captcha_Browser = NonBrowser()
            if len(config_dict["advanced"]["tixcraft_sid"]) > 1:
                set_non_browser_cookies(
                    driver, config_dict["homepage"], Captcha_Browser)
    except Exception as exc:
        print(f"OCR 初始化失敗: {exc}")
        pass

    maxbot_last_reset_time = time.time()
    is_quit_bot = False
    is_refresh_datetime_sent = False

    while True:
        time.sleep(0.05)

        # pass if driver not loaded.
        if driver is None:
            print("web driver not accessible!")
            break

        if not is_quit_bot:
            # [修改] 傳入 config_dict 以讀取刷新間隔
            url, is_quit_bot = get_current_url(driver, config_dict)
            # print("url:", url)

        if is_quit_bot:
            try:
                driver.quit()
                driver = None
            except Exception as e:
                pass
            break

        if url is None:
            continue
        else:
            if len(url) == 0:
                continue

        if not is_refresh_datetime_sent:
            is_refresh_datetime_sent = check_refresh_datetime_occur(
                driver, config_dict["refresh_datetime"])

        is_maxbot_paused = False
        if os.path.exists(CONST_MAXBOT_INT28_FILE):
            is_maxbot_paused = True
        sync_status_to_extension(not is_maxbot_paused)

        if len(url) > 0:
            if url != last_url:
                print(url)
                write_last_url_to_file(url)
                if is_maxbot_paused:
                    print("MAXBOT Paused.")
            last_url = url

        # ================= [新增] 真正的暫停攔截點 =================
        if is_maxbot_paused:
            # 如果處於暫停狀態，直接跳回迴圈開頭，不執行下方的搶票邏輯！
            continue
        # ========================================================

        sendkey_to_browser(driver, config_dict, url)

        # default is 0, not reset.
        if config_dict["advanced"]["reset_browser_interval"] > 0:
            maxbot_running_time = time.time() - maxbot_last_reset_time
            if maxbot_running_time > config_dict["advanced"]["reset_browser_interval"]:
                driver = reset_webdriver(driver, config_dict, url)
                maxbot_last_reset_time = time.time()

        tixcraft_family = False
        if 'tixcraft.com' in url:
            tixcraft_family = True

        if tixcraft_family:
            is_quit_bot = tixcraft_main(
                driver, url, config_dict, ocr, Captcha_Browser)

        # for facebook signin
        facebook_login_url = 'https://www.facebook.com/login.php?'
        if url[:len(facebook_login_url)] == facebook_login_url:
            facebook_main(driver, config_dict)


def cli():
    parser = argparse.ArgumentParser(
        description="MaxBot Argument Parser")

    parser.add_argument("--input",
                        help="config file path",
                        type=str)

    parser.add_argument("--homepage",
                        help="overwrite homepage setting",
                        type=str)

    parser.add_argument("--ticket_number",
                        help="overwrite ticket_number setting",
                        type=int)

    parser.add_argument("--tixcraft_sid",
                        help="overwrite tixcraft sid field",
                        type=str)

    parser.add_argument("--kktix_account",
                        help="overwrite kktix_account field",
                        type=str)

    parser.add_argument("--kktix_password",
                        help="overwrite kktix_password field",
                        type=str)

    parser.add_argument("--ibonqware",
                        help="overwrite ibonqware field",
                        type=str)

    # default="False",
    parser.add_argument("--headless",
                        help="headless mode",
                        type=str)

    parser.add_argument("--browser",
                        help="overwrite browser setting",
                        default='',
                        choices=['chrome', 'firefox',
                                 'edge', 'safari', 'brave'],
                        type=str)

    parser.add_argument("--window_size",
                        help="Window size",
                        type=str)

    parser.add_argument("--proxy_server",
                        help="overwrite proxy server, format: ip:port",
                        type=str)

    args = parser.parse_args()
    main(args)


def test_captcha_model():
    # for test kktix answer.
    captcha_text_div_text = "請輸入括弧內數字( 27８９41 )"
    captcha_text_div_text = "請將括弧內文字轉換為阿拉伯數字(一二三四五六)"
    answer_list = util.get_answer_list_from_question_string(
        None, captcha_text_div_text)
    print("answer_list:", answer_list)

    ocr = ddddocr.DdddOcr(show_ad=False, beta=True)
    image_file = 'captcha-xxxx.png'
    if os.path.exists(image_file):
        with open(image_file, 'rb') as f:
            image_bytes = f.read()
        res = ocr.classification(image_bytes)
        print(res)


if __name__ == "__main__":
    debug_captcha_model_flag = False    # online mode
    # for debug purpose.
    # debug_captcha_model_flag = True

    # jieba.initialize()

    if not debug_captcha_model_flag:
        cli()
    else:
        test_captcha_model()
