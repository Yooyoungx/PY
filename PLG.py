#!/usr/bin/env python3
# encoding=utf-8
import traceback
import argparse
import base64
import json
import logging
import os
import pathlib
import platform
import random
import shutil
import ssl
import subprocess
import sys
import threading
import time
import urllib.parse
import warnings
import webbrowser
from datetime import datetime
from typing import Optional
import asyncio
import time
import requests

import nodriver as uc
from nodriver import cdp
from nodriver.core.config import Config
from urllib3.exceptions import InsecureRequestWarning

import util
from NonBrowser import NonBrowser

try:
    import ddddocr
except Exception as exc:
    print(exc)
    pass
CONST_APP_VERSION = "1"

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
    "*ticketmaster.sg/js/adblock.js*",
    "*tixcraft.com/js/analytics.js*",
    "*tixcraft.com/js/common.js*",
    "*tixcraft.com/js/custom.js*",
    "*treasuredata.com/*",
    "*www.youtube.com/youtubei/v1/player/heartbeat*",
]

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
CONST_SELECT_ORDER_DEFAULT = CONST_FROM_TOP_TO_BOTTOM

CONT_STRING_1_SEATS_REMAINING = ['@1 seat(s) remaining', '剩餘 1@', '@1 席残り']

CONST_OCR_CAPTCH_IMAGE_SOURCE_NON_BROWSER = "NonBrowser"
CONST_OCR_CAPTCH_IMAGE_SOURCE_CANVAS = "canvas"

CONST_WEBDRIVER_TYPE_NODRIVER = "nodriver"
CONST_CHROME_FAMILY = ["chrome", "edge", "brave"]

warnings.simplefilter('ignore', InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
logging.basicConfig()
logger = logging.getLogger('logger')

# ==========================================
# [設定區] 檔案路徑與常數
# ==========================================
CONST_MAXBOT_CONFIG_FILE = "settings.json"
warnings.simplefilter('ignore', InsecureRequestWarning)

# ==========================================
# [核心功能 1] 讀取設定檔
# ==========================================


def get_config_dict(args):
    app_root = util.get_app_root()

    # 1. 預設使用原本的常數 (例如 settings.json)
    target_filename = CONST_MAXBOT_CONFIG_FILE

    # 2. 如果 GUI 有傳入指定的設定檔名 (例如 settings-A.json)，就把它替換掉
    if hasattr(args, 'input') and args.input and len(args.input) > 0:
        target_filename = args.input

    # 3. 組合出完整的「絕對路徑」，確保 .exe 執行時絕對找得到！
    config_filepath = os.path.join(app_root, target_filename)

    config_dict = None
    if os.path.isfile(config_filepath):
        with open(config_filepath, 'r', encoding='utf-8') as json_data:
            config_dict = json.load(json_data)

            # 將 UI 參數覆蓋 (這段維持你原本的邏輯不變)
            arg_map = {
                "headless": ["advanced", "headless"],
                "homepage": ["homepage"],
                "ticket_number": ["ticket_number"],
                "browser": ["browser"],
                "proxy_server": ["advanced", "proxy_server_port"],
                "window_size": ["advanced", "window_size"]
            }
            for arg_name, json_path in arg_map.items():
                if hasattr(args, arg_name):
                    val = getattr(args, arg_name)
                    if val and str(val).strip():
                        d = config_dict
                        for key in json_path[:-1]:
                            d = d[key]
                        d[json_path[-1]] = val

            config_dict["token"] = util.get_token()

            # ==========================================
            # 🔥 神級修復：把目前的設定檔路徑，當作一個變數塞進字典裡！
            # 這樣 FubonBot 裡面的 config.get("config_filepath") 才抓得到東西
            # ==========================================
            config_dict["config_filepath"] = config_filepath

    else:
        # 加上一個防呆機制：如果找不到設定檔，印出錯誤訊息方便除錯
        print(f"找不到設定檔: {config_filepath}")

    return config_dict


class FubonBot:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""
        #  註冊彈窗監聽器 (只要有彈窗就會呼叫 self._handle_dialog)
        # self.tab.add_handler(
        #    cdp.page.JavascriptDialogOpening, self._handle_dialog)
        # 狀態變數
        self.is_date_selected = False
        self.is_area_selected = False
        self.is_seat_selected = False
        # [新增] Telegram 通知相關狀態
        self.is_telegram_sent = False
        self.bot_start_time = time.time()  # 記錄機器人啟動的當下時間

        # [新增] 初始化 ddddocr 引擎，關閉廣告訊息保持 Log 乾淨
        print(">>> [系統] 正在載入 ddddocr 辨識模型...")
        self.ocr = ddddocr.DdddOcr(show_ad=False)

        # 音效狀態
        self.played_sound_ticket = False
        self.ticket_sound_tag = {"last_key": None}

        # 暫停控制檔案 (與 Settings_old 連動的關鍵)
        self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # 讀取設定檔
        self.date_auto_select = config.get("date_auto_select", {
            "enable": True, "mode": "from top to bottom", "date_keyword": ""
        })
        self.area_auto_select = config.get("area_auto_select", {
            "enable": True, "mode": "from top to bottom", "area_keyword": ""
        })

        # 讀取進階暫停/接續設定
        advanced = config.get("advanced", {})
        self.keyword_pause = advanced.get("keyword_pause", "")
        self.keyword_resume = advanced.get("keyword_resume", "")
        # 確保延遲時間是數字，預設為 0
        try:
            self.keyword_pause_sec = float(
                advanced.get("keyword_pause_sec", 0))
        except:
            self.keyword_pause_sec = 0
        try:
            self.keyword_resume_sec = float(
                advanced.get("keyword_resume_sec", 0))
        except:
            self.keyword_resume_sec = 0

    async def run(self):
        print(f"機器人啟動！(目標張數: {self.ticket_number})")

        d_mode = self.date_auto_select.get("mode", "預設")
        a_mode = self.area_auto_select.get("mode", "預設")
        print(f"模式設定 -> 日期: {d_mode} | 區域: {a_mode}")

        # 顯示關鍵字監控狀態
        if self.keyword_pause:
            print(f"監控暫停關鍵字: {self.keyword_pause}")
        if self.keyword_resume:
            print(f"監控接續關鍵字: {self.keyword_resume}")

        print("等待網頁載入中...")

        try:
            if self.config.get('homepage'):
                await self.tab.get(self.config['homepage'])
        except Exception as e:
            print(f"開啟網頁錯誤: {e}")

        while True:
            try:
                # ---------------------------------------------------
                # 0. 設定檔熱重載 (Hot Reload)
                # ---------------------------------------------------
                await self.reload_config_if_changed()

                # ---------------------------------------------------
                # 1. 執行關鍵字檢查 (自動暫停/繼續)
                # ---------------------------------------------------
                await self.check_flow_keywords()

                # ---------------------------------------------------
                # 2. 檢查是否處於暫停狀態
                # ---------------------------------------------------
                if os.path.exists(self.PAUSE_FILE):
                    # print(f">>> 機器人暫停中 (檢測到 {self.PAUSE_FILE})...")
                    await asyncio.sleep(0.5)
                    continue  # 直接跳過後面所有搶票邏輯

                # ---------------------------------------------------
                # 3. 正常的搶票流程
                # ---------------------------------------------------
                current_url = await self.tab.evaluate("window.location.href")

                # 檢測頁面切換
                if current_url and current_url != self.last_url:
                    print(f"偵測到頁面切換: {current_url}")

                    # [狀態重置] 離開日期或詳情頁時，重置日期選擇狀態
                    if "GameInfo" not in current_url and "ActivityInfo/Details" not in current_url:
                        self.is_date_selected = False

                    # [區域頁面重入檢測] 如果卡在區域選擇頁，嘗試刷新
                    if '/UTK02/UTK' in current_url.upper() and 'PRODUCT_ID=' in current_url.upper():
                        if self.is_area_selected:
                            print(">>> [重入檢測] 再次回到區域選擇頁面，重置狀態並刷新...")
                            self.is_area_selected = False
                            try:
                                await self.tab.reload()
                                await asyncio.sleep(0.5)
                            except:
                                pass

                    # 更新最後網址
                    self.last_url = current_url

                # 分派具體動作 (如選日期、選位)
                if current_url:
                    await self.dispatch_action(current_url)

            except Exception as e:
                # print(f"Main loop exception: {e}")
                pass

            await asyncio.sleep(0.5)

    async def check_flow_keywords(self):
        """
        [新增功能] 檢查頁面關鍵字以自動暫停或繼續
        邏輯完全參考 IBON_AAA
        """
        # 如果沒有設定關鍵字，就直接離開，節省資源
        if not self.keyword_pause and not self.keyword_resume:
            return

        try:
            # 獲取頁面文字 (包含 body 內的所有可見文字)
            body_text = await self.tab.evaluate("document.body.innerText")
            if not body_text:
                return

            # A. 檢查是否需要「自動繼續」 (當機器人處於暫停狀態時特別有用)
            if self.keyword_resume and os.path.exists(self.PAUSE_FILE):
                if self.keyword_resume in body_text:
                    print(f">>> 發現接續關鍵字: '{self.keyword_resume}'")
                    if self.keyword_resume_sec > 0:
                        print(f"    等待 {self.keyword_resume_sec} 秒後接續...")
                        await asyncio.sleep(self.keyword_resume_sec)

                    try:
                        os.remove(self.PAUSE_FILE)  # 刪除暫停檔 -> 恢復運作
                        print(">>> 已刪除暫停檔，機器人恢復運作！")
                    except Exception as e:
                        print(f"刪除暫停檔失敗: {e}")

            # B. 檢查是否需要「自動暫停」 (當機器人正在運作時)
            if self.keyword_pause and not os.path.exists(self.PAUSE_FILE):
                if self.keyword_pause in body_text:
                    print(f">>> 發現暫停關鍵字: '{self.keyword_pause}'")
                    if self.keyword_pause_sec > 0:
                        print(f"    等待 {self.keyword_pause_sec} 秒後暫停...")
                        await asyncio.sleep(self.keyword_pause_sec)

                    try:
                        with open(self.PAUSE_FILE, "w") as f:
                            f.write("paused by keyword")  # 建立暫停檔 -> 停止運作
                        print(">>> 已建立暫停檔，機器人進入暫停模式！")
                    except Exception as e:
                        print(f"建立暫停檔失敗: {e}")

        except Exception:
            pass

    async def dispatch_action(self, url):
        """任務分發中心 (專為 UTK 售票系統與富邦勇士修改)"""
        upper_url = url.upper()

        # ==========================================
        # [新增] 狀態重置區：當回到首頁時，完全重置所有鎖定狀態
        # ==========================================
        if 'UTK0101_' in upper_url:
            self.is_date_selected = False
            self.is_area_selected = False
            self.is_seat_selected = False
            self.is_telegram_sent = False
            return

        # ==========================================
        # 0. 購票成功 (UTK0206_ 結帳/購物車頁面)
        # ==========================================
        elif 'UTK0206_' in upper_url:
            if getattr(self, 'is_seat_selected', False):
                print(">>> [系統] 🎉 恭喜！成功進入購物車/結帳頁面！自動化流程已完成！")
                self.is_seat_selected = False  # 防呆重置

            # 觸發 Telegram 通知
            if not getattr(self, 'is_telegram_sent', False):
                try:
                    import time
                    from datetime import datetime

                    # 計算總耗時
                    current_elapsed = time.time() - getattr(self, 'bot_start_time', time.time())

                    msg_content = (
                        f"🎉 <b>富邦勇士 搶票成功！</b>\n"
                        f"--------------------------------\n"
                        f"🔗 <a href='{url}'>點此前往結帳</a>\n"
                        f"🎫 目標張數: {self.ticket_number} 張\n"
                        f"⏱️ 總耗時: {current_elapsed:.3f} 秒\n"
                        f"📅 時間: {datetime.now().strftime('%H:%M:%S')}\n"
                        f"⚠️ <b>請盡速在 10 分鐘內完成付款！</b>"
                    )

                    await self.send_telegram_message(msg_content)
                    self.is_telegram_sent = True

                except Exception as e:
                    print(f"⚠️ Telegram 通知準備失敗: {e}")

            return  # 已經在結帳頁面了，停止往下執行

        # ==========================================
        # 1. 第一階段：日期/場次選擇 (UTK0201_)
        # ==========================================
        elif 'UTK0201_' in upper_url:
            # 【關鍵修復】只要進入日期頁面，強制重置後續所有的狀態鎖！
            # 確保不管是第一輪還是第 N 輪，區域和座位都能正常觸發
            self.is_area_selected = False
            self.is_seat_selected = False
            self.is_telegram_sent = False

            if not self.is_date_selected:
                await self.select_date()

        # ==========================================
        # 2. 第二階段：區域選擇 (UTK0204_ 且沒有座位表時)
        # ==========================================
        elif 'UTK0204_' in upper_url and not self.is_area_selected:
            # 進入區域前，重置座位選擇標記
            self.is_seat_selected = False
            if self.area_auto_select.get("enable", True):
                await self.select_area_legacy()

        # ==========================================
        # 3. 第三階段：座位選擇 -> OCR -> 下一步 -> 錯誤重試
        # ==========================================
        elif 'UTK0205_' in upper_url or ('UTK0204_' in upper_url and getattr(self, 'is_area_selected', False)):

            # 【環節 A：錯誤重試】檢查是否有因為驗證碼錯誤跳出的 jQuery 彈窗
            is_error_dialog_closed = await self.check_and_close_jquery_dialog()

            if is_error_dialog_closed:
                print(">>> [系統] 發現驗證碼錯誤彈窗！準備重新辨識...")
                import asyncio
                await asyncio.sleep(0.5)  # 等待新圖片載入

                # 重新跑 OCR，如果成功填入，再次點擊下一步
                if await self.process_captcha():
                    await self.click_next()

            else:
                # 【環節 B：正常流程】如果還沒選過位子，才執行選位
                if not getattr(self, 'is_seat_selected', False):

                    # 1. 執行座位選擇
                    seat_success = await self.select_ticket_quantity_legacy()

                    if seat_success:
                        import asyncio
                        # 2. 選位成功後，稍微等待驗證碼圖片渲染
                        await asyncio.sleep(0.5)

                        # 3. 呼叫 ddddocr 執行自動辨識並填入
                        ocr_success = await self.process_captcha()

                        # 4. 如果 OCR 辨識成功，立刻點擊加入購物車
                        if ocr_success:
                            await self.click_next()

    async def select_date(self):
        """[第一階段] 場次/日期選擇 (簡化極速版：直接點擊第一個可用按鈕)"""
        if not self.date_auto_select.get("enable", True):
            return

        # 建構極簡版 JavaScript 腳本，尋找並點擊第一個可用的購買按鈕
        js_script = """
        (function() {
            try {
                // 直接尋找畫面上的 #buy_btn (或是任何可點擊的 button)
                const btn = document.querySelector('#buy_btn') || document.querySelector('button');
                if (btn && !btn.disabled) {
                    btn.click();
                    return 1; // 成功點擊，回傳 1 給 Python
                }
                return 2; // 找不到或不可點，回傳 2 觸發重整
            } catch (e) {
                return -1; // 發生錯誤
            }
        })();
        """

        try:
            # 執行 JS 並取得結果
            result = await self.tab.evaluate(js_script)

            if result == 1:
                print(">>> [場次/日期] 👉 成功抓到購買按鈕，執行點擊！")
                self.is_date_selected = True

            elif result == 2:
                # 沒票或還沒開賣時的處理邏輯 (自動隨機延遲後重整)
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))

                if base_wait > 0:
                    print(">>> [場次/日期] 尚未開賣或找不到按鈕，準備刷新...")
                    try:
                        # 使用隨機時間函數防封鎖 (確保不會 0 秒狂刷)
                        random_wait = self.get_random_reload_time(base_wait)
                        await self.tab.reload()
                        print(
                            f"    -> 刷新後隨機等待: {random_wait:.2f} 秒 (基準: {base_wait}s)")
                        await asyncio.sleep(random_wait)
                    except:
                        pass

            elif result == -1:
                print(">>> [DEBUG] 日期選擇 JS 執行發生內部錯誤")

        except Exception as e:
            pass

    async def select_area_legacy(self):
        """[第二階段] 區域選擇 (整合前端 JS 暴力選取，保留外部設定檔動態讀取)"""
        if not self.area_auto_select.get("enable", True):
            return

        # ==========================================
        # 1. 讀取並解析外部設定檔
        # ==========================================
        auto_select_mode = self.area_auto_select.get(
            "mode", "from top to bottom")
        raw_keyword = self.area_auto_select.get("area_keyword", "").strip()

        keyword_list = []
        if len(raw_keyword) > 0:
            try:
                if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                    keyword_list = json.loads(raw_keyword)
                else:
                    keyword_list = json.loads("[" + raw_keyword + "]")
            except:
                keyword_list = [raw_keyword]
        else:
            keyword_list = [""]

        # 將 Python 的變數轉成 JavaScript 可以讀取的格式
        js_keywords = json.dumps(keyword_list, ensure_ascii=False)
        js_mode = f"'{auto_select_mode}'"

        # ==========================================
        # 2. 構建超快速 JavaScript 區域掃描腳本
        # ==========================================
        js_script = f"""
        (function() {{
            try {{
                // 接收來自 Python 的設定參數
                const keywords = {js_keywords};
                const mode = {js_mode};

                let allRows = Array.from(document.querySelectorAll('tr.saleTr'));
                let candidates = [];

                if (allRows.length > 0) {{
                    for (let row of allRows) {{
                        const rowContent = row.innerText.toUpperCase();

                        // [防呆過濾] 檢查剩餘張數，若沒票就直接跳過
                        const seatElement = row.querySelector('#SEAT');
                        const seatCount = seatElement ? parseInt(seatElement.innerText) : 0;
                        if (seatCount <= 0) continue;

                        // [關鍵字比對] 支援空白分隔的多重條件，例如 "VIP A排"
                        let isMatch = false;
                        if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                            isMatch = true; // 沒設關鍵字，全部皆可
                        }} else {{
                            for (let k of keywords) {{
                                let target_kws = k.trim().split(" ").filter(w => w.length > 0);
                                let currentGroupMatch = true;
                                for (let w of target_kws) {{
                                    if (!rowContent.includes(w.toUpperCase())) {{
                                        currentGroupMatch = false;
                                        break;
                                    }}
                                }}
                                if (currentGroupMatch) {{
                                    isMatch = true;
                                    break;
                                }}
                            }}
                        }}

                        // 如果關鍵字符合且有票，加入候選名單
                        if (isMatch) {{
                            candidates.push(row);
                        }}
                    }}
                }}

                // 找不到符合且有票的區域，回傳 2 讓 Python 去重整網頁
                if (candidates.length === 0) return 2;

                // 根據外部設定檔的模式進行排序
                if (mode === "from bottom to top") {{
                    candidates.reverse();
                }} else if (mode === "random") {{
                    for (let i = candidates.length - 1; i > 0; i--) {{
                        const j = Math.floor(Math.random() * (i + 1));
                        [candidates[i], candidates[j]] = [
                            candidates[j], candidates[i]];
                    }}
                }}

                // 執行點擊 (點擊排序後的第一個符合區域)
                candidates[0].click();
                return 1; // 成功點擊

            }} catch(e) {{
                return -1; // 發生例外錯誤
            }}
        }})();
        """

        # ==========================================
        # 3. 執行腳本與狀態處理
        # ==========================================
        try:
            result = await self.tab.evaluate(js_script)

            if result == 1:
                print(f">>> [區域] 👉 成功匹配並點擊區域！")
                await asyncio.sleep(0.2)  # 給網頁一點反應時間
                self.is_area_selected = True

            elif result == 2:
                # 找不到票區或全部售完，觸發 Python 自動刷新
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))

                # 給予極短保底時間，避免 0 秒狂刷被伺服器封鎖
                if base_wait <= 0:
                    base_wait = 0.2

                print(">>> [區域] 找不到符合關鍵字或有空位的票區，準備刷新...")
                try:
                    random_wait = self.get_random_reload_time(base_wait)
                    await self.tab.reload()
                    print(
                        f"    -> 刷新後隨機等待: {random_wait:.2f} 秒 (基準設定: {base_wait}s)")
                    await asyncio.sleep(random_wait)
                except:
                    pass

            elif result == -1:
                print(">>> [DEBUG] 區域選擇 JS 執行發生內部錯誤")

        except Exception as e:
            pass

    def get_random_reload_time(self, base_time):
        """
        區域選擇專用
        計算隨機浮動的重整時間
        base_time: 設定的基準秒數 (例如 0.5)
        return: 浮動後的秒數 (例如 0.5 + 0.3 = 0.8)
        """
        try:
            base = float(base_time)
        except:
            base = 0.5  # 預設值

        # 隨機決定是 + 還是 -
        sign = 1 if random.random() < 0.5 else -1

        # 產生 0.1 ~ 0.6 的隨機浮動值
        jitter = random.uniform(0.1, 0.6)

        # 計算最終時間
        final_time = base + (sign * jitter)

        # 防呆：確保時間至少有 0.1 秒，不會變成負數
        return max(0.1, final_time)

    async def select_ticket_quantity_legacy(self):
        """ [核心功能] 座位選擇 (純圖形座位表模式：暴力選位 + 自動聚焦驗證碼) """

        ticket_num = self.ticket_number
        if ticket_num <= 0:
            return

        # 專注於圖形座位表 (#TBL) 的極簡極速腳本
        js_select = f"""
        (function() {{
            try {{
                const targetTicketCount = {ticket_num};
                const seatTable = document.querySelector('#TBL');

                if (!seatTable) return 0; // 座位表還沒載入，回傳 0 繼續等

                // 1. 點擊票別按鈕 (無腦抓綠色一般票按鈕)
                const typeButton = document.querySelector('div.flex.seatype button.f1.green') || document.querySelector('button.f1.green');
                if (typeButton) typeButton.click();

                // 2. 尋找座位 (優先找連號)
                let targetSeats = [];
                const rows = document.querySelectorAll('#TBL tbody tr');

                for (let row of rows) {{
                    const cells = row.querySelectorAll('td');
                    let consecutiveSeats = [];

                    for (let cell of cells) {{
                        const styleStr = cell.getAttribute('style') || "";
                        const isAvailable = styleStr.includes('cursor: pointer') && styleStr.includes('seat-empty');

                        if (isAvailable) {{
                            consecutiveSeats.push(cell);
                            if (consecutiveSeats.length === targetTicketCount) {{
                                targetSeats = consecutiveSeats;
                                break;
                            }}
                        }} else if (styleStr.includes('seat-people') || !cell.hasAttribute('title')) {{
                            consecutiveSeats = []; // 遇到障礙物，連號重算
                        }}
                    }}
                    if (targetSeats.length > 0) break;
                }}

                // 3. 防呆機制：沒連號就硬抓剩下的空位
                if (targetSeats.length === 0) {{
                    const allAvailableSeats = Array.from(document.querySelectorAll('#TBL td')).filter(cell => {{
                        const s = cell.getAttribute('style') || "";
                        return s.includes('cursor: pointer') && s.includes('seat-empty');
                    }});
                    if (allAvailableSeats.length >= targetTicketCount) {{
                        targetSeats = allAvailableSeats.slice(
                            0, targetTicketCount);
                    }}
                }}

                // 4. 執行點擊與驗證碼聚焦
                if (targetSeats.length === targetTicketCount) {{
                    targetSeats.forEach(seat => seat.click());

                    // 選好座位後，幫你把游標焦點鎖定在驗證碼輸入框
                    const captchaInput = document.querySelector('#CHECK_CNF_CODE');
                    if (captchaInput) captchaInput.focus();

                    return 1; // 選位成功
                }} else {{
                    return 2; // 空位不足
                }}
            }} catch (e) {{
                return -1;
            }}
        }})();
        """

        try:
            result = await self.tab.evaluate(js_select)

            if result == 1:
                print(f">>> [座位] 🎉 成功鎖定 {ticket_num} 個座位！準備進行 OCR 辨識...")
                self.is_seat_selected = True  # 上鎖，不讓迴圈重複選位
                return True

            elif result == 2:
                print(f">>> [座位] ❌ 殘念...剩餘空位不足 {ticket_num} 張！準備重新整理頁面...")

                # 觸發自動重整，等待別人清票或系統放票
                try:
                    base_wait = float(self.config.get("advanced", {}).get(
                        "auto_reload_page_interval", 0.5))
                    if base_wait <= 0:
                        base_wait = 0.2

                    # 取一個隨機延遲時間，避免機器人特徵太明顯被封鎖
                    random_wait = self.get_random_reload_time(base_wait)

                    await self.tab.reload()  # 執行 F5 重新整理

                    print(
                        f"    -> 刷新後隨機等待: {random_wait:.2f} 秒 (基準設定: {base_wait}s)")
                    await asyncio.sleep(random_wait)
                except Exception as e:
                    pass

                return False  # 回傳 False，讓 dispatch_action 下次迴圈再進來找位子

            elif result == 0:
                # 畫面還沒載入完成，不做任何事，等待下一次迴圈
                return False

            elif result == -1:
                print("[DEBUG] 選位 JS 執行發生內部錯誤")
                return False

        except Exception as e:
            pass

        return False

    async def click_next(self):
        """[核心功能] 點擊下一步 (加入購物車) (含音效)"""

        # 1. 播放音效邏輯 (保持原樣)
        def play_coin_sound_independently():
            if self.config["advanced"].get("play_sound", {}).get("ticket", False):
                try:
                    import os
                    import util
                    app_root = util.get_app_root()
                    sound_path = os.path.join(app_root, "coin01.mp3")
                    if os.path.exists(sound_path):
                        print(f"[SOUND] 播放音效: {sound_path}")
                        util.play_mp3_async(sound_path)
                except Exception:
                    pass

        # 2. 核心點擊邏輯 (極簡極速版)
        js_click_cart = """
        (function() {
            try {
                // 直接透過 ID 尋找「加入購物車」按鈕
                const btn = document.querySelector('#addcart');
                if (btn && !btn.disabled) {
                    btn.click();
                    return 1; // 成功點擊
                }
                return 0; // 找不到或按鈕無效
            } catch (e) {
                return -1; // 發生錯誤
            }
        })();
        """

        try:
            result = await self.tab.evaluate(js_click_cart)

            if result == 1:
                # 判斷是否需要播放音效 (避免重複播放)
                try:
                    cur_url = await self.tab.evaluate("location.href")
                except:
                    cur_url = ""
                page_key = f"{cur_url}#addcart"

                if self.ticket_sound_tag.get("last_key") != page_key:
                    play_coin_sound_independently()
                    self.played_sound_ticket = True
                    self.ticket_sound_tag["last_key"] = page_key

                print(">>> [下一步]  成功點擊「加入購物車」按鈕！")
                return True

            elif result == 0:
                # 這裡不特別印出錯誤，因為主迴圈可能會頻繁呼叫它直到按鈕出現
                pass

        except Exception as e:
            pass

        return False

    async def process_captcha(self):
        """處理圖形驗證碼：抓取 #chk_pic -> ddddocr 辨識 -> 填入 #CHK"""

        print(">>> [OCR] 開始處理圖形驗證碼...")

        # 1. 利用 JS 將網頁上的圖片轉成 Base64
        js_get_image = """
        (function() {
            var img = document.querySelector('#chk_pic');
            if (!img) return null;

            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').split(',')[1];
        })();
        """

        try:
            # 最多嘗試辨識 3 次
            for attempt in range(3):
                base64_data = await self.tab.evaluate(js_get_image)

                if not base64_data:
                    print(">>> [OCR] 找不到驗證碼圖片 (#chk_pic)")
                    return False

                # 2. 解碼 Base64 並交給 ddddocr 辨識
                img_bytes = base64.b64decode(base64_data)
                ocr_answer = self.ocr.classification(img_bytes)

                # 清理辨識結果 (去掉空白)
                ocr_answer = ocr_answer.strip() if ocr_answer else ""
                print(f">>> [OCR] 第 {attempt + 1} 次辨識結果: '{ocr_answer}'")

                # 3. 判斷是否為 4 碼
                if len(ocr_answer) == 4:
                    # 4. 透過 JS 將答案填入輸入框 #CHK
                    js_fill_input = f"""
                    (function() {{
                        var input = document.querySelector('#CHK');
                        if (input) {{
                            input.value = '{ocr_answer}';
                            // 觸發網頁事件，讓前端框架知道有打字了
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        return false;
                    }})();
                    """
                    await self.tab.evaluate(js_fill_input)
                    print(f">>> [OCR]  已自動填入驗證碼: {ocr_answer}")
                    return True

                else:
                    print(">>> [OCR]  辨識長度不等於 4 碼，準備刷新圖片重試...")
                    # 透過 JS 刷新圖片，改變 src 後面的 timestamp
                    js_refresh_img = """
                    var img = document.querySelector('#chk_pic');
                    if(img) img.src = '/Home/pic?TYPE=UTK0205&ts=' + new Date().getTime();
                    """
                    await self.tab.evaluate(js_refresh_img)
                    await asyncio.sleep(0.2)  # 等待新圖片載入

            print(">>> [OCR]  嘗試 3 次辨識皆失敗，請手動輸入！")
            return False

        except Exception as e:
            print(f">>> [OCR] 發生例外錯誤: {e}")
            return False

    async def check_and_close_jquery_dialog(self):
        """處理 jQuery UI 的假彈窗 (專門針對：驗證碼輸入錯誤)"""
        js_check_dialog = """
        (function() {
            try {
                // 尋找 jQuery UI 的 Ok 按鈕
                let btn = document.querySelector('div.ui-dialog-buttonpane button');
                // 確保按鈕存在，且在畫面上是可見的 (offsetParent !== null)
                if (btn && btn.innerText.includes('Ok') && btn.offsetParent !== null) {
                    btn.click();
                    return true; // 發現並關閉了彈窗
                }
                return false; // 沒有彈窗
            } catch (e) {
                return false;
            }
        })();
        """
        try:
            result = await self.tab.evaluate(js_check_dialog)
            if result:
                print(">>> [驗證碼錯誤] 偵測到錯誤提示，已自動點擊 Ok 關閉！")
                return True
        except Exception:
            pass

        return False

    async def reload_config_if_changed(self):
        """[核心新增] 檢查設定檔 (settings.json) 是否變更，若有則熱重載"""
        try:
            # 請確認您的設定檔檔名是否為 settings.json
            config_path = "settings.json"

            # 檢查檔案是否存在
            if not os.path.exists(config_path):
                return

            # 獲取檔案最後修改時間
            mtime = os.path.getmtime(config_path)

            # 初始化 last_config_mtime (如果還沒有這個變數)
            if not hasattr(self, "last_config_mtime"):
                self.last_config_mtime = mtime
                return  # 第一次執行不需重載

            # 如果檔案修改時間比上次紀錄的新，代表被改過了
            if mtime > self.last_config_mtime:
                self.last_config_mtime = mtime

                print(f">>> [系統] 偵測到設定檔變更，正在熱重載...")

                import json
                with open(config_path, "r", encoding="utf-8") as f:
                    new_config = json.load(f)

                # 1. 更新區域關鍵字
                if "area_auto_select" in new_config:
                    self.area_auto_select = new_config["area_auto_select"]
                    k = self.area_auto_select.get('area_keyword', '')
                    m = self.area_auto_select.get('mode', '預設')
                    print(f"    -> 區域更新: 關鍵字[{k}] | 模式[{m}]")

                # 2. 更新日期關鍵字
                if "date_auto_select" in new_config:
                    self.date_auto_select = new_config["date_auto_select"]
                    k = self.date_auto_select.get('date_keyword', '')
                    print(f"-> 日期更新: 關鍵字[{k}]")

                # 3. 更新進階設定 (刷新秒數等)
                if "advanced" in new_config:
                    self.config["advanced"] = new_config["advanced"]
                    print(f"-> 進階設定已更新")

        except Exception as e:
            print(f">>> [熱重載失敗] {e}")

    async def send_telegram_message(self, message):
        """
        發送 Telegram 通知 (專屬類別版)
        """
        # 1. [基礎防呆] 檢查設定檔是否存在 (直接讀取 self.config)
        if not self.config or "advanced" not in self.config:
            return

        # 2. [開關檢查] 檢查是否啟用
        if not self.config["advanced"].get("telegram_enable", False):
            return

        # 3. [讀取資料]
        bot_token = self.config["advanced"].get("telegram_bot_token", "")
        chat_id = self.config["advanced"].get("telegram_chat_id", "")

        # 4. [資料檢查]
        if not bot_token or not chat_id:
            print("⚠️ Telegram 設定不完整，跳過通知")
            return

        # 5. [發送請求]
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }

            # 設定 timeout=6 秒，避免網路卡頓影響搶票
            response = requests.post(url, data=payload, timeout=6)

            if response.status_code == 200:
                print("✅ Telegram 搶票成功通知發送成功！")
            else:
                print(
                    f"❌ Telegram 發送失敗 (代碼 {response.status_code}): {response.text}")

        except Exception as e:
            print(f"❌ Telegram 連線錯誤: {e}")


# ==========================================
# [PLG富邦搶票]
# ==========================================


class EraBot:

    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        # 🔥 統一標準：從主程式接收檔案路徑，沒傳的話保底用 settings.json
        self.settings_path = config.get("config_filepath", "settings.json")

        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 狀態變數
        self.is_login_done = False
        self.is_date_selected = False
        self.is_area_selected = False
        self.is_seat_selected = False
        self.is_telegram_sent = False

        # ==========================================
        # [新增] 綁定 GUI 的暫停控制檔案
        # ==========================================
        self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # 初始化 ddddocr 引擎
        print(">>> [年代售票] 正在載入 ddddocr 辨識模型...")
        self.ocr = ddddocr.DdddOcr(show_ad=False)

    async def dispatch_action(self, url):
        """年代售票 任務分發中心"""
        upper_url = url.upper()

        # ==========================================
        # 0. 首頁狀態重置 (UTK0101_)
        # ==========================================
        if 'UTK0101_' in upper_url:
            self.is_date_selected = False
            self.is_area_selected = False
            self.is_seat_selected = False
            self.is_telegram_sent = False

        # ==========================================
        # 1. 自動登入階段 (UTK1306_)
        # ==========================================
        elif 'UTK1306_' in upper_url:
            if not getattr(self, 'is_login_done', False):
                await self.auto_login()

        # ==========================================
        # 2. 選擇區域 (UTK0201_000 或 UTK0204_)
        # ==========================================
        # 🔥 把區域的判斷往前拉，優先攔截 _000
        elif 'UTK0201_000' in upper_url or 'UTK0204_' in upper_url:
            self.is_seat_selected = False

            if not getattr(self, 'is_area_selected', False):
                await self.select_area()

        # ==========================================
        # 3. 選擇日期/場次 (UTK0201_00)
        # ==========================================
        # 🔥 嚴格限制只有 _00 結尾的才是日期頁
        elif 'UTK0201_00' in upper_url:
            self.is_area_selected = False
            self.is_seat_selected = False

            if not getattr(self, 'is_date_selected', False):
                await self.select_date()
        # ==========================================
        # 4. 第三階段：座位選擇 / 張數輸入 -> OCR -> 加入購物車
        # ==========================================
        # 將 UTK0202_ (一般模式) 和 UTK0205_ (座位圖模式) 合併處理
        elif 'UTK0202_' in upper_url or 'UTK0205_' in upper_url or ('UTK0204_' in upper_url and getattr(self, 'is_area_selected', False)):

            # 【環節 A：錯誤彈窗處理】接收擷取到的彈窗文字
            error_msg = await self.check_and_close_jquery_dialog()

            if error_msg:
                print(f">>> [系統]系統彈窗攔截: 【{error_msg}】 (已自動點擊 Ok)")
                print(">>> [系統] 準備重新整理頁面，獲取最新空位狀態...")

                import asyncio
                # 1. 解開座位鎖，確保等一下重整完會重新觸發選位
                self.is_seat_selected = False

                # 2. 執行 F5 重新整理
                await self.tab.reload()

                # 3. 給予短暫緩衝時間等待網頁開始載入
                await asyncio.sleep(0.5)

            else:
                # 【環節 B：正常流程】如果沒有彈窗，且還沒選過位子，才執行選位/選張數
                if not getattr(self, 'is_seat_selected', False):

                    # 1. 執行智能選位 (支援雙模式)
                    seat_success = await self.select_tickets()

                    if seat_success:
                        import asyncio
                        await asyncio.sleep(0.5)

                        # 2. 呼叫 OCR 執行自動辨識並填入
                        ocr_success = await self.process_captcha()

                        # 3. 如果 OCR 辨識成功，點擊加入購物車
                        if ocr_success:
                            await self.click_next()

    async def run(self):
        print(f">>> [年代售票] 機器人啟動！(目標張數: {self.ticket_number})")
        print("等待網頁載入中...")

        import os
        import asyncio

        while True:
            try:
                # ==========================================
                # 【防護】GUI 暫停機制攔截
                # ==========================================
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                # 取得當前網址
                current_url = await self.tab.evaluate("window.location.href")

                # 檢測頁面切換
                if current_url and current_url != self.last_url:
                    print(f"偵測到頁面切換: {current_url}")
                    upper_url = current_url.upper()

                    # ==========================================
                    # 🔥 修正：精準切割區域與日期，避免鎖被誤洗！
                    # ==========================================
                    # 1. 區域選擇頁面 (UTK0201_000)
                    if 'UTK0201_000' in upper_url:
                        # 進入區域頁了，千萬不要重置日期鎖！
                        pass

                    # 2. 真實的日期選擇頁面 (UTK0201_00)
                    elif 'UTK0201_00' in upper_url:
                        if getattr(self, 'is_date_selected', False):
                            print(">>> [系統] 偵測到真實退回日期選擇頁，已重置日期鎖，準備重新掃描場次！")
                            self.is_date_selected = False
                        await self.reload_settings()

                    # 3. 另外一種區域選擇頁 (UTK0204_)
                    elif 'UTK0204_' in upper_url and getattr(self, 'is_area_selected', False):
                        print(">>> [系統] 偵測到退回區域選擇頁，已重置區域鎖，準備重新刷票！")
                        self.is_area_selected = False

                    # 4. 退回到「票數/座位選擇頁」
                    elif ('UTK0202_' in upper_url or 'UTK0205_' in upper_url) and getattr(self, 'is_seat_selected', False):
                        print(">>> [系統] 偵測到退回座位/票數頁面，已重置座位鎖，準備重新選位！")
                        self.is_seat_selected = False

                    self.last_url = current_url

                # 分發動作
                if current_url:
                    await self.dispatch_action(current_url)

            except Exception as e:
                pass

            await asyncio.sleep(0.05)

    async def reload_settings(self):
        """[年代售票] 從設定檔讀取最新搶票設定 (支援多重設定檔動態切換 + 磁碟 I/O 提速)"""
        import json
        import os

        # 🔥 核心修正：使用初始化時存好的動態路徑
        settings_path = getattr(self, 'settings_path', 'settings.json')

        try:
            # 檢查檔案是否存在
            if not os.path.exists(settings_path):
                return

            # 🔥 終極提速核心：檢查檔案修改時間，沒變過就不讀取硬碟，直接秒退！
            current_mtime = os.path.getmtime(settings_path)
            if getattr(self, 'last_settings_mtime', 0) == current_mtime:
                return
            self.last_settings_mtime = current_mtime

            # 讀取 JSON 檔案
            with open(settings_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)

            # 更新年代售票需要的設定區塊
            if "area_auto_select" in new_config:
                self.config["area_auto_select"] = new_config["area_auto_select"]
                # 年代特有：同步更新屬性，確保 select_area 抓得到
                self.area_auto_select = new_config["area_auto_select"]
            if "date_auto_select" in new_config:
                self.config["date_auto_select"] = new_config["date_auto_select"]
            if "advanced" in new_config:
                self.config["advanced"] = new_config["advanced"]
            if "keyword_exclude" in new_config:
                self.config["keyword_exclude"] = new_config["keyword_exclude"]
            if "ticket_number" in new_config:
                self.config["ticket_number"] = new_config["ticket_number"]
                self.ticket_number = int(new_config.get("ticket_number", 1))

            # 抓出純檔名，讓 Log 看起來乾淨俐落
            filename = os.path.basename(settings_path)
            print(f">>> [系統] 進入日期選擇頁面！已成功套用最新設定 ({filename})")

        except json.JSONDecodeError:
            filename = os.path.basename(settings_path)
            print(f">>> [系統錯誤] {filename} 格式有誤！請檢查是否多加了逗號或少了雙引號。")
        except Exception as e:
            pass

    async def auto_login(self):
        """[核心] 年代售票：自動填入帳號密碼 -> OCR 驗證碼 -> 穩健點擊登入"""

        # 1. 從設定檔讀取帳號密碼
        account = self.config.get("advanced", {}).get("ticket_account", "")
        password = self.config.get("advanced", {}).get(
            "ticket_password_plaintext", "").strip()

        if not password:
            try:
                import util
                password = util.decrypt_me(self.config.get(
                    "advanced", {}).get("ticket_password", ""))
            except:
                pass

        if not account or not password:
            print(">>> [年代售票] ⚠️ 未設定帳號密碼，跳過自動登入！")
            self.is_login_done = True
            return

        # 2. 構建 JS 腳本：瞬間填入帳號與密碼
        js_fill_credentials = f"""
        (function() {{
            try {{
                let accInput = document.querySelector('input[cname="帳號"]');
                let pwdInput = document.querySelector('input[cname="密碼"]');

                if (accInput && pwdInput && accInput.value === '') {{
                    accInput.value = '{account}';
                    pwdInput.value = '{password}';

                    accInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    pwdInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    return true;
                }}
                return accInput.value !== '';
            }} catch(e) {{
                return false;
            }}
        }})();
        """

        try:
            is_filled = await self.tab.evaluate(js_fill_credentials)

            if is_filled:
                print(">>> [年代售票] 帳號密碼已填入！準備處理驗證碼...")

                # 3. 呼叫 OCR 辨識並填入驗證碼
                ocr_success = await self.process_captcha()

                # 4. 確認驗證碼填寫成功後，再按確認登入
                if ocr_success:
                    print(">>> [年代售票] 驗證碼填寫完畢，等待 0.5 秒確保網頁接收...")
                    import asyncio
                    await asyncio.sleep(0.5)  # 不拚速度，確保萬無一失

                    js_click_login = """
                    (function() {
                        // 支援年代售票可能的登入按鈕寫法 (包含 a 標籤或 input)
                        let loginBtn = document.querySelector('a.btn-login') ||
                                       document.querySelector('input[value="登入"]') ||
                                       document.querySelector('button[value="登入"]');
                        if (loginBtn) {
                            loginBtn.click();
                            return true;
                        }
                        return false;
                    })();
                    """
                    btn_clicked = await self.tab.evaluate(js_click_login)
                    if btn_clicked:
                        print(">>> [年代售票] 👉 已點擊登入按鈕！")
                        self.is_login_done = True
                    else:
                        print(">>> [年代售票] ⚠️ 找不到登入按鈕，請確認網頁結構！")

        except Exception as e:
            print(f">>> [年代售票] 登入過程發生錯誤: {e}")

    async def process_captcha(self):
        """共用核心：處理圖形驗證碼"""
        print(">>> [OCR] 開始處理圖形驗證碼...")

        js_get_image = """
        (function() {
            var img = document.querySelector('#chk_pic');
            if (!img) return null;

            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').split(',')[1];
        })();
        """

        try:
            for attempt in range(3):
                base64_data = await self.tab.evaluate(js_get_image)
                if not base64_data:
                    print(">>> [OCR] 找不到驗證碼圖片 (#chk_pic)")
                    return False

                import base64
                img_bytes = base64.b64decode(base64_data)
                ocr_answer = self.ocr.classification(img_bytes)
                ocr_answer = ocr_answer.strip() if ocr_answer else ""

                print(f">>> [OCR] 第 {attempt + 1} 次辨識結果: '{ocr_answer}'")

                if len(ocr_answer) == 4:
                    js_fill_input = f"""
                    (function() {{
                        // 【關鍵修改】：加入 ASP.NET 的專屬 ID，並保留其他備用選項
                        var input = document.querySelector('#ctl00_ContentPlaceHolder1_CHK') ||
                                    document.querySelector('#CHK') ||
                                    document.querySelector('input[cname="認證碼"]');
                        if (input) {{
                            input.value = '{ocr_answer}';
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        return false;
                    }})();
                    """
                    is_filled = await self.tab.evaluate(js_fill_input)
                    if is_filled:
                        print(f">>> [OCR] ✅ 已自動填入驗證碼: {ocr_answer}")
                        return True
                    else:
                        print(">>> [OCR] ⚠️ 找不到驗證碼輸入框！")
                        return False
                else:
                    # 辨識失敗，點擊換圖
                    print(">>> [OCR] ⚠️ 辨識長度不對，刷新圖片重試...")
                    js_refresh_img = "let img = document.querySelector('#chk_pic'); if(img) img.click();"
                    await self.tab.evaluate(js_refresh_img)
                    import asyncio
                    await asyncio.sleep(0.5)

            return False
        except Exception as e:
            print(f">>> [OCR] 發生例外錯誤: {e}")
            return False

    async def select_date(self):
        """[年代售票] 場次/日期選擇 (支援開賣倒數原地狙擊版)"""
        print(">>> [系統] 進入年代售票日期選擇階段...")
        try:
            date_auto_select = self.config.get("date_auto_select", {})
            if not date_auto_select.get("enable", True):
                print(">>> [年代售票-日期] 設定檔未啟用，跳過。")
                return

            raw_keyword = date_auto_select.get("date_keyword", "").strip()
            import json
            keyword_list = []
            if len(raw_keyword) > 0:
                try:
                    if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                        keyword_list = json.loads(raw_keyword)
                    else:
                        keyword_list = json.loads("[" + raw_keyword + "]")
                except:
                    keyword_list = [raw_keyword]
            else:
                keyword_list = [""]

            js_keywords = json.dumps(keyword_list, ensure_ascii=False)
            js_mode = f"'{date_auto_select.get('mode', 'from top to bottom')}'"

            js_script = f"""
            (function() {{
                try {{
                    const keywords = {js_keywords};
                    const mode = {js_mode};

                    let rows = Array.from(document.querySelectorAll("table tbody tr"));
                    let candidates_ready = [];
                    let candidates_countdown = [];

                    if (rows && rows.length > 0) {{
                        for (let row of rows) {{
                            let btn = row.querySelector("button.btn-event") || row.querySelector("button");
                            if (!btn) continue;

                            // 1. 檢查硬體鎖定
                            if (btn.disabled || btn.classList.contains('disabled')) continue;

                            let btnTextRaw = (btn.innerText || "").toUpperCase();
                            
                            // 2. 絕對死亡名單 (真的不能買的)
                            let isDead = btnTextRaw.includes('售完') || 
                                         btnTextRaw.includes('暫停') || 
                                         btnTextRaw.includes('SOLD OUT');
                            if (isDead) continue;

                            // 3. 倒數名單 (有機會，需原地等待)
                            let isCountdown = btnTextRaw.includes('倒數') || 
                                              btnTextRaw.includes('分') || 
                                              btnTextRaw.includes('秒') || 
                                              btnTextRaw.includes('尚未');

                            // 4. 組合場次文字
                            let rowText = row.innerText.toUpperCase();
                            let timeEl = row.querySelector("time");
                            if (timeEl && timeEl.getAttribute("datetime")) {{
                                let dt = timeEl.getAttribute("datetime").toUpperCase();
                                let p = dt.split("-");
                                if (p.length === 3) {{
                                    let y = p[0]; let m_str = p[1]; let d_str = p[2];
                                    let m_int = parseInt(m_str, 10).toString();
                                    let d_int = parseInt(d_str, 10).toString();
                                    rowText += ` ${{dt}} ${{y}}/${{m_str}}/${{d_str}} ${{y}}/${{m_int}}/${{d_int}} ${{m_str}}/${{d_str}} ${{m_int}}/${{d_int}} ${{m_str}}${{d_str}} ${{m_int}}月${{d_int}}日 ${{m_str}}月${{d_str}}日`;
                                }} else {{
                                    rowText += " " + dt;
                                }}
                            }}

                            // 5. 關鍵字過濾
                            let isMatch = false;
                            if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                                isMatch = true;
                            }} else {{
                                for (let k of keywords) {{
                                    let target_kws = k.trim().split(" ").filter(w => w.length > 0);
                                    let currentGroupMatch = true;
                                    for (let w of target_kws) {{
                                        if (!rowText.includes(w.toUpperCase())) {{
                                            currentGroupMatch = false;
                                            break;
                                        }}
                                    }}
                                    if (currentGroupMatch) {{
                                        isMatch = true;
                                        break;
                                    }}
                                }}
                            }}

                            // 6. 分流：是可以買了？還是還在倒數？
                            if (isMatch) {{
                                if (isCountdown) {{
                                    candidates_countdown.push(btn);
                                }} else {{
                                    candidates_ready.push(btn);
                                }}
                            }}
                        }}
                    }}

                    // 🔥 狀況 A：有已經解鎖的按鈕 ➔ 點擊並回傳 1
                    if (candidates_ready.length > 0) {{
                        if (mode === "from bottom to top") {{
                            candidates_ready.reverse();
                        }} else if (mode === "random") {{
                            for (let i = candidates_ready.length - 1; i > 0; i--) {{
                                const j = Math.floor(Math.random() * (i + 1));
                                [candidates_ready[i], candidates_ready[j]] = [candidates_ready[j], candidates_ready[i]];
                            }}
                        }}
                        candidates_ready[0].click();
                        return 1;
                    }}
                    
                    // 🔥 狀況 B：找不到解鎖按鈕，但找到了倒數中的目標 ➔ 回傳 3 (啟動狙擊模式)
                    if (candidates_countdown.length > 0) {{
                        return 3;
                    }}

                    // 🔥 狀況 C：畫面上連倒數按鈕都沒有 (可能還沒開賣或完全找錯頁面) ➔ 回傳 2 (重新整理)
                    return 2;

                }} catch (e) {{
                    return -1;
                }}
            }})();
            """

            result = await self.tab.evaluate(js_script)

            if result == 1:
                print(">>> [年代售票-日期] 🎉 成功匹配日期並執行點擊！等待網頁跳轉...")
                self.is_date_selected = True
                import asyncio
                await asyncio.sleep(0.5)

            elif result == 2:
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))
                if base_wait > 0:
                    print(">>> [年代售票-日期] 找不到可用場次或倒數按鈕，準備刷新...")
                    import asyncio
                    await self.tab.reload()
                    await asyncio.sleep(base_wait)

            # 🔥 新增狙擊狀態處理
            elif result == 3:
                if not hasattr(self, 'date_sniper_log'):
                    self.date_sniper_log = 0
                self.date_sniper_log += 1
                if self.date_sniper_log % 20 == 0:
                    print(">>> [年代售票-日期] ⏳ 鎖定倒數計時中！不刷新網頁，每 0.05 秒死盯按鈕解鎖...")
                import asyncio
                # 只等待 0.05 秒，不重整網頁，讓迴圈迅速回來重新執行 JS！
                await asyncio.sleep(0.05)

            elif result == -1:
                print(">>> [DEBUG] 日期選擇 JS 執行發生內部錯誤")

        except Exception as e:
            print(f">>> [嚴重錯誤] select_date 發生 Python 例外: {e}")

    async def select_area(self):
        """[年代售票] 區域選擇 (精準鎖定 <li> <a> 結構 + 排除關鍵字 + 去逗號防呆)"""

        print(">>> [系統] 進入年代售票區域選擇階段...")

        try:
            # 1. 讀取設定檔的區域自動選擇設定
            area_auto_select = getattr(
                self, 'area_auto_select', self.config.get("area_auto_select", {}))
            if not area_auto_select.get("enable", True):
                print(">>> [年代售票-區域] 設定檔未啟用區域自動選擇，跳過。")
                return

            auto_select_mode = area_auto_select.get(
                "mode", "from top to bottom")

            # ==========================================
            # 🔥 修正：同時讀取「包含」與「排除」關鍵字
            # ==========================================
            raw_keyword = area_auto_select.get("area_keyword", "").strip()
            raw_keyword_exclude = self.config.get("keyword_exclude", "")
            if not raw_keyword_exclude:
                raw_keyword_exclude = area_auto_select.get(
                    "area_keyword_exclude", "")
            raw_keyword_exclude = str(raw_keyword_exclude).strip()

            import json

            def parse_keywords(kw_str):
                kw_str = kw_str.strip()
                if not kw_str:
                    return [""]
                try:
                    if kw_str.startswith("[") and kw_str.endswith("]"):
                        return json.loads(kw_str)
                    if '"' in kw_str or "'" in kw_str:
                        return json.loads("[" + kw_str + "]")
                except:
                    pass
                return [x.strip().strip('\'"') for x in kw_str.replace('，', ',').split(',') if x.strip()]

            keyword_list = parse_keywords(raw_keyword)
            exclude_list = parse_keywords(raw_keyword_exclude)

            js_keywords = json.dumps(keyword_list, ensure_ascii=False)
            js_excludes = json.dumps(exclude_list, ensure_ascii=False)
            js_mode = f"'{auto_select_mode}'"

            # 2. 構建 年代售票專用 的超快速 JavaScript 腳本
            js_script = f"""
            (function() {{
                try {{
                    const keywords = {js_keywords};
                    const excludes = {js_excludes};
                    const mode = {js_mode};

                    // 【關鍵防護升級】：精準鎖定真正的票區按鈕
                    let availableLinks = Array.from(document.querySelectorAll('li > a')).filter(a => {{
                        return a.querySelector('font') !== null && a.querySelector('img') === null;
                    }});

                    let candidates = [];

                    if (availableLinks.length > 0) {{
                        for (let link of availableLinks) {{
                            //  修正：把文字裡的逗號去掉，轉大寫，確保比對精準
                            const rowContent = link.innerText.replace(/,/g, '').toUpperCase();

                            // [雙重防呆] 確保真的沒有包含售完字眼
                            if (rowContent.includes('SOLD OUT') || rowContent.includes('售完')) continue;

                            // ==========================================
                            // 🔥 修正：新增排除關鍵字判斷
                            // ==========================================
                            let isExcluded = false;
                            if (excludes.length > 0 && excludes[0] !== "") {{
                                for (let exc of excludes) {{
                                    let cleanExc = exc.trim().replace(/,/g, '').toUpperCase();
                                    if (cleanExc.length > 0 && rowContent.includes(cleanExc)) {{
                                        isExcluded = true; break;
                                    }}
                                }}
                            }}
                            if (isExcluded) continue; // 發現排除字眼(如：輪椅)，直接跳過這個區域！

                            // 關鍵字比對邏輯
                            let isMatch = false;
                            if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                                isMatch = true; // 沒設關鍵字，全部皆可
                            }} else {{
                                for (let k of keywords) {{
                                    // 🔥 修正：目標關鍵字也去逗號
                                    let target_kws = k.trim().replace(/,/g, '').split(/\\s+/).filter(w => w.length > 0);
                                    let currentGroupMatch = true;
                                    for (let w of target_kws) {{
                                        if (!rowContent.includes(w.toUpperCase())) {{
                                            currentGroupMatch = false;
                                            break;
                                        }}
                                    }}
                                    if (currentGroupMatch) {{
                                        isMatch = true;
                                        break;
                                    }}
                                }}
                            }}

                            // 如果關鍵字符合，將這個 <a> 標籤加入候選名單
                            if (isMatch) {{
                                candidates.push(link);
                            }}
                        }}
                    }}

                    // 找不到符合且有票的區域，回傳 2 讓 Python 去重整網頁
                    if (candidates.length === 0) return 2;

                    // 根據設定檔的模式進行排序
                    if (mode === "from bottom to top") {{
                        candidates.reverse();
                    }} else if (mode === "random") {{
                        for (let i = candidates.length - 1; i > 0; i--) {{
                            const j = Math.floor(Math.random() * (i + 1));
                            [candidates[i], candidates[j]] = [
                                candidates[j], candidates[i]];
                        }}
                    }}

                    // 執行點擊 (點擊排序後的第一個區域)
                    candidates[0].click();
                    return 1;

                }} catch(e) {{
                    return -1; // 發生例外錯誤
                }}
            }})();
            """

            # 3. 執行 JS 與狀態處理
            result = await self.tab.evaluate(js_script)

            if result == 1:
                print(f">>> [年代售票-區域] 👉 成功匹配關鍵字並點擊區域！")
                import asyncio
                await asyncio.sleep(0.2)  # 給網頁一點跳轉的緩衝時間
                self.is_area_selected = True

            elif result == 2:
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))
                if base_wait <= 0:
                    base_wait = 0.2

                print(">>> [年代售票-區域] 找不到符合關鍵字或有空位的票區，準備刷新...")
                import asyncio
                await self.tab.reload()
                print(f"    -> 刷新後固定等待: {base_wait} 秒")
                await asyncio.sleep(base_wait)

            elif result == -1:
                print(">>> [DEBUG] 區域選擇 JS 執行發生內部錯誤")

        except Exception as e:
            print(f">>> [嚴重錯誤] select_area 發生 Python 例外: {e}")

    async def select_tickets(self):
        """[年代售票] 智能票數與座位選擇 (雙模式自動切換)"""
        ticket_num = self.ticket_number
        if ticket_num <= 0:
            return False

        js_select = f"""
        (function() {{
            try {{
                const targetTickets = {ticket_num};
                const seatTable = document.querySelector('#TBL');

                // ==========================================
                // 模式 2：座位圖模式 (有 #TBL)
                // ==========================================
                if (seatTable) {{
                    // A. 選擇票種 (避開身障)
                    let typeBtns = document.querySelectorAll('div.ticketType button');
                    let selectedBtn = null;
                    for (let btn of typeBtns) {{
                        let btnText = btn.innerText || "";
                        if (btnText.includes('身障') || btnText.includes('身心障礙')) continue;
                        selectedBtn = btn;
                        break;
                    }}
                    if (selectedBtn) selectedBtn.click();

                    // B. 尋找空座位 (優先找連號)
                    let rows = document.querySelectorAll('#TBL tbody tr');
                    let targetSeats = [];
                    for (let row of rows) {{
                        let cells = row.querySelectorAll('td');
                        let consec = [];
                        for (let cell of cells) {{
                            let bg = cell.style.backgroundImage || "";
                            // 判斷是否為空位
                            if (bg.includes('icon_chair_empty') && cell.style.cursor === 'pointer') {{
                                consec.push(cell);
                                if (consec.length === targetTickets) {{
                                    targetSeats = consec;
                                    break;
                                }}
                            // 如果遇到已售出或走道，連號重算
                            }} else if (bg.includes('icon_chair_sale') || !cell.hasAttribute('title')) {{
                                consec = [];
                            }}
                        }}
                        if (targetSeats.length > 0) break;
                    }}

                    // 防呆：沒連號就硬抓剩下的空位
                    if (targetSeats.length === 0) {{
                        let allEmpty = Array.from(document.querySelectorAll('#TBL td')).filter(c => {{
                            let b = c.style.backgroundImage || "";
                            return b.includes('icon_chair_empty') && c.style.cursor === 'pointer';
                        }});
                        if (allEmpty.length >= targetTickets) {{
                            targetSeats = allEmpty.slice(0, targetTickets);
                        }}
                    }}

                    // C. 點擊座位並聚焦驗證碼
                    if (targetSeats.length === targetTickets) {{
                        targetSeats.forEach(s => s.click());
                        let captchaInput = document.querySelector('#ctl00_ContentPlaceHolder1_CHK');
                        if(captchaInput) captchaInput.focus();
                        return 1; // 成功
                    }} else {{
                        return 2; // 空位不足
                    }}
                }}
                // ==========================================
                // 模式 1：一般張數輸入模式 (沒有 #TBL)
                // ==========================================
                else {{
                    let rows = document.querySelectorAll('table tbody tr');
                    let targetInput = null;

                    for (let row of rows) {{
                        let labelCell = row.querySelector('td[data-th="內容"]');
                        if (labelCell) {{
                            let labelText = labelCell.innerText || "";
                            if (labelText.includes('身障') || labelText.includes('身心障礙')) continue;
                        }}

                        let input = row.querySelector('input.qty');
                        if (input && !input.disabled) {{
                            targetInput = input;
                            break;
                        }}
                    }}

                    if (targetInput) {{
                        targetInput.value = targetTickets;
                        // 觸發網頁的驗證腳本
                        targetInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        targetInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        // 嘗試呼叫內建的 checkNum 函式 (年代售票的防呆機制)
                        if (typeof checkNum === "function") {{
                            checkNum(targetInput.id, targetTickets);
                        }}

                        let captchaInput = document.querySelector('#ctl00_ContentPlaceHolder1_CHK');
                        if(captchaInput) captchaInput.focus();
                        return 1; // 成功
                    }}
                    return 2; // 找不到可輸入的格子
                }}
            }} catch(e) {{
                return -1;
            }}
        }})();
        """

        try:
            result = await self.tab.evaluate(js_select)
            if result == 1:
                print(f">>> [座位/票數] 🎉 成功鎖定 {ticket_num} 張票！準備進行 OCR 辨識...")
                self.is_seat_selected = True
                return True
            elif result == 2:
                print(f">>> [座位/票數] ❌ 殘念...剩餘空位不足 {ticket_num} 張！準備重新整理頁面...")
                try:
                    base_wait = float(self.config.get("advanced", {}).get(
                        "auto_reload_page_interval", 0.5))
                    if base_wait <= 0:
                        base_wait = 0.2
                    import asyncio
                    await self.tab.reload()
                    await asyncio.sleep(base_wait)
                except:
                    pass
                return False
        except Exception as e:
            pass
        return False

    async def click_next(self):
        """[年代售票] 點擊加入購物車 (雙模式相容)"""
        js_submit = """
        (function() {
            try {
                // 優先找一般模式的加入購物車按鈕
                let btn1 = document.querySelector('#ctl00_ContentPlaceHolder1_AddShopingCart');
                // 再找座位圖模式的加入購物車按鈕
                let btn2 = document.querySelector('button.sumitButton');

                let btn = btn1 || btn2;
                if (btn && !btn.disabled) {
                    btn.click();
                    return true;
                }
                return false;
            } catch (e) {
                return false;
            }
        })();
        """
        try:
            result = await self.tab.evaluate(js_submit)
            if result:
                print(">>> [下一步] 🛒 已成功點擊「加入購物車」按鈕！")
                return True
        except:
            pass
        return False

    async def check_and_close_jquery_dialog(self):
        """處理 jQuery UI 的錯誤彈窗，並擷取彈窗內的文字內容"""
        js_check_dialog = """
        (function() {
            try {
                let btn = document.querySelector('div.ui-dialog-buttonpane button');

                // 確認按鈕存在、文字包含 Ok，且目前是顯示狀態
                if (btn && btn.innerText.includes('Ok') && btn.offsetParent !== null) {

                    // 往上尋找整個彈窗的父容器
                    let dialogBox = btn.closest('.ui-dialog');
                    let msgText = "未知的提示內容";

                    if (dialogBox) {
                        // 尋找 jQuery UI 存放文字內容的區塊
                        let contentNode = dialogBox.querySelector('.ui-dialog-content');
                        if (contentNode) {
                            msgText = contentNode.innerText.trim();
                        }
                    }

                    btn.click(); // 點擊關閉
                    return msgText; // 將抓到的文字回傳給 Python
                }
                return false;
            } catch (e) {
                return false;
            }
        })();
        """
        try:
            result = await self.tab.evaluate(js_check_dialog)
            # 如果回傳的是字串 (也就是有抓到彈窗)，Python 的 if 判斷會是 True
            if result:
                return result
        except:
            pass

        return False


# ==========================================
# [年代售票]
# ==========================================

class KhamBot:

    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        # 🔥 統一標準：從 config 拿取路徑，如果沒有就用預設值 settings.json
        self.settings_path = config.get("config_filepath", "settings.json")

        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 狀態變數
        self.is_login_done = False
        self.is_date_selected = False
        self.is_area_selected = False
        self.is_seat_selected = False
        self.is_telegram_sent = False

        # ==========================================
        # 綁定 GUI 的暫停控制檔案
        # ==========================================
        import os
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # 初始化 ddddocr 引擎
        print(">>> [寬宏售票] 正在載入 ddddocr 辨識模型...")
        try:
            import ddddocr
            self.ocr = ddddocr.DdddOcr(show_ad=False)
        except Exception as e:
            print(f">>> [系統] ddddocr 載入失敗: {e}")
            self.ocr = None

    async def run(self):
        print(f">>> [寬宏售票] 機器人啟動！(目標張數: {self.ticket_number})")
        print("等待網頁載入中...")

        import os
        import asyncio

        while True:
            try:
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                current_url = await self.tab.evaluate("window.location.href")

                if current_url and current_url != self.last_url:
                    print(f"偵測到頁面切換: {current_url}")
                    upper_url = current_url.upper()

                    # 🔥 把原本這裡的 await self.reload_settings() 刪除了！不再卡頓！
                    if 'UTK0201_' in upper_url and 'UTK0201_00' not in upper_url:
                        self.is_date_selected = False

                    elif 'UTK0201_00' in upper_url:
                        if getattr(self, 'is_date_selected', False):
                            print(">>> [系統] 偵測到退回日期選擇頁，已重置日期鎖，準備重新掃描場次！")
                            self.is_date_selected = False

                    elif 'UTK0204_' in upper_url and getattr(self, 'is_area_selected', False):
                        print(">>> [系統] 偵測到退回區域選擇頁，已重置區域鎖，準備重新刷票！")
                        self.is_area_selected = False

                    elif ('UTK0202_' in upper_url or 'UTK0205_' in upper_url) and getattr(self, 'is_seat_selected', False):
                        print(">>> [系統] 偵測到退回座位/票數頁面，已重置座位鎖，準備重新選位與打碼！")
                        self.is_seat_selected = False

                    self.last_url = current_url

                if current_url:
                    await self.dispatch_action(current_url)

            except Exception as e:
                pass

            await asyncio.sleep(0.05)

    async def dispatch_action(self, url):
        """寬宏售票 任務分發中心 (升級版：精準支援 UTK0201_ 家族各種跳轉)"""
        upper_url = url.upper()

        # ==========================================
        # 0. 首頁狀態重置與登入跳轉
        # ==========================================
        if 'UTK0101_' in upper_url:
            self.is_date_selected = False
            self.is_area_selected = False
            self.is_seat_selected = False
            self.is_telegram_sent = False

            if not getattr(self, 'is_login_done', False):
                print(">>> [寬宏售票] 偵測到在首頁且尚未登入，準備強制導航前往登入頁面...")
                login_url = "https://kham.com.tw/application/utk13/utk1306_.aspx"
                jump_js = f"window.location.href = '{login_url}';"
                try:
                    await self.tab.evaluate(jump_js)
                except:
                    pass
                import asyncio
                await asyncio.sleep(1)
                return

        # ==========================================
        # 1. 自動登入階段
        # ==========================================
        elif 'UTK1306_' in upper_url:
            if not getattr(self, 'is_login_done', False):
                if hasattr(self, 'auto_login'):
                    await self.auto_login()

        # ==========================================
        # 1.5 活動詳情頁 (我要購票按鈕)
        # 排除 000(區域頁), 001(票數頁), 041/00.ASPX(日期頁)
        # ==========================================
        elif 'UTK0201_040' in upper_url or ('UTK0201_' in upper_url and not any(x in upper_url for x in ['UTK0201_00', 'UTK0201_041', 'UTK0201_000', 'UTK0201_001'])):
            self.is_date_selected = False
            self.is_area_selected = False
            self.is_seat_selected = False
            if hasattr(self, 'click_go_buy'):
                await self.click_go_buy()

        # ==========================================
        # 2. 選擇日期/場次
        # ==========================================
        elif any(x in upper_url for x in ['UTK0201_00.ASPX', 'UTK0201_041']):
            self.is_area_selected = False
            self.is_seat_selected = False
            if not getattr(self, 'is_date_selected', False):
                if hasattr(self, 'select_date'):
                    await self.select_date()

        # ==========================================
        # 3. 🔥 選擇區域 (支援舊版 UTK0204_ 與新版 UTK0201_000)
        # ==========================================
        elif any(x in upper_url for x in ['UTK0204_.ASPX', 'UTK0201_000']):
            self.is_seat_selected = False
            if not getattr(self, 'is_area_selected', False):
                if hasattr(self, 'select_area'):
                    await self.select_area()

        # ==========================================
        # 4. 票數選擇 / 座位選擇
        # ==========================================
        elif any(x in upper_url for x in ['UTK0202_', 'UTK0205_', 'UTK0201_001']):
            if not self.is_area_selected:
                print(">>> [系統] 🎯 偵測到已進入票數/座位頁面，立刻啟動搶票程式！")
                self.is_area_selected = True

            error_msg = await self.check_and_close_jquery_dialog()

            if error_msg:
                if "加入購物車" in error_msg or "完成" in error_msg:
                    print(f">>> [系統] 🎉 恭喜！系統提示：【{error_msg}】")
                    self.is_seat_selected = True
                else:
                    print(f">>> [系統] 💥 系統彈窗攔截: 【{error_msg}】 (已自動點掉)")
                    self.is_seat_selected = False
                    base_wait = getattr(self, 'refresh_sec', 0.1)
                    try:
                        await self.tab.evaluate("window.location.reload();")
                    except:
                        pass
                    import asyncio
                    await asyncio.sleep(base_wait)

            else:
                if not getattr(self, 'is_seat_selected', False):
                    seat_success = await self.select_tickets()
                    if seat_success:
                        import asyncio
                        await asyncio.sleep(0.3)
                        ocr_success = await self.process_captcha()
                        if ocr_success:
                            await self.click_next()

    async def reload_settings(self, silent=False):
        """[寬宏售票] 從設定檔讀取最新搶票設定 (支援多重設定檔動態切換 + 磁碟 I/O 提速)"""
        import json
        import os

        # 🔥 核心修正：直接使用初始化時從 plg.py 接過來的正確路徑
        settings_path = getattr(self, 'settings_path', 'settings.json')

        try:
            if not os.path.exists(settings_path):
                return

            # 🔥 終極提速核心：檢查檔案修改時間，沒變過就不讀取硬碟，直接秒退！
            current_mtime = os.path.getmtime(settings_path)
            if getattr(self, 'last_settings_mtime', 0) == current_mtime:
                return
            self.last_settings_mtime = current_mtime

            with open(settings_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)

            # 同步更新各個區塊的設定
            if "area_auto_select" in new_config:
                self.config["area_auto_select"] = new_config["area_auto_select"]
            if "date_auto_select" in new_config:
                self.config["date_auto_select"] = new_config["date_auto_select"]
            if "advanced" in new_config:
                self.config["advanced"] = new_config["advanced"]
            if "keyword_exclude" in new_config:
                self.config["keyword_exclude"] = new_config["keyword_exclude"]
            if "ticket_number" in new_config:
                self.config["ticket_number"] = new_config["ticket_number"]
                self.ticket_number = int(new_config.get("ticket_number", 1))

            # 強制優先讀取 GUI 上的「重新整理間隔」
            if "advanced" in new_config and "auto_reload_page_interval" in new_config["advanced"]:
                self.refresh_sec = float(
                    new_config["advanced"]["auto_reload_page_interval"])
            elif "refresh_sec" in new_config:
                self.refresh_sec = float(new_config["refresh_sec"])

            if not silent:
                current_refresh = getattr(self, 'refresh_sec', 0.2)
                # 抓出純檔名，讓 Log 看起來乾淨俐落
                filename = os.path.basename(settings_path)
                print(
                    f">>> [系統] 寬宏售票已套用最新設定 [{filename}] (目標: {self.ticket_number} 張 | 失敗重整: {current_refresh} 秒)")

        except Exception as e:
            # print(f">>> [DEBUG] 寬宏 reload_settings 出錯: {e}")
            pass

    async def auto_login(self):
        """[核心] 寬宏售票：會說話的自動填表與 OCR 登入"""

        # 防呆提示：不要每 0.05 秒一直印
        if not getattr(self, 'is_printing_login', False):
            print(">>> [寬宏售票-登入] 進入登入頁面，準備填寫帳密與驗證碼...")
            self.is_printing_login = True

        # ==========================================
        # 🔥 核心修正：讀取寬宏專屬的帳號密碼！
        # ==========================================
        account = self.config.get("advanced", {}).get("kham_account", "")
        password = self.config.get("advanced", {}).get(
            "kham_password_plaintext", "").strip()

        if not password:
            try:
                import util
                password = util.decrypt_me(self.config.get(
                    "advanced", {}).get("kham_password", ""))
            except:
                pass

        if not account or not password:
            if not getattr(self, 'is_printing_no_acc', False):
                print(">>> [寬宏售票-登入] ⚠️ 未設定寬宏帳號密碼，請手動登入！")
                self.is_printing_no_acc = True
            return

        # 狀態機 JS 腳本：精準回報網頁現況
        js_fill_credentials = f"""
        (function() {{
            try {{
                let accInput = document.querySelector('#ACCOUNT');
                let pwdInput = document.querySelector('#PASSWORD');

                // 如果元素還沒生出來，回報 WAITING
                if (!accInput || !pwdInput) return "WAITING_DOM";

                // 如果是空的，執行填寫並回報 JUST_FILLED
                if (accInput.value === '') {{
                    accInput.value = '{account}';
                    pwdInput.value = '{password}';
                    accInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    pwdInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    pwdInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    pwdInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return "JUST_FILLED";
                }}

                // 如果已經填過了，回報 ALREADY_FILLED
                return "ALREADY_FILLED";
            }} catch(e) {{
                return "ERROR";
            }}
        }})();
        """

        try:
            status = await self.tab.evaluate(js_fill_credentials)

            # 只要帳密格子裡有字了 (剛填好 或 已經填好)，就發動 OCR 攻擊！
            if status == "JUST_FILLED" or status == "ALREADY_FILLED":
                if status == "JUST_FILLED":
                    print(">>> [寬宏售票-登入] 帳號密碼自動填寫完成！準備破解圖形驗證碼...")

                # 呼叫 OCR
                ocr_success = await self.process_captcha()

                # 如果 OCR 成功，點擊送出
                if ocr_success:
                    print(">>> [寬宏售票-登入] 驗證碼填入完畢，等待 0.5 秒確保網頁消化...")
                    import asyncio
                    await asyncio.sleep(0.5)

                    js_click_login = """
                    (function() {
                        let loginBtn = document.querySelector('button[onclick*="doLogin1"]');
                        if (loginBtn && !loginBtn.disabled) {
                            loginBtn.click();
                            return true;
                        }
                        return false;
                    })();
                    """
                    btn_clicked = await self.tab.evaluate(js_click_login)
                    if btn_clicked:
                        print(">>> [寬宏售票-登入] 👉 已自動點擊「送出」按鈕！")
                        self.is_login_done = True
                        self.is_printing_login = False  # 解開 Log 鎖，以防登入失敗退回還能重新印
                    else:
                        print(">>> [寬宏售票-登入] ⚠️ 找不到送出按鈕！")

        except Exception as e:
            print(f">>> [寬宏售票-登入] 過程發生錯誤: {e}")

    async def process_captcha(self):
        """[寬宏售票] 共用核心：處理圖形驗證碼"""
        print(">>> [OCR] 開始處理圖形驗證碼...")

        # 抓取寬宏驗證碼圖片 (#chk_pic)
        js_get_image = """
        (function() {
            var img = document.querySelector('#chk_pic');
            if (!img) return null;

            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || img.width;
            canvas.height = img.naturalHeight || img.height;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').split(',')[1];
        })();
        """

        try:
            # 最多嘗試辨識 3 次
            for attempt in range(3):
                base64_data = await self.tab.evaluate(js_get_image)
                if not base64_data:
                    print(">>> [OCR] 找不到驗證碼圖片 (#chk_pic)")
                    return False

                import base64
                img_bytes = base64.b64decode(base64_data)

                # 確保 ddddocr 已經成功載入
                if self.ocr:
                    ocr_answer = self.ocr.classification(img_bytes)
                    ocr_answer = ocr_answer.strip() if ocr_answer else ""
                else:
                    print(">>> [OCR] ddddocr 尚未初始化，無法辨識！")
                    return False

                print(f">>> [OCR] 第 {attempt + 1} 次辨識結果: '{ocr_answer}'")

                # 寬宏的驗證碼通常是 4 碼
                if len(ocr_answer) == 4:
                    js_fill_input = f"""
                    (function() {{
                        // 填入寬宏驗證碼輸入框 (#CHK)
                        var input = document.querySelector('#CHK');
                        if (input) {{
                            input.value = '{ocr_answer}';
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        return false;
                    }})();
                    """
                    is_filled = await self.tab.evaluate(js_fill_input)
                    if is_filled:
                        print(f">>> [OCR]  已自動填入驗證碼: {ocr_answer}")
                        return True
                    else:
                        print(">>> [OCR]  找不到驗證碼輸入框！")
                        return False
                else:
                    # 辨識失敗，點擊圖片換一張新的
                    print(">>> [OCR]  辨識長度不對，刷新圖片重試...")
                    js_refresh_img = "let img = document.querySelector('#chk_pic'); if(img) img.click();"
                    await self.tab.evaluate(js_refresh_img)
                    import asyncio
                    await asyncio.sleep(0.5)  # 給網頁時間載入新圖片

            return False

        except Exception as e:
            print(f">>> [OCR] 發生例外錯誤: {e}")
            return False

    async def select_date(self):
        """[寬宏售票] 場次/日期選擇 (泛用表格結構相容版)"""
        await self.reload_settings(silent=True)

        if not getattr(self, 'is_printing_date', False):
            print(">>> [寬宏售票-日期] 進入日期選擇頁面，等待場次表載入...")
            self.is_printing_date = True

        try:
            date_auto_select = self.config.get("date_auto_select", {})
            if not date_auto_select.get("enable", True):
                print(">>> [寬宏售票-日期] 設定檔未啟用，跳過。")
                return

            raw_keyword = date_auto_select.get("date_keyword", "").strip()
            import json
            keyword_list = []
            if len(raw_keyword) > 0:
                try:
                    if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                        keyword_list = json.loads(raw_keyword)
                    else:
                        keyword_list = json.loads("[" + raw_keyword + "]")
                except:
                    keyword_list = [raw_keyword]
            else:
                keyword_list = [""]

            js_keywords = json.dumps(keyword_list, ensure_ascii=False)
            js_mode = f"'{date_auto_select.get('mode', 'from top to bottom')}'"

            js_script = f"""
            (function() {{
                try {{
                    const keywords = {js_keywords};
                    const mode = {js_mode};

                    // 🔥 修正：不再強求 table 具備特定 class，直接抓取所有表格列
                    let rows = Array.from(document.querySelectorAll("table tbody tr"));
                    
                    if (rows.length === 0) return "WAITING_DOM"; 
                    if (rows.length === 1 && rows[0].innerText.includes('載入')) return "WAITING_DOM";

                    let candidates = [];

                    for (let row of rows) {{
                        // 防呆：如果是標題列 (th) 就直接跳過
                        if (row.querySelector('th')) continue;

                        let btn = row.querySelector("button");
                        if (!btn || btn.disabled) continue;

                        let btnText = btn.innerText || "";
                        if (btnText.includes('售完') || btnText.includes('額滿')) continue;
                        // 確保這個按鈕是我們想要的訂購按鈕
                        if (!btnText.includes('訂購') && !btnText.includes('購票')) continue;

                        let rowText = row.innerText.toUpperCase();
                        // 日期格式化：增加配對容錯率
                        let dateMatch = rowText.match(/(\\d{{4}})\\s*\\/\\s*(\\d{{2}})\\s*\\/\\s*(\\d{{2}})/);
                        if (dateMatch) {{
                            let y = dateMatch[1];
                            let m_str = dateMatch[2];
                            let d_str = dateMatch[3];
                            let m_int = parseInt(m_str, 10).toString();
                            let d_int = parseInt(d_str, 10).toString();
                            rowText += ` ${{y}}/${{m_str}}/${{d_str}} ${{y}}/${{m_int}}/${{d_int}} ${{m_str}}/${{d_str}} ${{m_int}}/${{d_int}} ${{m_str}}${{d_str}} ${{m_int}}月${{d_int}}日 ${{m_str}}月${{d_str}}日`;
                        }}

                        let isMatch = false;
                        if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                            isMatch = true;
                        }} else {{
                            for (let k of keywords) {{
                                let target_kws = k.trim().split(" ").filter(w => w.length > 0);
                                let currentGroupMatch = true;
                                for (let w of target_kws) {{
                                    if (!rowText.includes(w.toUpperCase())) {{
                                        currentGroupMatch = false;
                                        break;
                                    }}
                                }}
                                if (currentGroupMatch) {{
                                    isMatch = true;
                                    break;
                                }}
                            }}
                        }}

                        if (isMatch) {{
                            candidates.push(btn);
                        }}
                    }}

                    if (candidates.length === 0) return "RELOAD";

                    if (mode === "from bottom to top") {{
                        candidates.reverse();
                    }} else if (mode === "random") {{
                        for (let i = candidates.length - 1; i > 0; i--) {{
                            const j = Math.floor(Math.random() * (i + 1));
                            [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
                        }}
                    }}

                    candidates[0].click();
                    return "SUCCESS";

                }} catch (e) {{
                    return "ERROR|" + e.toString();
                }}
            }})();
            """

            result = await self.tab.evaluate(js_script)
            import asyncio

            if result == "SUCCESS":
                print(">>> [寬宏售票-日期] 🎉 成功匹配日期並執行點擊！")
                self.is_date_selected = True

            elif result == "WAITING_DOM":
                if not hasattr(self, 'date_wait_count'):
                    self.date_wait_count = 0
                self.date_wait_count += 1
                if self.date_wait_count % 10 == 0:
                    print(">>> [寬宏售票-日期] ⏳ 等待寬宏伺服器回傳場次資料... (網頁轉圈圈中)")
                await asyncio.sleep(0.05)

            elif result == "RELOAD":
                base_wait = getattr(self, 'refresh_sec', 0.2)
                if base_wait <= 0:
                    base_wait = 0.2

                print(f">>> [寬宏售票-日期] ⏳ 找不到符合關鍵字的場次或已售完，{base_wait} 秒後自動重整...")
                try:
                    await self.tab.evaluate("window.location.reload();")
                except:
                    pass
                await asyncio.sleep(base_wait)

            elif isinstance(result, str) and result.startswith("ERROR|"):
                print(f">>> [DEBUG] 日期選擇 JS 執行發生內部錯誤: {result}")

        except Exception as e:
            print(f">>> [嚴重錯誤] select_date 發生 Python 例外: {e}")

    async def select_area(self):
        """[寬宏售票] 區域選擇 (新版表格相容 + 防擋彈窗 + 隨機秒數重整)"""

        await self.reload_settings(silent=True)

        if not getattr(self, 'is_printing_area', False):
            print(">>> [系統] 進入寬宏售票區域選擇階段...")
            self.is_printing_area = True

        import asyncio
        await asyncio.sleep(0.15)

        try:
            area_auto_select = getattr(
                self, 'area_auto_select', self.config.get("area_auto_select", {}))
            if not area_auto_select.get("enable", True):
                print(">>> [寬宏售票-區域] 設定檔未啟用區域自動選擇，跳過。")
                return

            auto_select_mode = area_auto_select.get(
                "mode", "from top to bottom")
            raw_keyword = area_auto_select.get("area_keyword", "").strip()
            raw_keyword_exclude = self.config.get("keyword_exclude", "")
            if not raw_keyword_exclude:
                raw_keyword_exclude = area_auto_select.get(
                    "area_keyword_exclude", "")
            raw_keyword_exclude = str(raw_keyword_exclude).strip()

            import json

            def parse_keywords(kw_str):
                kw_str = kw_str.strip()
                if not kw_str:
                    return [""]
                try:
                    if kw_str.startswith("[") and kw_str.endswith("]"):
                        return json.loads(kw_str)
                    if '"' in kw_str or "'" in kw_str:
                        return json.loads("[" + kw_str + "]")
                except:
                    pass
                return [x.strip().strip('\'"') for x in kw_str.replace('，', ',').split(',') if x.strip()]

            keyword_list = parse_keywords(raw_keyword)
            exclude_list = parse_keywords(raw_keyword_exclude)

            js_keywords = json.dumps(keyword_list, ensure_ascii=False)
            js_excludes = json.dumps(exclude_list, ensure_ascii=False)
            js_mode = f"'{auto_select_mode}'"

            # 構建 寬宏售票專用 的 JavaScript 腳本
            js_script = f"""
            (function() {{
                try {{
                    // 偷偷攔截系統原生的 alert，防止點擊時被無意義的警告彈窗卡住
                    if (!window.khamHookedArea) {{
                        window.khamAlertMsgArea = "";
                        window.originalAlertArea = window.alert;
                        window.alert = function(msg) {{
                            window.khamAlertMsgArea = msg;
                        }};
                        window.khamHookedArea = true;
                    }}

                    const keywords = {js_keywords};
                    const excludes = {js_excludes};
                    const mode = {js_mode};

                    // 尋找所有狀態列 (寬宏新版的區域都是 tr.status_tr)
                    let rows = Array.from(document.querySelectorAll('tr.status_tr'));
                    let candidates = [];

                    if (rows.length > 0) {{
                        for (let row of rows) {{
                            // 1. 檢查空位狀態
                            let emptyTd = row.querySelector('td[data-title="空位："]');
                            if (!emptyTd) continue;
                            let emptyText = (emptyTd.innerText || "").trim().toUpperCase();
                            
                            // 如果空位寫著 0, 售完, 額滿，直接跳過這區
                            if (emptyText === '0' || emptyText.includes('售完') || emptyText.includes('額滿')) continue;

                            // 2. 獲取該區的文字內容並清理格式
                            let rowContent = (row.innerText || "").replace(/,/g, '').toUpperCase();
                            
                            // 預設排除身障席位 (除非關鍵字有明講)
                            let isHandicap = rowContent.includes('輪椅') || rowContent.includes('身障') || rowContent.includes('陪同');

                            // 3. 處理排除關鍵字
                            let isExcluded = false;
                            if (excludes.length > 0 && excludes[0] !== "") {{
                                for (let exc of excludes) {{
                                    let cleanExc = exc.trim().replace(/,/g, '').toUpperCase();
                                    if (cleanExc.length > 0 && rowContent.includes(cleanExc)) {{
                                        isExcluded = true; 
                                        break;
                                    }}
                                }}
                            }}
                            if (isExcluded) continue;

                            // 4. 處理包含關鍵字配對
                            let isMatch = false;
                            if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                                // 沒有設關鍵字：有票就當作候選！但自動排除身障席
                                if (!isHandicap) isMatch = true;
                            }} else {{
                                for (let k of keywords) {{
                                    let target_kws = k.trim().replace(/,/g, '').split(/\\s+/).filter(w => w.length > 0);
                                    let currentGroupMatch = true;
                                    for (let w of target_kws) {{
                                        // 價格容錯：例如使用者輸入 5600，但網頁是 5680，我們可以只比對前面數字
                                        // 這裡直接比對字串是否包含
                                        if (!rowContent.includes(w.toUpperCase())) {{
                                            currentGroupMatch = false; 
                                            break;
                                        }}
                                    }}
                                    if (currentGroupMatch) {{ 
                                        isMatch = true; 
                                        break; 
                                    }}
                                }}
                            }}

                            if (isMatch) {{
                                candidates.push(row);
                            }}
                        }}
                    }}

                    // 如果沒有任何候選區域有票，回報重整
                    if (candidates.length === 0) return "RELOAD";

                    // 5. 根據排序模式決定點擊哪一個
                    if (mode === "from bottom to top") {{
                        candidates.reverse();
                    }} else if (mode === "random") {{
                        for (let i = candidates.length - 1; i > 0; i--) {{
                            const j = Math.floor(Math.random() * (i + 1));
                            [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
                        }}
                    }}

                    let targetRow = candidates[0];
                    
                    // 點擊事件觸發
                    if (typeof jQuery !== 'undefined') {{
                        jQuery(targetRow).trigger('click');
                    }} else {{
                        targetRow.click();
                    }}

                    // 檢查點擊瞬間有沒有被系統彈窗擋下來 (例如秒殺被搶空)
                    if (window.khamAlertMsgArea !== "") {{
                        let msg = window.khamAlertMsgArea;
                        window.khamAlertMsgArea = ""; 
                        return "ALERT|" + msg;
                    }}

                    return "SUCCESS";

                }} catch(e) {{
                    return "ERROR|" + e.toString();
                }}
            }})();
            """

            result = await self.tab.evaluate(js_script)

            if result == "SUCCESS":
                print(f">>> [寬宏售票-區域] 🎉 成功匹配關鍵字並點擊空位區域！")
                await asyncio.sleep(0.5)
                self.is_area_selected = True

            elif isinstance(result, str) and result.startswith("ALERT|"):
                alert_msg = result.split("|")[1]
                print(f">>> [系統] ⚠️ 點擊區域時被系統攔截！訊息：【{alert_msg}】")
                print(">>> [系統] 準備重新整理尋找其他機會...")
                self.is_printing_area = False
                await self.tab.evaluate("window.location.reload();")
                await asyncio.sleep(0.5)

            elif result == "RELOAD":
                advanced_conf = self.config.get("advanced", {})
                base_wait = getattr(self, 'refresh_sec', 0.2)
                if base_wait <= 0:
                    base_wait = 0.2

                is_random = advanced_conf.get("auto_reload_random_mode", False)
                actual_wait = base_wait

                if is_random:
                    import random
                    try:
                        rand_range = float(advanced_conf.get(
                            "auto_reload_random_range", 1.0))
                    except:
                        rand_range = 1.0
                    actual_wait = round(
                        base_wait + random.uniform(0, rand_range), 2)

                print(
                    f">>> [寬宏售票-區域] ⏳ 找不到符合關鍵字或皆已售完，準備刷新... (等待 {actual_wait} 秒)")

                try:
                    await self.tab.evaluate("window.location.reload();")
                except:
                    pass
                await asyncio.sleep(actual_wait)

            elif isinstance(result, str) and result.startswith("ERROR|"):
                print(f">>> [DEBUG] 區域選擇 JS 執行發生內部錯誤: {result}")

        except Exception as e:
            print(f">>> [嚴重錯誤] select_area 發生 Python 例外: {e}")

    async def select_tickets(self):
        """[寬宏售票] 智能票數與座位選擇 (支援一般/座位圖雙模式 + 隨機秒數重整)"""
        ticket_num = self.ticket_number
        if ticket_num <= 0:
            return False

        js_select = f"""
        (function() {{
            try {{
                const targetTickets = {ticket_num};
                const seatTable = document.querySelector('#TBL');

                // ==========================================
                // 模式 2：座位圖模式 (有 #TBL)
                // ==========================================
                if (seatTable || window.location.href.toUpperCase().includes('UTK0205_')) {{

                    // A. 選擇票種 (尋找綠色按鈕，避開身障與陪同票)
                    let typeBtns = document.querySelectorAll('button.green');
                    let selectedBtn = null;
                    for (let btn of typeBtns) {{
                        let btnText = btn.innerText || "";
                        if (btnText.includes('身障') || btnText.includes('陪同') || btnText.includes('身心障礙')) continue;
                        selectedBtn = btn;
                        break;
                    }}
                    if (selectedBtn) selectedBtn.click();

                    // B. 尋找空座位 (優先找同行連號)
                    let rows = document.querySelectorAll('#TBL tbody tr');
                    let targetSeats = [];
                    for (let row of rows) {{
                        let cells = row.querySelectorAll('td');
                        let consec = [];
                        for (let cell of cells) {{
                            // 寬宏的空位 class 包含 empty
                            if (cell.classList.contains('empty')) {{
                                consec.push(cell);
                                if (consec.length === targetTickets) {{
                                    targetSeats = consec;
                                    break;
                                }}
                            }} else if (cell.classList.contains('people') || cell.innerHTML.includes('&nbsp;')) {{
                                // 遇到已售出或是走道，連號重新計算
                                consec = [];
                            }}
                        }}
                        if (targetSeats.length > 0) break;
                    }}

                    // 防呆：如果找不到連號，就硬抓剩下的所有散位
                    if (targetSeats.length === 0) {{
                        let allEmpty = Array.from(document.querySelectorAll('td.empty'));
                        if (allEmpty.length >= targetTickets) {{
                            targetSeats = allEmpty.slice(0, targetTickets);
                        }}
                    }}

                    // C. 點擊座位並聚焦驗證碼
                    if (targetSeats.length === targetTickets) {{
                        targetSeats.forEach(s => s.click());
                        let captchaInput = document.querySelector('#CHK');
                        if (captchaInput) captchaInput.focus();
                        return 1; // 成功
                    }} else {{
                        return 2; // 空位不足
                    }}
                }}

                // ==========================================
                // 模式 1：一般張數輸入模式 (沒有 #TBL)
                // ==========================================
                else {{
                    let rows = document.querySelectorAll('table tbody tr');
                    let targetInput = null;

                    for (let row of rows) {{
                        let labelCell = row.querySelector('td[data-th="內容："]');
                        if (labelCell) {{
                            let labelText = labelCell.innerText || "";
                            // 排除身障與陪同票
                            if (labelText.includes('身障') || labelText.includes('陪同') || labelText.includes('身心障礙')) continue;
                        }}

                        let input = row.querySelector('input.numbox[type="number"]');
                        if (input && !input.disabled) {{
                            targetInput = input;
                            break;
                        }}
                    }}

                    if (targetInput) {{
                        // 【關鍵】：先清空原本的 0，再填寫目標張數
                        targetInput.value = '';
                        targetInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        targetInput.value = targetTickets;

                        // 觸發寬宏的驗證腳本
                        targetInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        targetInput.dispatchEvent(new Event('change', {{ bubbles: true }}));

                        if (typeof checkNum === "function") {{
                            checkNum(targetInput);
                        }}

                        let captchaInput = document.querySelector('#CHK');
                        if (captchaInput) captchaInput.focus();
                        return 1; // 成功
                    }}
                    return 2; // 找不到可輸入的格子或已售完
                }}
            }} catch(e) {{
                return -1;
            }}
        }})();
        """

        try:
            result = await self.tab.evaluate(js_select)
            if result == 1:
                print(f">>> [座位/票數] 🎉 成功鎖定 {ticket_num} 張票！準備進行 OCR 辨識...")
                self.is_seat_selected = True
                return True

            elif result == 2:
                # ==========================================
                # 失敗重整邏輯 (結合隨機秒數)
                # ==========================================
                advanced_conf = self.config.get("advanced", {})
                base_wait = getattr(self, 'refresh_sec', 0.2)
                if base_wait <= 0:
                    base_wait = 0.2

                is_random = advanced_conf.get("auto_reload_random_mode", False)
                actual_wait = base_wait

                if is_random:
                    import random
                    try:
                        rand_range = float(advanced_conf.get(
                            "auto_reload_random_range", 1.0))
                    except:
                        rand_range = 1.0
                    actual_wait = round(
                        base_wait + random.uniform(0, rand_range), 2)

                print(
                    f">>> [座位/票數] ❌ 殘念...剩餘空位不足 {ticket_num} 張！準備刷新... (等待 {actual_wait} 秒)")

                import asyncio
                try:
                    await self.tab.evaluate("window.location.reload();")
                except:
                    pass
                await asyncio.sleep(actual_wait)
                return False

            elif result == -1:
                print(">>> [DEBUG] 選位 JS 執行發生內部錯誤")
                return False

        except Exception as e:
            print(f">>> [嚴重錯誤] select_tickets 發生例外: {e}")
        return False

    async def click_next(self):
        """[寬宏售票] 點擊加入購物車"""
        js_submit = """
        (function() {
            try {
                // 尋找帶有 addShoppingCart 函數的紅色按鈕
                let btn = document.querySelector('button[onclick*="addShoppingCart"]');

                if (btn && !btn.disabled) {
                    btn.click();
                    return true;
                }
                return false;
            } catch (e) {
                return false;
            }
        })();
        """
        try:
            result = await self.tab.evaluate(js_submit)
            if result:
                print(">>> [下一步] 🛒 已成功點擊「加入購物車」按鈕！")
                return True
        except:
            pass
        return False

    async def check_and_close_jquery_dialog(self):
        """[寬宏售票] 處理 jQuery UI 的錯誤彈窗，並擷取彈窗內的文字內容"""
        js_check_dialog = """
        (function() {
            try {
                // 尋找 jQuery UI 的底部按鈕
                let btn = document.querySelector('div.ui-dialog-buttonpane button');

                // 確認按鈕存在，且目前在畫面上是顯示狀態
                if (btn && btn.offsetParent !== null) {

                    // 將按鈕文字轉大寫去空白，擴大守備範圍
                    let btnText = (btn.innerText || "").trim().toUpperCase();

                    if (btnText.includes('OK') || btnText.includes('確定') || btnText.includes('確認') || btnText.includes('關閉')) {

                        // 往上尋找整個彈窗的父容器
                        let dialogBox = btn.closest('.ui-dialog');
                        let msgText = "未知的提示內容";

                        if (dialogBox) {
                            // 尋找 jQuery UI 存放文字內容的區塊
                            let contentNode = dialogBox.querySelector('.ui-dialog-content');
                            if (contentNode) {
                                msgText = contentNode.innerText.trim();
                            }
                        }

                        btn.click(); // 點擊關閉
                        return msgText; // 將抓到的文字回傳給 Python
                    }
                }
                return false;
            } catch (e) {
                return false;
            }
        })();
        """
        try:
            result = await self.tab.evaluate(js_check_dialog)
            # 如果回傳的是字串 (也就是有抓到彈窗)，Python 的 if 判斷會是 True
            if result:
                return result
        except:
            pass

        return False

    async def click_go_buy(self):
        """[寬宏售票] 第 1.5 階段：開賣前監控與狂點「我要購票」 (動態特徵抓取版)"""
        await self.reload_settings(silent=True)
        base_wait = getattr(self, 'refresh_sec', 0.2)
        if base_wait <= 0:
            base_wait = 0.2

        js_click = """
        (function() {
            try {
                // 攔截系統警告，避免「尚未開賣」的彈窗卡死程式
                if (!window.khamHookedPre) {
                    window.khamAlertMsgPre = "";
                    window.originalAlertPre = window.alert;
                    window.alert = function(msg) {
                        window.khamAlertMsgPre = msg;
                    };
                    window.khamHookedPre = true;
                }

                // 🔥 修正：不綁死 ID，改用特徵掃描尋找購票按鈕
                let targetBtn = null;
                let btns = document.querySelectorAll('button, a.btn, input[type="button"]');
                for (let b of btns) {
                    let txt = (b.innerText || b.value || "").replace(/\\s/g, "");
                    let onc = b.getAttribute("onclick") || "";
                    if (txt.includes("我要購票") || txt.includes("立即購票") || onc.includes("doSend")) {
                        targetBtn = b;
                        break;
                    }
                }

                if (targetBtn) {
                    targetBtn.click();
                    
                    // 檢查點擊後有沒有被系統罵「尚未開賣」
                    if (window.khamAlertMsgPre !== "") {
                        let msg = window.khamAlertMsgPre;
                        window.khamAlertMsgPre = "";
                        return "ALERT|" + msg;
                    }
                    return "CLICKED";
                }
                return "NOT_FOUND";
            } catch(e) {
                return "ERROR|" + e.toString();
            }
        })();
        """

        import asyncio
        try:
            result = await self.tab.evaluate(js_click)

            if result == "CLICKED":
                if not getattr(self, 'is_printing_gobuy', False):
                    print(">>> [寬宏售票] 🚀 找到「我要購票」按鈕，發動點擊！等待跳轉...")
                    self.is_printing_gobuy = True
                await asyncio.sleep(base_wait)

            elif isinstance(result, str) and result.startswith("ALERT|"):
                alert_msg = result.split("|")[1]
                if not getattr(self, 'is_printing_gobuy_alert', False):
                    print(f">>> [寬宏售票] ⏳ 系統提示：【{alert_msg}】，持續按設定的秒數重整搶進中...")
                    self.is_printing_gobuy_alert = True
                await self.tab.evaluate("window.location.reload();")
                await asyncio.sleep(base_wait)

            elif result == "NOT_FOUND":
                if not getattr(self, 'is_printing_gobuy_wait', False):
                    print(">>> [寬宏售票] ⏳ 尚未看到「我要購票」按鈕，持續重整監控中...")
                    self.is_printing_gobuy_wait = True
                await self.tab.evaluate("window.location.reload();")
                await asyncio.sleep(base_wait)

        except Exception as e:
            pass


# ==========================================
# [寬宏售票]
# ==========================================


class TicketPlusBot:
    """遠大售票 (TicketPlus) 專用機器人"""

    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        # 🔥 新增：從 config 拿取路徑，如果沒有就用預設的 settings.json
        self.settings_path = config.get("config_filepath", "settings.json")

        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        import os
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # 狀態鎖變數 (根據遠大的流程設定)
        self.is_login_done = False
        self.is_date_selected = False
        self.is_area_selected = False
        self.is_ticket_assigned = False
        self.is_next_clicked = False
        self.is_telegram_sent = False

        print(">>> [遠大售票] 正在載入 ddddocr 辨識模型...")
        import ddddocr
        self.ocr = ddddocr.DdddOcr(show_ad=False)

    async def reload_config_if_changed(self):
        """[動態更新] 檢查設定檔是否變更，若有則熱重載 (支援多重設定檔)"""
        import json
        import os
        try:
            # 🔥 修正：不再寫死 'settings.json'，改用初始化時存好的動態路徑
            config_path = getattr(self, 'settings_path', 'settings.json')

            if not os.path.exists(config_path):
                return

            mtime = os.path.getmtime(config_path)
            if not hasattr(self, "last_config_mtime"):
                self.last_config_mtime = mtime
                return

            if mtime > self.last_config_mtime:
                self.last_config_mtime = mtime

                # 從路徑中抓出純檔名，讓 Log 更清楚顯示是哪個檔案更新了
                filename = os.path.basename(config_path)
                print(f">>> [系統] 偵測到 {filename} 變更，正在熱重載最新戰術...")

                with open(config_path, "r", encoding="utf-8") as f:
                    new_config = json.load(f)

                # 同步更新各個區塊的設定
                if "area_auto_select" in new_config:
                    self.config["area_auto_select"] = new_config["area_auto_select"]
                if "date_auto_select" in new_config:
                    self.config["date_auto_select"] = new_config["date_auto_select"]
                if "advanced" in new_config:
                    self.config["advanced"] = new_config["advanced"]

                # 【關鍵新增】：把 GUI 產生在最外層的排除關鍵字也熱重載進來
                if "keyword_exclude" in new_config:
                    self.config["keyword_exclude"] = new_config["keyword_exclude"]

                if "ticket_number" in new_config:
                    self.config["ticket_number"] = new_config["ticket_number"]
                    self.ticket_number = int(
                        new_config.get("ticket_number", 1))

                print(f"    -> [更新] 遠大售票 ({filename}) 設定套用完畢！")
        except Exception as e:
            pass

    async def run(self):
        print(f">>> [遠大售票] 機器人啟動！(目標張數: {self.ticket_number})")
        print("等待網頁載入中...")

        import os
        import asyncio

        while True:
            try:
                # ==========================================
                # 1. 暫停攔截 (加入狀態提示)
                # ==========================================
                if os.path.exists(self.PAUSE_FILE):
                    if not getattr(self, 'is_printing_pause', False):
                        self.is_printing_pause = True
                    await asyncio.sleep(0.5)
                    continue
                else:
                    if getattr(self, 'is_printing_pause', False):
                        self.is_printing_pause = False

                # 2. 獲取網址
                current_url = await self.tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                upper_curr = current_url.upper()

                # 3. 允許核心搶票頁面進行熱重載 (隨時改張數/關鍵字)
                if '/ACTIVITY/' in upper_curr or '/ORDER/' in upper_curr:
                    await self.reload_config_if_changed()

                # 4. 檢測頁面切換與退回防呆解鎖
                if current_url != self.last_url:
                    print(f"偵測到頁面切換: {current_url}")

                    # 情況 A：如果退回首頁
                    if current_url == 'https://ticketplus.com.tw/':
                        self.is_date_selected = False
                        self.is_area_selected = False
                        self.is_ticket_assigned = False
                        self.is_next_clicked = False
                        self.is_telegram_sent = False

                    # 情況 B：如果退回日期選擇頁 (activity)
                    elif '/ACTIVITY/' in upper_curr and getattr(self, 'is_date_selected', False):
                        print(">>> [系統] 偵測到退回日期選擇頁，已重置日期鎖，準備重新掃描場次！")
                        self.is_date_selected = False
                        self.is_area_selected = False
                        self.is_ticket_assigned = False
                        self.is_next_clicked = False
                        self.is_telegram_sent = False

                    # 情況 C：如果從結帳頁退回選區/選票頁 (order)
                    elif '/ORDER/' in upper_curr and getattr(self, 'is_area_selected', False):
                        print(">>> [系統] 偵測到退回區域選擇頁，已重置相關鎖定，準備重新刷票！")
                        self.is_area_selected = False
                        self.is_ticket_assigned = False
                        self.is_next_clicked = False
                        self.is_telegram_sent = False

                    self.last_url = current_url

                # ==========================================
                # 🔥 5. 全域彈窗擊殺器 (Global Error Popup Killer)
                # ==========================================
                if '/ORDER/' in upper_curr:
                    js_kill_popup = """
                    (function() {
                        let popups = document.querySelectorAll('div[role="dialog"], .v-dialog');
                        for (let dialog of popups) {
                            if (dialog.offsetParent !== null) {
                                let text = dialog.innerText || "";
                                // 判斷是否為「購票失敗」、「售完」或「我知道了」等錯誤彈窗
                                if (text.includes('失敗') || text.includes('售完') || text.includes('我知道了')) {
                                    let btn = dialog.querySelector('button.primary') || 
                                              dialog.querySelector('button.primary-1') || 
                                              dialog.querySelector('button.v-btn') || 
                                              dialog.querySelector('button');
                                    if (btn) {
                                        btn.click();
                                        return true;
                                    }
                                }
                            }
                        }
                        return false;
                    })();
                    """
                    killed = await self.tab.evaluate(js_kill_popup)
                    if killed:
                        print(">>> [系統] 💥 攔截到「購票失敗/售完」彈窗！已點擊關閉，解除所有鎖定重新撿漏...")
                        # 這是最重要的：把所有進度鎖打回原形！
                        self.is_area_selected = False
                        self.is_ticket_assigned = False
                        self.is_next_clicked = False

                        # 稍微等一下彈窗消失動畫
                        await asyncio.sleep(0.3)

                        # 繼續這圈迴圈，它接下來就會走到 dispatch_action -> select_area -> 開始瘋狂點更新票數！

                # 6. 分發任務
                await self.dispatch_action(current_url)

            except Exception as e:
                pass

            await asyncio.sleep(0.05)

    async def dispatch_action(self, url):
        """遠大售票 任務分發中心"""
        lower_url = url.lower()

        # ==========================================
        # 0. 首頁自動登入 (https://ticketplus.com.tw/)
        # ==========================================
        # 遠大的首頁網址通常很乾淨，或者是結尾帶斜線
        if lower_url == 'https://ticketplus.com.tw' or lower_url == 'https://ticketplus.com.tw/':
            if not getattr(self, 'is_login_done', False):
                await self.auto_login()

        # ==========================================
        # 1. 第一階段：場次/日期選擇 (/activity/XXX)
        # ==========================================
        elif '/activity/' in lower_url:
            # 確保進入日期頁面時，後面的區域鎖都是解開的
            self.is_area_selected = False
            self.is_ticket_assigned = False

            if not getattr(self, 'is_date_selected', False):
                await self.select_date()

        # ==========================================
        # 2. 第二/三階段：區域選擇與票數分配 (/order/XXX/OOO)
        # ==========================================
        elif '/order/' in lower_url:

            # 第一關：選區並展開面板
            if not getattr(self, 'is_area_selected', False):
                await self.select_area()

            # 第二關：點擊 + 號分配票數
            elif not getattr(self, 'is_ticket_assigned', False):
                await self.assign_ticket_number()

            # 第三關：萬一前面沒點到下一步，這裡負責補刀；如果點過了，就乖乖等跳轉
            elif not getattr(self, 'is_next_clicked', False):
                await self.click_next()

        # ==========================================
        # 3. 結帳階段 (/confirm/ 或 /confirmseat/)
        # ==========================================
        elif '/confirm/' in lower_url or '/confirmseat/' in lower_url:
            # 確保在這裡不會觸發前幾關的鎖
            self.is_area_selected = True
            self.is_ticket_assigned = True

            await self.process_confirmation()

    async def auto_login(self):
        """[遠大售票] 自動填寫手機號碼與密碼並登入 (完美對應 Vue.js)"""

        # 1. 讀取設定檔的帳號密碼
        account = self.config.get("advanced", {}).get("ticketplus_account", "")
        password = self.config.get("advanced", {}).get(
            "ticketplus_password_plaintext", "").strip()

        if not password:
            try:
                import util
                password = util.decrypt_me(self.config.get(
                    "advanced", {}).get("ticketplus_password", ""))
            except:
                pass

        if not account or not password:
            print(">>> [遠大售票]  未設定帳號密碼，跳過自動登入！")
            self.is_login_done = True
            return

        # 2. 構建狀態機式 JS 腳本
        js_login_flow = f"""
        (function() {{
            try {{
                // A. 檢查是否已登入 (遠大登入後，cookie 會有包含 account 的 user 資訊)
                if (document.cookie.includes('%22account%22')) {{
                    return "LOGGED_IN";
                }}

                // B. 檢查密碼輸入框是否已出現 (判斷彈窗是否開著)
                let pwdInput = document.querySelector('input[type="password"]');
                let accInput = document.querySelector('input[placeholder="手機號碼 *"]');

                if (!pwdInput || pwdInput.offsetParent === null) {{
                    // 尚未開啟彈窗，尋找並點擊首頁右上角的登入頭像 (mdi-account)
                    let loginIcon = document.querySelector('i.mdi-account');
                    if (loginIcon) {{
                        let btn = loginIcon.closest('button');
                        if (btn) btn.click();
                    }} else {{
                        // RWD 手機版漢堡選單模式
                        let rwdBtns = document.querySelectorAll('div.drawerItem');
                        if (rwdBtns.length > 3) rwdBtns[3].click();
                    }}
                    return "WAIT_MODAL"; // 告訴 Python 等待彈窗動畫
                }}

                // C. 彈窗已開，開始瞬間填寫帳密
                if (accInput && pwdInput) {{
                    // 填入帳號 (手機號碼)
                    if (accInput.value !== '{account}') {{
                        accInput.value = '{account}';
                        accInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}

                    // 填入密碼
                    if (pwdInput.value !== '{password}') {{
                        pwdInput.value = '{password}';
                        pwdInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}

                    // D. 尋找登入按鈕並點擊 (Vuetify 的按鈕通常包含 '登入' 文字)
                    let btns = Array.from(document.querySelectorAll('button'));
                    let submitBtn = btns.find(b => b.innerText.includes('登入') && !b.disabled);

                    if (submitBtn) {{
                        submitBtn.click();
                        return "SUBMITTED";
                    }}
                    return "READY_TO_SUBMIT";
                }}
                return "WORKING";
            }} catch(e) {{
                return "ERROR";
            }}
        }})();
        """

        try:
            # 3. 執行 JS 並根據回傳狀態採取動作
            result = await self.tab.evaluate(js_login_flow)

            if result == "LOGGED_IN":
                print(">>> [遠大售票]  偵測到已登入狀態！")
                self.is_login_done = True

            elif result == "WAIT_MODAL":
                print(">>> [遠大售票] 正在開啟登入彈窗...")
                import asyncio
                await asyncio.sleep(0.5)  # 給 Vue.js 一點時間渲染彈窗

            elif result == "SUBMITTED":
                print(">>> [遠大售票]  帳密已填入，並點擊登入！等待伺服器驗證...")
                import asyncio
                await asyncio.sleep(1.0)  # 等待遠大 API 回傳登入成功

            elif result == "READY_TO_SUBMIT":
                print(">>> [遠大售票]  帳密已填，嘗試發送 Enter 鍵送出...")
                # 備用方案：透過 nodriver 原生指令對密碼框發送 Enter
                pwd_element = await self.tab.select('input[type="password"]')
                if pwd_element:
                    await pwd_element.send_keys('\n')
                import asyncio
                await asyncio.sleep(1.0)

            elif result == "ERROR":
                pass

        except Exception as e:
            print(f">>> [嚴重錯誤] auto_login 發生 Python 例外: {e}")

    async def select_date(self):
        """[遠大售票] 場次/日期選擇 (支援彈窗自動擊殺與 CDP 實體點擊)"""

        print(">>> [系統] 進入遠大售票日期/場次選擇階段...")

        try:
            date_auto_select = self.config.get("date_auto_select", {})
            if not date_auto_select.get("enable", True):
                return

            auto_select_mode = date_auto_select.get(
                "mode", "from top to bottom")
            raw_keyword = date_auto_select.get("date_keyword", "").strip()

            import json
            keyword_list = []
            if len(raw_keyword) > 0:
                try:
                    if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                        keyword_list = json.loads(raw_keyword)
                    else:
                        keyword_list = json.loads("[" + raw_keyword + "]")
                except:
                    keyword_list = [raw_keyword]
            else:
                keyword_list = [""]

            js_keywords = json.dumps(keyword_list, ensure_ascii=False)
            js_mode = f"'{auto_select_mode}'"

            # 構建遠大專用 JS 腳本
            js_script = f"""
            (function() {{
                try {{
                    // ==========================================
                    // A. 彈窗擊殺系統 (清除實名制同意、廣告遮罩)
                    // ==========================================
                    let popups = document.querySelectorAll('div[role="dialog"]');
                    popups.forEach(dialog => {{
                        if (dialog.offsetParent !== null) {{
                            // 尋找主要的確定/同意/關閉按鈕
                            let primaryBtn = dialog.querySelector('button.primary') || dialog.querySelector('button.primary-1') || dialog.querySelector('button');
                            if (primaryBtn) primaryBtn.click();
                        }}
                    }});

                    // ==========================================
                    // B. Vue.js 載入狀態防呆
                    // ==========================================
                    let loader = document.querySelector('.v-progress-circular');
                    if (loader && loader.offsetParent !== null) {{
                        return "LOADING"; // 還在轉圈圈，通知 Python 等待
                    }}

                    // ==========================================
                    // C. 掃描場次並進行標記 (Mark)
                    // ==========================================
                    const keywords = {js_keywords};
                    const mode = {js_mode};

                    // 鎖定遠大的場次列
                    let rows = Array.from(document.querySelectorAll('div#buyTicket div.sesstion-item div.row'));
                    let candidates = [];

                    if (rows.length > 0) {{
                        for (let row of rows) {{
                            let rowText = row.innerText.toUpperCase();
                            let btn = row.querySelector('button');

                            // 過濾掉沒按鈕、按鈕反灰、或是文字顯示銷售一空的場次
                            if (!btn || btn.disabled) continue;
                            if (!btn.innerText.includes('立即購')) continue;
                            if (rowText.includes('銷售一空')) continue;

                            // 關鍵字比對
                            let isMatch = false;
                            if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                                isMatch = true;
                            }} else {{
                                for (let k of keywords) {{
                                    let target_kws = k.trim().split(" ").filter(w => w.length > 0);
                                    let currentGroupMatch = true;
                                    for (let w of target_kws) {{
                                        if (!rowText.includes(w.toUpperCase())) {{
                                            currentGroupMatch = false; break;
                                        }}
                                    }}
                                    if (currentGroupMatch) {{ isMatch = true; break; }}
                                }}
                            }}

                            if (isMatch) candidates.push(btn);
                        }}
                    }}

                    if (candidates.length === 0) return "NO_TICKETS";

                    // 排序機制
                    if (mode === "from bottom to top") {{
                        candidates.reverse();
                    }} else if (mode === "random") {{
                        for (let i = candidates.length - 1; i > 0; i--) {{
                            const j = Math.floor(Math.random() * (i + 1));
                            [candidates[i], candidates[j]] = [
                                candidates[j], candidates[i]];
                        }}
                    }}

                    // 賦予動態 ID 並捲動至畫面中央
                    let target = candidates[0];
                    let uniqueId = 'maxbot_target_' + Date.now();
                    target.id = uniqueId;
                    target.scrollIntoView(
                        {{ behavior: 'instant', block: 'center' }});

                    return uniqueId;

                }} catch(e) {{
                    return "ERROR";
                }}
            }})();
            """

            # 執行 JS
            result = await self.tab.evaluate(js_script)

            if isinstance(result, str) and result.startswith("maxbot_target_"):
                print(f">>> [遠大售票-日期] 🎯 成功鎖定場次！發動 CDP 實體點擊...")
                target_element = await self.tab.select(f'#{result}')
                if target_element:
                    await target_element.click()

                import asyncio
                await asyncio.sleep(0.5)  # 給網頁跳轉時間
                self.is_date_selected = True

            elif result == "LOADING":
                # 還在轉圈圈，稍微等一下，下次迴圈再試，不需要重整
                import asyncio
                await asyncio.sleep(0.1)

            elif result == "NO_TICKETS":
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))
                if base_wait <= 0:
                    base_wait = 0.2

                print(">>> [遠大售票-日期] 找不到符合的場次或尚未開賣，準備刷新...")
                import asyncio
                await self.tab.reload()
                print(f"    -> 刷新後固定等待: {base_wait} 秒")
                await asyncio.sleep(base_wait)

            elif result == "ERROR":
                print(">>> [DEBUG] 日期選擇 JS 執行發生內部錯誤")

        except Exception as e:
            print(f">>> [嚴重錯誤] select_date 發生 Python 例外: {e}")

    async def select_area(self):
        """[遠大售票] 區域選擇 (單純鎖定關鍵字 + 極速點擊更新票數防禦)"""
        import json
        import asyncio

        try:
            area_auto_select = getattr(
                self, 'area_auto_select', self.config.get("area_auto_select", {}))
            if not area_auto_select.get("enable", True):
                return

            auto_select_mode = area_auto_select.get(
                "mode", "from top to bottom")
            raw_keyword = area_auto_select.get("area_keyword", "").strip()
            raw_keyword_exclude = self.config.get("keyword_exclude", "")
            if not raw_keyword_exclude:
                raw_keyword_exclude = area_auto_select.get(
                    "area_keyword_exclude", "")
            raw_keyword_exclude = str(raw_keyword_exclude).strip()

            def parse_keywords(kw_str):
                kw_str = kw_str.strip()
                if not kw_str:
                    return [""]
                try:
                    if kw_str.startswith("[") and kw_str.endswith("]"):
                        return json.loads(kw_str)
                    if '"' in kw_str or "'" in kw_str:
                        return json.loads("[" + kw_str + "]")
                except:
                    pass
                return [x.strip().strip('\'"') for x in kw_str.replace('，', ',').split(',') if x.strip()]

            keyword_list = parse_keywords(raw_keyword)
            exclude_list = parse_keywords(raw_keyword_exclude)

            js_keywords = json.dumps(keyword_list, ensure_ascii=False)
            js_excludes = json.dumps(exclude_list, ensure_ascii=False)
            js_mode = f"'{auto_select_mode}'"

            # 這是你原本乾淨的 JS 腳本，完全保留
            js_script = f"""
                (function() {{
                    try {{
                        let popups = document.querySelectorAll('div[role="dialog"]');
                        let isErrorPopup = false;
                        popups.forEach(dialog => {{
                            if (dialog.offsetParent !== null) {{
                                let text = dialog.innerText || "";
                                if (text.includes('失敗') || text.includes('售完') || text.includes('限制')) {{
                                    isErrorPopup = true;
                                }}
                                let btn = dialog.querySelector('button.primary') || dialog.querySelector('button.primary-1') || dialog.querySelector('button.v-btn');
                                if (btn) btn.click();
                            }}
                        }});

                        if (isErrorPopup) return "ERROR_POPUP";

                        let loader = document.querySelector('.v-progress-circular');
                        if (loader && loader.offsetParent !== null) return "LOADING";

                        const keywords = {js_keywords};
                        const excludes = {js_excludes};
                        const mode = {js_mode};

                        let rows = Array.from(document.querySelectorAll('.v-expansion-panel'));
                        if (rows.length === 0) {{
                            rows = Array.from(document.querySelectorAll('.price-group > div, div.rwd-margin'));
                        }}

                        let candidates = [];

                        for (let row of rows) {{
                            let header = row.querySelector('.v-expansion-panel-header');
                            let evaluateEl = header ? header : row;

                            let rawText = evaluateEl.textContent || evaluateEl.innerText || "";
                            let rowText = rawText.toUpperCase().replace(/,/g, '');
                            let rowHtml = evaluateEl.innerHTML.toLowerCase();

                            // 區域賣光或沒位子，跳過不加進名單
                            if (rowText.includes('已售完') || rowText.includes('剩餘 0') || rowText.includes('剩餘：0') || rowHtml.includes('soldout')) {{
                                continue;
                            }}

                            let isExcluded = false;
                            if (excludes.length > 0 && excludes[0] !== "") {{
                                for (let exc of excludes) {{
                                    let cleanExc = exc.trim().toUpperCase().replace(/,/g, '');
                                    if (cleanExc.length > 0 && rowText.includes(cleanExc)) {{
                                        isExcluded = true; break;
                                    }}
                                }}
                            }}
                            if (isExcluded) continue;

                            let isMatch = false;
                            if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) {{
                                isMatch = true;
                            }} else {{
                                for (let k of keywords) {{
                                    let target_kws = k.trim().split(/\s+/).filter(w => w.length > 0);
                                    let currentGroupMatch = true;
                                    for (let w of target_kws) {{
                                        let cleanW = w.toUpperCase().replace(/,/g, '');
                                        if (!rowText.includes(cleanW)) {{
                                            currentGroupMatch = false; break;
                                        }}
                                    }}
                                    if (currentGroupMatch) {{ isMatch = true; break; }}
                                }}
                            }}

                            if (isMatch) candidates.push(evaluateEl);
                        }}

                        // 🔥 如果名單是空的（找不到區域，或區域沒辦法買），回傳 NO_TICKETS
                        if (candidates.length === 0) return "NO_TICKETS";

                        if (mode === "from bottom to top") {{
                            candidates.reverse();
                        }} else if (mode === "random") {{
                            for (let i = candidates.length - 1; i > 0; i--) {{
                                const j = Math.floor(Math.random() * (i + 1));
                                [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
                            }}
                        }}

                        let targetElement = candidates[0];
                        let rawTargetText = targetElement.textContent || targetElement.innerText || "";
                        let targetName = rawTargetText.replace(/\s+/g, ' ').trim();

                        if (targetElement.classList.contains('v-expansion-panel-header')) {{
                            if (targetElement.getAttribute('aria-expanded') === 'true') {{
                                return "ALREADY_EXPANDED|" + targetName;
                            }}
                        }}

                        let uniqueId = 'maxbot_target_' + Date.now();
                        targetElement.id = uniqueId;
                        targetElement.scrollIntoView({{ behavior: 'instant', block: 'center' }});

                        return uniqueId + "|" + targetName;

                    }} catch(e) {{
                        return "ERROR";
                    }}
                }})();
            """

            result = await self.tab.evaluate(js_script)

            if isinstance(result, str) and result.startswith("maxbot_target_"):
                parts = result.split("|", 1)
                target_id = parts[0]
                area_name = parts[1] if len(parts) > 1 else "未知區域"
                self.current_area_name = area_name
                print(f">>> [遠大售票-區域] 🎯 鎖定票區：【{area_name}】，點擊展開面板...")

                target_element = await self.tab.select(f'#{target_id}')
                if target_element:
                    await target_element.click()

                await asyncio.sleep(0.3)
                self.is_area_selected = True

            elif isinstance(result, str) and result.startswith("ALREADY_EXPANDED"):
                parts = result.split("|", 1)
                area_name = parts[1] if len(parts) > 1 else "未知區域"
                self.current_area_name = area_name
                print(f">>> [遠大售票-區域] 🎯 票區：【{area_name}】 已展開！進入張數檢查...")
                self.is_area_selected = True

            elif result == "LOADING":
                await asyncio.sleep(0.1)

            elif result == "ERROR_POPUP":
                print(f">>> [系統] ⚠️ 發現錯誤彈窗！已關閉並準備重整...")
                self.is_area_selected = False
                self.is_ticket_assigned = False
                await self.tab.reload()
                await asyncio.sleep(0.5)

            # ==========================================
            # 🔥 關鍵修改：找不到區域或無法點選時，全面改用「點擊更新票數」
            # ==========================================
            elif result == "NO_TICKETS":
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))
                if base_wait <= 0:
                    base_wait = 0.2

                # 加入計數器避免終端機被洗頻
                if not hasattr(self, 'refresh_log_count'):
                    self.refresh_log_count = 0
                self.refresh_log_count += 1

                if self.refresh_log_count % 3 == 0:
                    print(">>> [遠大售票-區域] ♻️ 找不到指定區域或皆已售完，持續點擊「更新票數」極速撿漏中...")

                # 暴力尋找並點擊「更新票數」按鈕
                js_refresh = """
                    (function() {
                        try {
                            let refreshBtn = null;
                            let spans = Array.from(document.querySelectorAll('span'));
                            for (let span of spans) {
                                if (span.textContent && span.textContent.includes('更新票數')) {
                                    refreshBtn = span.closest('button') || span.closest('.v-btn') || span;
                                    break;
                                }
                            }
                            if (!refreshBtn) {
                                let btns = Array.from(document.querySelectorAll('button, .v-btn'));
                                refreshBtn = btns.find(b => (b.innerText && b.innerText.includes('更新票數')) ||
                                                            (b.textContent && b.textContent.includes('更新票數')));
                            }
                            
                            if (refreshBtn && !refreshBtn.disabled) {
                                refreshBtn.click();
                                return true;
                            }
                            return false;
                        } catch(e) { return false; }
                    })();
                """
                try:
                    is_btn_clicked = await self.tab.evaluate(js_refresh)
                    if not is_btn_clicked:
                        # 只有在畫面上真的連更新按鈕都沒有的時候，才迫不得已按 F5 重新整理
                        if self.refresh_log_count % 3 == 0:
                            print("    -> ⚠️ 畫面上沒有「更新票數」按鈕，執行完整網頁重整 (F5)...")
                        await self.tab.reload()
                except Exception:
                    try:
                        await self.tab.reload()
                    except:
                        pass

                await asyncio.sleep(base_wait)

        except Exception as e:
            pass

    async def assign_ticket_number(self):
        """[遠大售票] 分配票數 (新增：若無按鈕則點擊更新票數刷新)"""

        js_script = f"""
        (function() {{
            try {{
                const targetTickets = {self.ticket_number};

                let activePanels = document.querySelectorAll('.v-expansion-panel--active');
                let activePanel = activePanels.length > 0 ? activePanels[0] : document;

                let countDiv = activePanel.querySelector('div.count-button > div:nth-child(2)');
                let plusBtnIcon = activePanel.querySelector('i.mdi-plus');

                // ==========================================
                // 🔥 無敵邏輯：找不到 + 號按鈕，代表還沒開賣！
                // ==========================================
                if (!countDiv || !plusBtnIcon) {{
                    
                    // 尋找「更新票數」按鈕並點擊
                    let refreshBtn = null;
                    let spans = Array.from(document.querySelectorAll('span'));
                    for (let span of spans) {{
                        if (span.textContent && span.textContent.includes('更新票數')) {{
                            refreshBtn = span.closest('button') || span.closest('.v-btn') || span;
                            break;
                        }}
                    }}
                    if (!refreshBtn) {{
                        let btns = Array.from(document.querySelectorAll('button, .v-btn'));
                        refreshBtn = btns.find(b => (b.innerText && b.innerText.includes('更新票數')) ||
                                                    (b.textContent && b.textContent.includes('更新票數')));
                    }}
                    
                    if (refreshBtn && !refreshBtn.disabled) {{
                        refreshBtn.click();
                        return "REFRESH_CLICKED"; // 告訴 Python 我們按了更新
                    }}

                    return "NOT_READY"; // 連更新按鈕都沒有，只能乾等
                }}

                // ==========================================
                // 找到 + 號了，開始正常選票流程！
                // ==========================================
                let actualBtn = plusBtnIcon.closest('button');
                if (!actualBtn) return "NOT_READY";

                let currentCount = parseInt(countDiv.innerText) || 0;

                if (currentCount >= targetTickets) return "DONE";
                if (actualBtn.disabled) return "DISABLED";

                let diff = targetTickets - currentCount;

                let uniqueId = 'maxbot_plus_' + Date.now();
                actualBtn.id = uniqueId;

                return uniqueId + "|" + diff;

            }} catch(e) {{
                return "ERROR";
            }}
        }})();
        """

        try:
            result = await self.tab.evaluate(js_script)

            if isinstance(result, str) and result.startswith("maxbot_plus_"):
                parts = result.split("|")
                target_id = parts[0]
                clicks_needed = int(parts[1]) if len(parts) > 1 else 1

                target_element = await self.tab.select(f'#{target_id}')
                if target_element:
                    area_name = getattr(self, 'current_area_name', '該區域')
                    print(
                        f">>> [遠大售票-票數] 將對【 {area_name} 】連點 {clicks_needed} 下...")

                    import asyncio
                    for _ in range(clicks_needed):
                        await target_element.click()
                        await asyncio.sleep(0.02)

                print(f">>> [遠大售票-票數]  張數分配完畢！光速進入下一步...")
                self.is_ticket_assigned = True
                await self.click_next()

            elif result == "DONE":
                self.is_ticket_assigned = True
                await self.click_next()

            # ==========================================
            # 🔥 處理剛剛發動的「更新票數」動作
            # ==========================================
            elif result == "REFRESH_CLICKED":
                # 為了避免 Log 洗頻，設定計數器
                if not hasattr(self, 'refresh_log_count'):
                    self.refresh_log_count = 0
                self.refresh_log_count += 1
                if self.refresh_log_count % 3 == 0:
                    print(f">>> [遠大售票-票數] ⏳ 面板已展開但無法選位！持續點擊「更新票數」刷新狀態中...")

                import asyncio
                # 給網頁 0.3 秒載入新資料，is_ticket_assigned 維持 False，下次迴圈再來檢查！
                await asyncio.sleep(0.3)

            elif result == "DISABLED":
                print(f">>> [遠大售票-票數]  剩餘空位不足或達到購買上限！繼續結帳...")
                self.is_ticket_assigned = True
                await self.click_next()

            elif result == "NOT_READY":
                import asyncio
                await asyncio.sleep(0.1)

        except Exception as e:
            pass

    async def click_next(self):
        """[遠大售票] 填寫問答題/專屬碼 並 點選下一步"""

        # 1. 從設定檔讀取答案 (user_guess_string)
        raw_answers = self.config.get("advanced", {}).get(
            "user_guess_string", "").strip()

        import json
        ans_list = []
        if raw_answers:
            try:
                # 處理類似 "\"D17844109\",\"650\"" 的字串
                if raw_answers.startswith("[") and raw_answers.endswith("]"):
                    ans_list = json.loads(raw_answers)
                elif '"' in raw_answers or "'" in raw_answers:
                    ans_list = json.loads("[" + raw_answers + "]")
                else:
                    ans_list = [x.strip()
                                for x in raw_answers.split(",") if x.strip()]
            except:
                pass

        # 取得第一個答案作為主要填寫內容
        target_answer = ans_list[0] if len(ans_list) > 0 else ""

        js_next = f"""
        (function() {{
            try {{
                // ==========================================
                // 1. 問答題 / 專屬購票碼 擊殺系統
                // ==========================================
                // 利用 placeholder 鎖定目標，無視 Vuetify 的動態 ID
                let answerInput = document.querySelector('input[placeholder="答案選項"]') ||
                                  document.querySelector('input[placeholder*="專屬"]') ||
                                  document.querySelector(
                                      '.exclusive-code input[type="text"]');

                if (answerInput && !answerInput.disabled && answerInput.value === '') {{
                    answerInput.value = '{target_answer}';

                    // 喚醒 Vue.js 的雙向綁定，讓它意識到我們填字了
                    answerInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    answerInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}

                // ==========================================
                // 2. 尋找下一步按鈕並點擊
                // ==========================================
                let nextBtn = document.querySelector('button.nextBtn');
                if (nextBtn && !nextBtn.disabled) {{
                    nextBtn.click();
                    return true;
                }}
                return false;
            }} catch(e) {{
                return false;
            }}
        }})();
        """
        try:
            result = await self.tab.evaluate(js_next)
            if result:
                print(
                    f">>> [遠大售票-下一步] 🚀 已填入答案【 {target_answer} 】並點擊「下一步」！準備進入結帳...")
                self.is_next_clicked = True  # 扣上防連點鎖
                import asyncio
                await asyncio.sleep(0.5)  # 給網頁跳轉時間
                return True
        except:
            pass
        return False

    async def process_confirmation(self):
        """[遠大售票] 結帳頁面處理：利用倒數計時器確認搶到票，自動打勾並發送通知"""

        js_confirm = """
        (function() {
            try {
                // 1. 檢查倒數計時器是否存在 (這是確定搶到票的鐵證)
                let timer = document.querySelector('.timer');
                if (!timer || !timer.innerText.includes('完成購票手續')) {
                    return false; // 還沒看到計時器，代表還在載入或沒搶到
                }

                // 2. 尋找同意條款的 Checkbox 並打勾
                let checkbox = document.querySelector('input[type="checkbox"]');
                if (checkbox && !checkbox.checked) {
                    let wrapper = checkbox.closest('.v-input--selection-controls__input') || checkbox.closest('label') || checkbox;
                    wrapper.click();
                }

                return true; // 成功看到計時器，回傳 True 讓 Python 發通知
            } catch(e) {
                return false;
            }
        })();
        """

        try:
            is_checkout_ready = await self.tab.evaluate(js_confirm)

            # 如果偵測到計時器 (is_checkout_ready 為 True)，且還沒發送過 Telegram，就發送！
            if is_checkout_ready and not getattr(self, 'is_telegram_sent', False):
                self.is_telegram_sent = True  # 上鎖，避免迴圈狂發

                print("\n=======================================================")
                print(">>> [遠大售票-結帳] 💳 偵測到結帳倒數計時器！已自動勾選同意條款！")
                print(">>> [遠大售票-結帳] ⚠️ 請盡速手動確認後續付款流程！")
                print("=======================================================\n")

                # 組合精美的通知訊息
                area_name = getattr(self, 'current_area_name', '未知的神祕區域')
                ticket_num = self.ticket_number
                msg = f"🎉 <b>遠大售票 搶票成功！</b>\n\n系統已成功鎖定座位並進入結帳倒數！\n🎟️ <b>目標區域：</b>{area_name}\n🎫 <b>成功張數：</b>{ticket_num} 張\n\n⚠️ <b>請盡速回電腦前完成付款手續！</b>"

                await self.send_telegram_message(msg)

        except Exception as e:
            pass

    async def send_telegram_message(self, message):
        """[遠大售票] 發送 Telegram 通知 (非阻塞背景發送版)"""

        # 1. 檢查設定是否存在且啟用
        if not self.config or "advanced" not in self.config:
            return
        if not self.config["advanced"].get("telegram_enable", False):
            return

        bot_token = self.config["advanced"].get("telegram_bot_token", "")
        chat_id = self.config["advanced"].get("telegram_chat_id", "")

        if not bot_token or not chat_id:
            print(">>> [系統] ⚠️ Telegram 設定不完整，跳過通知")
            return

        # 2. 定義發送任務
        def _send():
            import requests
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, data=payload, timeout=6)
                if response.status_code == 200:
                    print(">>> [系統] 📱 Telegram 搶票成功通知發送成功！")
                else:
                    print(f">>> [系統] ❌ Telegram 發送失敗: {response.text}")
            except Exception as e:
                print(f">>> [系統] ❌ Telegram 連線錯誤: {e}")

        # 3. 將 requests 丟到背景執行，絕對不卡死 nodriver 主執行緒
        import asyncio
        asyncio.create_task(asyncio.to_thread(_send))

# ==========================================
# [遠大售票]
# ==========================================


class KKTIXBot:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        self.settings_path = config.get("config_filepath", "settings.json")

        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        import os
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # ==========================================
        # KKTIX 專屬狀態鎖
        # ==========================================
        self.is_printing_pause = False
        self.is_login_done = False
        self.is_event_next_clicked = False  # 活動首頁的「立即購票」按鈕鎖
        self.is_ticket_assigned = False     # 區域與張數分配鎖
        self.is_terms_agreed = False        # 同意條款打勾鎖
        self.is_captcha_solved = False      # 驗證碼/問答題鎖
        self.is_reg_next_clicked = False    # 購票頁面的「下一步」鎖
        self.is_telegram_sent = False
        self.has_seen_spinner = False
        self.is_printing_spinner = False

        print(">>> [KKTIX] 正在載入 ddddocr 辨識模型...")
        try:
            import ddddocr
            self.ocr = ddddocr.DdddOcr(show_ad=False)
        except Exception as e:
            print(f">>> [系統] ddddocr 載入失敗: {e}")
            self.ocr = None

    async def run(self):
        print(f">>> [KKTIX] 機器人啟動！(目標張數: {self.ticket_number})")
        print("等待網頁載入中...")

        import os
        import asyncio

        while True:
            try:
                # 1. 暫停攔截
                if os.path.exists(self.PAUSE_FILE):
                    if not getattr(self, 'is_printing_pause', False):
                        self.is_printing_pause = True
                    await asyncio.sleep(0.5)
                    continue
                else:
                    if getattr(self, 'is_printing_pause', False):
                        self.is_printing_pause = False

                # 2. 獲取網址
                current_url = await self.tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                upper_curr = current_url.upper()

                # 3. 檢測頁面切換與退回防呆解鎖
                if current_url != self.last_url:
                    print(f"偵測到頁面切換: {current_url}")

                    if '/EVENTS/' in upper_curr and '/REGISTRATIONS/' not in upper_curr:
                        print(">>> [系統] 退回或進入活動頁面，解鎖所有購票狀態！")
                        self.is_event_next_clicked = False
                        self.is_ticket_assigned = False
                        self.is_terms_agreed = False
                        self.is_captcha_solved = False
                        self.is_reg_next_clicked = False
                        self.is_telegram_sent = False
                        self.has_seen_spinner = False

                        await self.reload_settings()

                    elif '/REGISTRATIONS/' in upper_curr and upper_curr.endswith('/NEW'):
                        print(">>> [系統] 偵測到進入選票頁面，解鎖填表狀態！")
                        self.is_ticket_assigned = False
                        self.is_terms_agreed = False
                        self.is_captcha_solved = False
                        self.is_reg_next_clicked = False
                        self.is_telegram_sent = False
                        self.has_seen_spinner = False

                    self.last_url = current_url

                # ==========================================
                # 【樣態 2】攔截彈窗 (內部已包含解鎖與重整機制)
                # ==========================================
                has_popup = await self.check_and_close_popups()
                if has_popup:
                    base_wait = getattr(self, 'refresh_sec', 0.2)
                    if base_wait <= 0:
                        base_wait = 0.2
                    await asyncio.sleep(base_wait)
                    continue

                # 5. 分發任務
                await self.dispatch_action(current_url)

            except Exception as e:
                pass

            await asyncio.sleep(0.05)

    async def dispatch_action(self, url):
        """KKTIX 任務分發中心"""
        lower_url = url.lower()

        # ==========================================
        # 🔥 核心新增：訂單靜默鎖定與解除機制
        # ==========================================
        if getattr(self, 'is_order_locked', False):
            # 檢查網址是否已經退回到「活動首頁」或「選張數/問答頁面」
            if ('/events/' in lower_url and '/registrations/' not in lower_url) or \
               ('/registrations/' in lower_url and lower_url.endswith('/new')):
                print("\n>>> [系統] 偵測到返回活動/選票頁面，解除訂單靜默鎖，機器人重新啟動！\n")

                # 解鎖！
                self.is_order_locked = False

                # 順便把先前的選票狀態全部清空，讓機器人可以乾淨地進行下一輪搶票
                self.is_ticket_assigned = False
                self.is_terms_agreed = False
                self.is_captcha_solved = False
                self.is_reg_next_clicked = False
                self.is_event_next_clicked = False
                self.is_telegram_sent = False
            else:
                # 如果還在結帳頁面，直接 return，讓機器人繼續安靜待命
                return

        # ==========================================
        # 以下維持您原本的分發邏輯...
        # ==========================================
        if '/users/sign_in' in lower_url:
            if not getattr(self, 'is_login_done', False):
                await self.auto_login()

        elif '/events/' in lower_url and '/registrations/' not in lower_url:
            if not getattr(self, 'is_event_next_clicked', False):
                await self.click_event_next()

        elif '/registrations/' in lower_url:
            if lower_url.endswith('/new'):
                if not getattr(self, 'is_ticket_assigned', False) or not getattr(self, 'is_terms_agreed', False):
                    await self.assign_ticket_number()
                elif not getattr(self, 'is_captcha_solved', False):
                    await self.solve_kktix_question()
                elif not getattr(self, 'is_reg_next_clicked', False):
                    await self.click_reg_next()
                else:
                    await self.monitor_booking_spinner()
            else:
                await self.process_order_confirmation()

    async def auto_login(self):
        if not getattr(self, 'is_login_checking', False):
            print(">>> [KKTIX-登入] 進入自動登入模組，準備執行登入腳本...")
            self.is_login_checking = True

        account = self.config.get("advanced", {}).get("kktix_account", "")
        password = self.config.get("advanced", {}).get(
            "kktix_password_plaintext", "").strip()

        if not password:
            try:
                import util
                password = util.decrypt_me(self.config.get(
                    "advanced", {}).get("kktix_password", ""))
            except:
                pass

        if not account or not password:
            print(">>> [KKTIX-登入]  未設定帳號密碼，跳過自動登入！")
            self.is_login_done = True
            return

        js_check = """
        (function() {
            try {
                let currentUrl = window.location.href;
                if (currentUrl.includes('/users/sign_in')) {
                    let accInput = document.querySelector('#user_login');
                    if (accInput && accInput.offsetParent !== null) return "READY_FOR_CDP";
                    return "WAITING_DOM";
                }
                let signOutBtn = document.querySelector('a[href="/users/sign_out"]');
                if (signOutBtn && signOutBtn.offsetParent !== null) return "LOGGED_IN";

                if (currentUrl === 'https://kktix.com' || currentUrl === 'https://kktix.com/') {
                    let loginBtn = document.querySelector('a[href="/users/sign_in"]');
                    if (loginBtn && loginBtn.offsetParent !== null) { loginBtn.click(); return "WAIT_JUMP"; }
                }
                return "UNKNOWN_PAGE";
            } catch(e) { return "ERROR"; }
        })();
        """
        try:
            result = await self.tab.evaluate(js_check)
            if result == "LOGGED_IN":
                print(">>> [KKTIX-登入]  成功偵測到「可見的登出按鈕」，確認已登入！")
                self.is_login_done = True
            elif result == "READY_FOR_CDP":
                import asyncio
                acc_val = await self.tab.evaluate('document.querySelector("#user_login").value')
                if not acc_val and not getattr(self, 'is_credentials_filled', False):
                    print(f">>> [KKTIX-登入]  實體鍵盤輸入帳號密碼...")
                    acc_input = await self.tab.select('#user_login')
                    if acc_input:
                        await acc_input.send_keys(account)
                    await asyncio.sleep(0.3)
                    pwd_input = await self.tab.select('#user_password')
                    if pwd_input:
                        await pwd_input.send_keys(password)
                    await asyncio.sleep(0.3)
                    print("\n>>> [KKTIX-登入] 帳密已自動填妥！請您【手動】點擊登入按鈕與打勾驗證！\n")
                    self.is_credentials_filled = True
            elif result == "WAIT_JUMP":
                import asyncio
                await asyncio.sleep(0.5)
        except Exception as e:
            pass

    async def assign_ticket_number(self):
        if not getattr(self, 'is_printing_assign', False):
            self.is_printing_assign = True

        import json
        import asyncio

        area_auto_select = self.config.get("area_auto_select", {})
        raw_keyword = area_auto_select.get("area_keyword", "").strip()
        raw_keyword_exclude = self.config.get("keyword_exclude", "")
        if not raw_keyword_exclude:
            raw_keyword_exclude = area_auto_select.get(
                "area_keyword_exclude", "")
        raw_keyword_exclude = str(raw_keyword_exclude).strip()
        area_mode = area_auto_select.get("mode", "from top to bottom")

        def parse_keywords(kw_str):
            kw_str = kw_str.strip()
            if not kw_str:
                return [""]
            try:
                if kw_str.startswith("[") and kw_str.endswith("]"):
                    return json.loads(kw_str)
                if '"' in kw_str or "'" in kw_str:
                    return json.loads("[" + kw_str + "]")
            except:
                pass
            return [x.strip().strip('\'"') for x in kw_str.replace('，', ',').split(',') if x.strip()]

        js_keywords = json.dumps(parse_keywords(
            raw_keyword), ensure_ascii=False)
        js_excludes = json.dumps(parse_keywords(
            raw_keyword_exclude), ensure_ascii=False)
        js_mode = f"'{area_mode}'"

        js_scan = f"""
        (function() {{
            try {{
                let outOfStockAlert = document.querySelector('.alert-warning .alert');
                if (outOfStockAlert && outOfStockAlert.innerText.includes('沒有任何可以購買')) {{
                    return "OUT_OF_STOCK_PAGE";
                }}

                if (document.querySelector('.loading') || document.querySelector('.spinner')) return "LOADING";
                let rows = Array.from(document.querySelectorAll('.display-table-row, .ticket-unit'));
                if (rows.length === 0) {{
                    let names = document.querySelectorAll('.ticket-name');
                    if (names.length === 0) return "NOT_READY";
                    names.forEach(n => rows.push(n.closest('div')));
                }}

                const keywords = {js_keywords};
                const excludes = {js_excludes};
                const mode = {js_mode};

                let candidates = [];
                for (let row of rows) {{
                    if (!row) continue;
                    let rowText = row.innerText.replace(/,/g, '').toUpperCase();
                    let rowHtml = row.innerHTML;

                    if (rowText.includes('已售完') || rowText.includes('SOLD OUT') ||
                        rowText.includes('暫無票') || rowText.includes('未開賣') || rowText.includes('完売') ||
                        !rowHtml.includes('<input')) continue;

                    let isExcluded = false;
                    if (excludes.length > 0 && excludes[0] !== "") {{
                        for (let exc of excludes) {{
                            let cleanExc = exc.trim().replace(/,/g, '').toUpperCase();
                            if (cleanExc.length > 0 && rowText.includes(cleanExc)) {{ isExcluded = true; break; }}
                        }}
                    }}
                    if (isExcluded) continue;

                    let isMatch = false;
                    if (keywords.length === 0 || (keywords.length === 1 && keywords[0] === "")) isMatch = true;
                    else {{
                        for (let k of keywords) {{
                            let target_kws = k.trim().replace(/,/g, '').split(/\\s+/).filter(w => w.length > 0);
                            let currentGroupMatch = true;
                            for (let w of target_kws) {{
                                if (!rowText.includes(w.toUpperCase())) {{ currentGroupMatch = false; break; }}
                            }}
                            if (currentGroupMatch) {{ isMatch = true; break; }}
                        }}
                    }}

                    if (isMatch) {{
                        let input = row.querySelector('input[type="text"]');
                        if (input && !input.disabled) {{
                            let nameEl = row.querySelector('.ticket-name');
                            let areaName = nameEl ? nameEl.innerText.replace(/\\s+/g, ' ').trim() : "指定區域";
                            candidates.push(
                                {{ input: input, areaName: areaName }});
                        }}
                    }}
                }}

                if (candidates.length === 0) return "NO_TICKETS";

                if (mode === "from bottom to top") candidates.reverse();
                else if (mode === "random") {{
                    for (let i = candidates.length - 1; i > 0; i--) {{
                        const j = Math.floor(Math.random() * (i + 1));
                        [candidates[i], candidates[j]] = [
                            candidates[j], candidates[i]];
                    }}
                }}

                let target = candidates[0];
                let uniqueId = 'maxbot_kktix_input_' + Date.now();
                target.input.id = uniqueId;
                target.input.scrollIntoView(
                    {{ behavior: 'instant', block: 'center' }});
                return uniqueId + "|" + target.areaName;
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """

        try:
            result = await self.tab.evaluate(js_scan)

            if isinstance(result, str) and result.startswith("maxbot_kktix_input_"):
                parts = result.split("|", 1)
                target_id = parts[0]
                area_name = parts[1] if len(parts) > 1 else "目標區域"
                self.current_area_name = area_name

                print(f">>> [KKTIX-選票]  鎖定票區：【{area_name}】，執行清空並打入張數...")

                input_element = await self.tab.select(f'#{target_id}')
                if input_element:
                    await input_element.click()
                    clear_js = f"""
                        let el = document.getElementById("{target_id}");
                        el.value = "";
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    """
                    await self.tab.evaluate(clear_js)
                    await asyncio.sleep(0.05)

                    await input_element.send_keys(str(self.ticket_number))
                    await asyncio.sleep(0.05)

                    print(f">>> [KKTIX-選票] 🎉 成功填入正確張數: {self.ticket_number} 張")
                    self.is_ticket_assigned = True

                terms_checkbox = await self.tab.select('#person_agree_terms')
                if terms_checkbox:
                    is_checked = await self.tab.evaluate('document.querySelector("#person_agree_terms").checked')
                    if not is_checked:
                        await terms_checkbox.click()
                        print(f">>> [KKTIX-選票]  已勾選「同意服務條款」")
                    self.is_terms_agreed = True

            elif result in ["NOT_READY", "LOADING"]:
                await asyncio.sleep(0.01)

            # ==========================================
            # 🔥 找不到票時的「隨機重整秒數」與狀態列印邏輯
            # ==========================================
            elif result in ["NO_TICKETS", "OUT_OF_STOCK_PAGE"]:
                self.is_printing_assign = False  # 讓重整後可以重新印 Log

                advanced_conf = self.config.get("advanced", {})
                base_wait = getattr(self, 'refresh_sec', 0.2)
                if base_wait <= 0:
                    base_wait = 0.2

                # 判斷開關狀態
                is_random = advanced_conf.get("auto_reload_random_mode", False)
                random_status = "啟用" if is_random else "關閉"
                actual_wait = base_wait

                if is_random:
                    import random
                    try:
                        rand_range = float(advanced_conf.get(
                            "auto_reload_random_range", 1.0))
                    except:
                        rand_range = 1.0
                    actual_wait = round(
                        base_wait + random.uniform(0, rand_range), 2)

                # 根據不同情況印出包含開關狀態的 Log
                # if result == "OUT_OF_STOCK_PAGE":
                    # print(f">>> [系統] ⚠️ 畫面顯示橘色橫幅「目前沒有任何可以購買的票券」，就地重整！ (隨機秒數: {random_status} | 準備等待 {actual_wait} 秒)")
                # else:
                    # print(f">>> [KKTIX-選票] 找不到符合關鍵字或有空位的票區，準備刷新... (隨機秒數: {random_status} | 準備等待 {actual_wait} 秒)")

                # 發動 JS 重整防卡死
                try:
                    await self.tab.evaluate("window.location.reload();")
                except:
                    pass
                await asyncio.sleep(actual_wait)

        except Exception as e:
            pass

    async def solve_kktix_question(self):
        """[KKTIX] 智能分類填寫：精準區分「會員碼/卡友碼」與「問答題」"""
        raw_answers = self.config.get("advanced", {}).get(
            "user_guess_string", "").strip()

        import json
        ans_list = []
        if raw_answers:
            try:
                if raw_answers.startswith("[") and raw_answers.endswith("]"):
                    ans_list = json.loads(raw_answers)
                elif '"' in raw_answers or "'" in raw_answers:
                    ans_list = json.loads("[" + raw_answers + "]")
                else:
                    ans_list = [x.strip()
                                for x in raw_answers.split(",") if x.strip()]
            except:
                pass
        if not ans_list:
            ans_list = [""]

        # ==========================================
        # 🔥 核心升級：分類雷達 JS，精準抓取不同類型的輸入框
        # ==========================================
        js_find_inputs = """
        (function() {
            try {
                let output = { memberCode: "", captcha: "", others: [] };

                // 1. 尋找「會員碼 / 卡友認證碼」 (特徵：在 .code-input 容器內)
                let codeContainer = document.querySelector('.code-input');
                let codeInput = null;
                if (codeContainer) {
                    // 抓取裡面的文字輸入框 (排除 radio 和 checkbox)
                    codeInput = codeContainer.querySelector(
                        'input[type="text"], input:not([type="radio"]):not([type="checkbox"])');
                    if (codeInput && codeInput.offsetParent !== null && codeInput.value === "") {
                        codeInput.id = codeInput.id || 'maxbot_code_' + Date.now();
                        output.memberCode = codeInput.id;
                    }
                }

                // 2. 尋找「自訂問答題」 (特徵：ng-model 包含 custom_captcha)
                let captchaInput = document.querySelector('input[ng-model="conditions.custom_captcha"], input[name="captcha_answer"]');
                if (captchaInput && captchaInput.offsetParent !== null && captchaInput.value === "") {
                    captchaInput.id = captchaInput.id || 'maxbot_captcha_' + Date.now();
                    output.captcha = captchaInput.id;
                }

                // 3. 尋找「其他未知輸入框」 (防呆：萬一 KKTIX 改版，還是能硬抓)
                let allTexts = Array.from(document.querySelectorAll('input[type="text"]')).filter(el => {
                    if (el.disabled || el.readOnly || el.offsetParent === null) return false;
                    if (el.getAttribute('ng-model')?.includes('quantity')) return false; // 排除張數
                    if (el === codeInput || el === captchaInput) return false; // 排除已經分類過的
                    if (el.value !== "") return false;
                    return true;
                });

                allTexts.forEach((el, idx) => {
                    el.id = el.id || 'maxbot_other_' + Date.now() + '_' + idx;
                    output.others.push(el.id);
                });

                // 如果什麼都沒抓到，回傳 NONE
                if (!output.memberCode && !output.captcha && output.others.length === 0) return "NONE";

                return "JSON|" + JSON.stringify(output);
            } catch(e) { return "ERROR"; }
        })();
        """

        try:
            result = await self.tab.evaluate(js_find_inputs)

            if isinstance(result, str) and result.startswith("JSON|"):
                data_str = result.split("|", 1)[1]
                data = json.loads(data_str)

                total_fields = (1 if data['memberCode'] else 0) + \
                    (1 if data['captcha'] else 0) + len(data['others'])
                print(f">>> [KKTIX-問答] 偵測到 {total_fields} 個需要填寫的格子！")

                import asyncio
                ans_index = 0  # 用來追蹤目前用到字典檔的第幾個答案

                # 定義一個內部小函數來執行填寫動作
                async def fill_field(q_id, field_name):
                    nonlocal ans_index
                    ans = ans_list[ans_index] if ans_index < len(
                        ans_list) else ans_list[-1]
                    q_element = await self.tab.select(f'#{q_id}')
                    if q_element:
                        await q_element.click()
                        await q_element.send_keys(ans)
                        print(f"    -> [{field_name}] 已精準填入：【{ans}】")

                        trigger_js = f"""
                            let el = document.getElementById("{q_id}");
                            if(el) {{
                                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                            }}
                        """
                        await self.tab.evaluate(trigger_js)
                        await asyncio.sleep(0.1)
                    ans_index += 1

                # 按照優先級依序填寫：1.會員碼 -> 2.問答題 -> 3.其他
                if data.get('memberCode'):
                    await fill_field(data['memberCode'], "會員/卡友認證碼")

                if data.get('captcha'):
                    await fill_field(data['captcha'], "自訂問答題")

                for other_id in data.get('others', []):
                    await fill_field(other_id, "一般文字框")

                self.is_captcha_solved = True
                return True

            elif result == "NONE":
                self.is_captcha_solved = True
                return True

        except Exception as e:
            print(f">>> [嚴重錯誤] solve_kktix_question 發生例外: {e}")

        return False

    async def click_reg_next(self):
        js_next = """
        (function() {
            try {
                let container = document.querySelector('.register-new-next-button-area') || document.querySelector('.form-actions');
                if (!container) return false;
                let buttons = Array.from(container.querySelectorAll('button.btn-primary'));
                if (buttons.length === 0) return false;

                let targetBtn = null;
                let computerBtn = buttons.find(b => b.innerText.includes('電腦配位') && !b.disabled);
                if (computerBtn) targetBtn = computerBtn;
                else targetBtn = buttons.find(b => !b.disabled);

                if (targetBtn) {
                    targetBtn.click();
                    return targetBtn.innerText.trim();
                }
                return false;
            } catch(e) { return false; }
        })();
        """
        try:
            clicked_text = await self.tab.evaluate(js_next)
            if clicked_text:
                print(f">>> [KKTIX-下一步]  已點擊「{clicked_text}」！準備進入訂單確認頁...")
                self.is_reg_next_clicked = True
        except:
            pass

    async def click_event_next(self):
        js_click_next = """
        (function() {
            try {
                let btn = document.querySelector('.tickets a.btn-point') || document.querySelector('.tickets a.btn-primary');
                if (btn) {
                    if (btn.innerText.includes('已售完') || btn.innerText.includes('Sold Out')) return "SOLD_OUT";
                    if (btn.innerText.includes('尚未開賣')) return "NOT_YET";
                    let uniqueId = 'kktix_next_' + Date.now();
                    btn.id = uniqueId;
                    return uniqueId;
                }
                return "NOT_FOUND";
            } catch(e) { return "ERROR"; }
        })();
        """
        try:
            result = await self.tab.evaluate(js_click_next)
            import asyncio
            if isinstance(result, str) and result.startswith("kktix_next_"):
                print(">>> [KKTIX-活動頁]  找到「立即購票」按鈕！發動點擊進入選票頁面...")
                target_element = await self.tab.select(f'#{result}')
                if target_element:
                    await target_element.click()
                self.is_event_next_clicked = True
                await asyncio.sleep(0.5)
            elif result == "SOLD_OUT":
                actual_wait = self.get_actual_wait_time()
                # print(f">>> [KKTIX-活動頁]  系統顯示「已售完」，等待 {actual_wait} 秒後刷新...")
                try:
                    await self.tab.evaluate("window.location.reload();")
                except:
                    pass
                await asyncio.sleep(actual_wait)
            elif result == "NOT_YET":
                actual_wait = self.get_actual_wait_time()
                # print(f">>> [KKTIX-活動頁]  尚未開賣，等待 {actual_wait} 秒後刷新...")
                try:
                    await self.tab.evaluate("window.location.reload();")
                except:
                    pass
                await asyncio.sleep(actual_wait)
        except:
            pass

    async def process_order_confirmation(self):
        """[KKTIX] 訂單確認頁處理：偵測倒數計時器並發送通知 (支援無縫連刷)"""
        js_close_popup = """
        (function() {
            try {
                let buttons = document.querySelectorAll('button, a.btn');
                for (let btn of buttons) {
                    let text = btn.innerText.trim();
                    if (['確定', '確認', '關閉', '我知道了'].includes(text)) {
                        if (btn.offsetParent !== null) { btn.click(); return text; }
                    }
                }
                return false;
            } catch(e) { return false; }
        })();
        """
        js_check_order = """
        (function() {
            try {
                let timer = document.querySelector('.countdown-block');
                if (timer && (timer.innerText.includes('訂單已保留') || timer.innerText.includes('請在'))) {
                    return timer.innerText.trim();
                }
                return false;
            } catch(e) { return false; }
        })();
        """
        try:
            clicked_btn_text = await self.tab.evaluate(js_close_popup)
            if clicked_btn_text:
                print(
                    f">>> [KKTIX-系統] 訂單完成頁面偵測到彈窗！已自動點擊「{clicked_btn_text}」按鈕關閉。")

            order_info = await self.tab.evaluate(js_check_order)

            # 如果偵測到訂單，且還沒發送過通知
            if order_info and not getattr(self, 'is_telegram_sent', False):
                self.is_telegram_sent = True

                print("\n=======================================================")
                print(f">>> [KKTIX-訂單]  成功搶到票了！系統偵測到保留位！")
                print(f">>> [KKTIX-訂單]  {order_info}")
                print(">>> [KKTIX-訂單]  機器人已於此頁面靜默待命。")
                print(">>> [KKTIX-訂單]  若要繼續搶票，請直接點擊瀏覽器的「上一頁」，機器人將瞬間重啟！")
                print("=======================================================\n")

                area_name = getattr(self, 'current_area_name', '已選區域')
                msg = f"🎉 <b>KKTIX 搶票成功！</b>\n\n🎟️ <b>區域：</b>{area_name}\n🎫 <b>張數：</b>{self.ticket_number} 張\n⏰ <b>狀態：</b>{order_info}\n\n⚠️ <b>請在時限內手動完成付款！</b>"

                # 發送 Telegram 通知
                await self.send_telegram_message(msg)

                # ==========================================
                # 核心新增：通知發送完畢後，正式掛上「靜默鎖」！
                # ==========================================
                self.is_order_locked = True

        except Exception as e:
            pass

    async def send_telegram_message(self, message):
        """發送 Telegram 通知 (還原完整 Log 與錯誤捕捉版)"""
        # 1. 檢查設定是否存在且啟用
        if not self.config or "advanced" not in self.config:
            return
        if not self.config["advanced"].get("telegram_enable", False):
            return

        bot_token = self.config["advanced"].get("telegram_bot_token", "")
        chat_id = self.config["advanced"].get("telegram_chat_id", "")

        if not bot_token or not chat_id:
            print(">>> [系統] Telegram 設定不完整，跳過通知")
            return

        # 2. 定義發送任務
        def _send():
            import requests
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, data=payload, timeout=6)
                if response.status_code == 200:
                    print(">>> [系統] 📱 Telegram 搶票成功通知發送成功！")
                else:
                    print(f">>> [系統] ⚠️ Telegram 發送失敗: {response.text}")
            except Exception as e:
                print(f">>> [系統] ❌ Telegram 連線錯誤: {e}")

        # 3. 將 requests 丟到背景執行，不卡死主執行緒
        import asyncio
        asyncio.create_task(asyncio.to_thread(_send))

    async def monitor_booking_spinner(self):
        """【樣態 1】監測「查詢空位中」的轉圈圈狀態"""
        js_check = """
        (function() {
            try {
                let spinners = document.querySelectorAll('.spinner-holder, span.ng-binding');
                for (let s of spinners) {
                    if (s.innerText.includes('查詢空位中') && s.offsetParent !== null) return "SPINNING";
                }
                let alerts = document.querySelectorAll('.alert-danger, .error-message');
                for (let a of alerts) {
                    let text = a.innerText || "";
                    if (text.includes('不足') || text.includes('售完') || text.includes('錯誤') || text.includes('失敗')) return "INLINE_ERROR";
                }
                return "STOPPED";
            } catch(e) { return "ERROR"; }
        })();
        """
        try:
            result = await self.tab.evaluate(js_check)
            import asyncio
            if result == "SPINNING":
                if not getattr(self, 'is_printing_spinner', False):
                    print(">>> [KKTIX] ⏳ 系統「查詢空位中」，請勿亂動，祈禱中...")
                    self.is_printing_spinner = True
                self.has_seen_spinner = True
                await asyncio.sleep(0.05)
            elif result == "INLINE_ERROR":
                print("\n>>> [系統] 💥 畫面上出現紅字錯誤提示！判定為搶票失敗。")
                await self.reset_and_reload()
            elif result == "STOPPED":
                if getattr(self, 'has_seen_spinner', False):
                    print("\n>>> [系統] 💥 「查詢空位中」已結束，但未進入訂單頁！判定為票已沒了。")
                    await self.reset_and_reload()
                else:
                    await asyncio.sleep(0.05)
        except:
            pass

    async def reset_and_reload(self):
        """[核心] 觸發失敗重整並解鎖所有狀態"""
        print(">>> [系統] 準備解鎖所有狀態並重新整理...\n")
        self.is_ticket_assigned = False
        self.is_terms_agreed = False
        self.is_captcha_solved = False
        self.is_reg_next_clicked = False
        self.is_printing_assign = False
        self.is_printing_spinner = False
        self.has_seen_spinner = False

        actual_wait = self.get_actual_wait_time()

        import asyncio
        # 發動 JS 重整防卡死
        try:
            await self.tab.evaluate("window.location.reload();")
        except:
            pass

        print(f"    -> 網頁已刷新，等待 {actual_wait} 秒後瞬間重啟搜尋...\n")
        await asyncio.sleep(actual_wait)

    async def check_and_close_popups(self):
        """【樣態 2】全域彈窗攔截 (極速一體化 + 內建暴力解鎖防卡死)"""
        js_unified_check = """
        (function() {
            let results = [];
            if (!window.interceptedPopups) {
                window.interceptedPopups = [];
                window.confirm = function(msg) { window.interceptedPopups.push("[Confirm] " + msg); return true; };
                window.alert = function(msg) { window.interceptedPopups.push("[Alert] " + msg); return true; };
            }
            if (window.interceptedPopups.length > 0) {
                results = window.interceptedPopups.slice();
                window.interceptedPopups = [];
            }
            try {
                let buttons = document.querySelectorAll('button, a.btn');
                for (let btn of buttons) {
                    let text = (btn.innerText || '').trim().toUpperCase();
                    if (['確定', '確認', '關閉', '我知道了', 'OK'].includes(text)) {
                        if (btn.offsetParent !== null) {
                            let container = btn.closest('.ngdialog, .modal, .popup-container');
                            let content = container ? container.innerText.replace(/\\n/g, ' ').trim() : "未知網頁彈窗";
                            btn.click();
                            results.push("[HTML] " + content);
                            break;
                        }
                    }
                }
            } catch(e) {}
            return results.length > 0 ? results : null;
        })();
        """
        try:
            caught_msgs = await self.tab.evaluate(js_unified_check)
            if caught_msgs and isinstance(caught_msgs, list):
                for msg in caught_msgs:
                    clean_msg = str(msg.get('value', msg)
                                    if isinstance(msg, dict) else msg)
                    print(f">>> [系統攔截] 🛡️ 成功攔截並點掉彈窗！內容：「{clean_msg}」")

                print(">>> [系統] 💥 觸發防卡死機制：瞬間解鎖所有狀態，交由系統重整...")
                self.is_ticket_assigned = False
                self.is_terms_agreed = False
                self.is_captcha_solved = False
                self.is_reg_next_clicked = False
                self.is_printing_assign = False
                self.is_printing_spinner = False
                self.has_seen_spinner = False

                # 發動 JS 重整防卡死
                try:
                    await self.tab.evaluate("window.location.reload();")
                except:
                    pass

                return True
        except Exception as e:
            pass
        return False

    def get_actual_wait_time(self):
        """[核心模組] 獲取實際等待秒數（支援讀取設定檔的隨機秒數開關與範圍）"""
        advanced_conf = self.config.get("advanced", {})
        base_wait = getattr(self, 'refresh_sec', 0.2)
        if base_wait <= 0:
            base_wait = 0.2

        is_random = advanced_conf.get("auto_reload_random_mode", False)
        if not is_random:
            return base_wait

        import random
        try:
            rand_range = float(advanced_conf.get(
                "auto_reload_random_range", 1.0))
        except:
            rand_range = 1.0

        return round(base_wait + random.uniform(0, rand_range), 2)

    async def reload_settings(self):
        """[KKTIX] 動態讀取 GUI 指定的設定檔路徑"""
        import json
        import os

        settings_path = getattr(self, 'settings_path', 'settings.json')

        try:
            if not os.path.exists(settings_path):
                return

            with open(settings_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)

            # 更新字典內容
            if "area_auto_select" in new_config:
                self.config["area_auto_select"] = new_config["area_auto_select"]
            if "advanced" in new_config:
                self.config["advanced"] = new_config["advanced"]
            if "kktix" in new_config:
                self.config["kktix"] = new_config["kktix"]
            if "keyword_exclude" in new_config:
                self.config["keyword_exclude"] = new_config["keyword_exclude"]
            if "ticket_number" in new_config:
                self.config["ticket_number"] = new_config["ticket_number"]
                self.ticket_number = int(new_config.get("ticket_number", 1))

            # 更新重整時間
            if "refresh_sec" in new_config:
                self.refresh_sec = float(new_config["refresh_sec"])
            elif "advanced" in new_config and "auto_reload_page_interval" in new_config["advanced"]:
                self.refresh_sec = float(
                    new_config["advanced"]["auto_reload_page_interval"])

            current_refresh = getattr(self, 'refresh_sec', 0.2)

            # 🔥 優化：從路徑中抓出純檔名 (例如 settings-A.json)，讓 Log 看起來更清楚
            filename = os.path.basename(settings_path)
            print(
                f">>> [系統] 進入活動頁面！已套用最新設定 ({filename} | 目標: {self.ticket_number} 張 | 失敗重整: {current_refresh} 秒)")

        except Exception as e:
            # print(f">>> [DEBUG] KKTIX reload_settings 出錯: {e}")
            pass
# ==========================================
# [KKTIX售票]
# ==========================================


class MelonBot:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        import os
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # 狀態變數鎖
        self.is_date_time_selected = False
        self.is_popup_opened = False
        self.is_area_selected = False
        self.is_seat_selected = False
        self.is_telegram_sent = False

        # 🔥 新增：驗證碼通知鎖，避免連續狂發訊息
        self.is_captcha_notified = False

        # 用來存放彈出視窗的 tab 物件
        self.popup_tab = None
        self.popup_opened_time = 0  # 🔥 紀錄彈窗開啟的時間

    async def send_telegram_message(self, message):
        """發送 Telegram 通知 (還原完整 Log 與錯誤捕捉版)"""
        # 1. 檢查設定是否存在且啟用
        if not self.config or "advanced" not in self.config:
            return
        if not self.config["advanced"].get("telegram_enable", False):
            return

        bot_token = self.config["advanced"].get("telegram_bot_token", "")
        chat_id = self.config["advanced"].get("telegram_chat_id", "")

        if not bot_token or not chat_id:
            print(">>> [系統] Telegram 設定不完整，跳過通知")
            return

        # 2. 定義發送任務
        def _send():
            import requests
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, data=payload, timeout=6)
                if response.status_code == 200:
                    print(">>> [系統] 📱 Telegram 通知發送成功！")
                else:
                    print(f">>> [系統] ⚠️ Telegram 發送失敗: {response.text}")
            except Exception as e:
                print(f">>> [系統] ❌ Telegram 連線錯誤: {e}")

        # 3. 將 requests 丟到背景執行，不卡死主執行緒
        import asyncio
        asyncio.create_task(asyncio.to_thread(_send))

    async def run(self):
        print(f">>> [Melon Ticket] 機器人啟動！(目標張數: {self.ticket_number})")
        import os
        import time
        import asyncio

        while True:
            try:
                # 1. 暫停攔截
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                # 2. 處理彈出視窗 (Popup Window)
                tab_count = len(self.driver.tabs)
                if tab_count > 1 and not self.is_popup_opened:
                    print(">>> [系統] 偵測到彈出視窗！正在將視角切換至搶票小視窗...")
                    self.popup_tab = self.driver.tabs[-1]
                    self.is_popup_opened = True
                    self.popup_opened_time = time.time()  # 🔥 開始計時
                    await asyncio.sleep(1)

                # 🔥 修正 1：偵測彈窗關閉，徹底重置進度鎖定
                elif tab_count == 1 and self.is_popup_opened:
                    print(">>> [系統] ⚠️ 彈出視窗已關閉！已清除舊視窗紀錄並解鎖狀態...")
                    self.is_popup_opened = False
                    self.popup_tab = None

                    # 【關鍵解鎖 1】：重置視窗內部的進度！
                    self.is_area_selected = False
                    self.is_seat_selected = False
                    self.is_telegram_sent = False  # 重置 TG 鎖
                    self.is_captcha_notified = False  # 🔥 重置驗證碼通知鎖

                    # 【關鍵解鎖 2】：這行解開，只要視窗不見，就會自動重點 Get Tickets
                    self.is_date_time_selected = False

                # 🔥 新增功能：20分鐘 (1200秒) 強制關閉彈窗重刷機制
                if self.is_popup_opened and self.popup_tab:
                    if time.time() - self.popup_opened_time > 1800:
                        print(
                            ">>> [系統] ⏱️ 彈窗停留超過 30 分鐘！為了防止 Melon 伺服器斷線，正在強制重啟...")
                        try:
                            await self.popup_tab.close()
                        except:
                            pass
                        self.is_popup_opened = False
                        self.popup_tab = None
                        self.is_area_selected = False
                        self.is_seat_selected = False
                        self.is_date_time_selected = False
                        self.is_captcha_notified = False  # 🔥 重置驗證碼通知鎖
                        continue  # 直接進入下一個迴圈，觸發重開邏輯

                active_tab = self.popup_tab if self.is_popup_opened else self.tab

                # 3. 獲取網址
                current_url = await active_tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue
                # ==========================================

                # 🔥 修正 2：完美 F5 重新整理偵測術
                if '/PERFORMANCE/INDEX.HTM' in current_url.upper():
                    is_fresh = await active_tab.evaluate("typeof window.maxbot_reloaded === 'undefined'")
                    if is_fresh:
                        await active_tab.evaluate("window.maxbot_reloaded = true")
                        if getattr(self, 'is_date_time_selected', False):
                            print(">>> [系統] 🔄 偵測到網頁重新載入！已為您解開日期與 ENTER 鎖！")
                            self.is_date_time_selected = False
                            self.is_area_selected = False
                            self.is_seat_selected = False
                            self.is_captcha_notified = False  # 🔥 重置驗證碼通知鎖

                if current_url != getattr(self, 'last_url', ''):
                    print(f"偵測到頁面切換: {current_url}")
                    self.last_url = current_url

                # 4. 分發任務
                await self.dispatch_action(current_url, active_tab)

            except Exception as e:
                # 建議在開發/除錯期間把錯誤印出來，才不會發生「默默壞掉」找不到原因的狀況
                # print(f">>> [迴圈錯誤] {e}")
                pass

            await asyncio.sleep(0.05)

    async def dispatch_action(self, url, active_tab):
        """Melon Ticket 任務分發中心"""
        upper_url = url.upper()

        if '/PERFORMANCE/INDEX.HTM' in upper_url:
            if not getattr(self, 'is_date_time_selected', False):
                await self.select_date_and_time(active_tab)

        elif '/RESERVATION/POPUP' in upper_url:
            # 0. 全時雷達：每次都即時檢查驗證碼是否擋路
            captcha_status = await self.check_and_solve_captcha(active_tab)
            if captcha_status == "BLOCKING":
                return

            # 1. 選區塊
            if not getattr(self, 'is_area_selected', False):
                await self.select_area(active_tab)

            # 2. 刷座位
            elif not getattr(self, 'is_seat_selected', False):
                await self.select_seat(active_tab)

    async def check_and_solve_captcha(self, active_tab):
        """[Melon 第二階段前置] 實體可見度偵測與驗證碼破解"""
        import asyncio

        # 核心 JS 邏輯：檢查、攔截警告、填寫狀態、重新整理
        js_captcha = """
        (function() {
            try {
                let docMain = document;
                let frame = document.getElementById('oneStopFrame');
                let docFrame = frame ? frame.contentWindow.document : null;

                if (!window._alertHooked) {
                    window.alert = function(msg) { window._lastAlert = msg; };
                    window._alertHooked = true;
                }
                if (docFrame && !frame.contentWindow._alertHooked) {
                    frame.contentWindow.alert = function(msg) { frame.contentWindow._lastAlert = msg; };
                    frame.contentWindow._alertHooked = true;
                }

                let alertMsg = window._lastAlert || (docFrame && frame.contentWindow._lastAlert);
                let reloadBtn = docMain.getElementById('btnReload') || (docFrame && docFrame.getElementById('btnReload'));

                // 【需求 3】送出後錯誤警告：自動點擊 Re Flash
                if (alertMsg) {
                    window._lastAlert = null;
                    if (docFrame) frame.contentWindow._lastAlert = null;
                    window._captchaSubmitted = false; 
                    if (reloadBtn) reloadBtn.click();
                    return "ALERT_CAUGHT|" + alertMsg;
                }

                let captchaImg = docMain.getElementById('captchaImg') || (docFrame && docFrame.getElementById('captchaImg'));
                let certBox = docMain.getElementById('certification') || (docFrame && docFrame.getElementById('certification'));

                let isVisible = false;
                if (certBox && certBox.offsetWidth > 0 && certBox.offsetHeight > 0) {
                    let style = window.getComputedStyle(certBox);
                    if (style.display !== 'none' && style.opacity !== '0' && style.visibility !== 'hidden') {
                        isVisible = true;
                    }
                }

                if (!isVisible) {
                    window._captchaSubmitted = false; 
                    return "NO_CAPTCHA"; 
                }

                if (window._captchaSubmitted) {
                    if (Date.now() - window._submitTime > 2500) {
                        window._captchaSubmitted = false;
                        if (reloadBtn) reloadBtn.click(); 
                        return "STUCK_RELOAD";
                    }
                    return "SUBMITTING_WAIT";
                }

                if (!captchaImg || !captchaImg.src) return "BLOCKING";

                return "CAPTCHA_PENDING|" + captchaImg.src;

            } catch(e) {
                return "ERROR|" + e.toString();
            }
        })();
        """

        try:
            result = await active_tab.evaluate(js_captcha)

            if isinstance(result, str):
                if result == "NO_CAPTCHA":
                    self.is_captcha_notified = False
                    self.ocr_fail_count = 0  # 🔥 成功通過時，將失敗計數器歸零

                    if not getattr(self, 'captcha_cleared_printed', False):
                        # print(">>> [Melon] ✅ 驗證碼視窗已確認消失，準備執行區域點擊...")
                        self.captcha_cleared_printed = True

                    return "PASS"

                elif result.startswith("ALERT_CAUGHT|"):
                    msg = result.split("|")[1]
                    print(
                        f">>> [Melon] 🛑 發現警告: 【{msg}】已自動點擊 [Re Flash] 重新取得驗證碼！")
                    self.last_captcha_src = ""
                    await asyncio.sleep(0.5)
                    return "BLOCKING"

                elif result == "SUBMITTING_WAIT":
                    return "BLOCKING"

                elif result == "STUCK_RELOAD":
                    print(">>> [Melon] ⚠️ 送出後無回應超過 2.5 秒，已自動點擊 [Re Flash] 刷新！")
                    self.last_captcha_src = ""
                    await asyncio.sleep(0.5)
                    return "BLOCKING"

                elif result.startswith("CAPTCHA_PENDING|"):
                    self.captcha_cleared_printed = False
                    base64_src = result.split("|")[1]

                    if getattr(self, 'last_captcha_src', '') == base64_src:
                        if not hasattr(self, 'captcha_wait_count'):
                            self.captcha_wait_count = 0
                        self.captcha_wait_count += 1
                        await asyncio.sleep(0.1)
                        return "BLOCKING"

                    self.last_captcha_src = base64_src
                    print(">>> [Melon] 🛡️ 擷取到驗證碼，啟動 ddddocr...")

                    try:
                        import base64
                        import re
                        from io import BytesIO
                        from PIL import Image

                        if not hasattr(self, 'custom_ocr'):
                            import ddddocr
                            self.custom_ocr = ddddocr.DdddOcr(show_ad=False)

                        img_data = base64_src.split(
                            ',')[1] if ',' in base64_src else base64_src
                        raw_img_bytes = base64.b64decode(img_data)

                        try:
                            img = Image.open(BytesIO(raw_img_bytes))
                            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                                bg = Image.new('RGB', img.size,
                                               (255, 255, 255))
                                if img.mode == 'P':
                                    img = img.convert('RGBA')
                                bg.paste(img, mask=img.split()[3])
                                img = bg
                            else:
                                img = img.convert('RGB')

                            buffered = BytesIO()
                            img.save(buffered, format="PNG")
                            ocr_img_bytes = buffered.getvalue()
                        except Exception as img_err:
                            ocr_img_bytes = raw_img_bytes

                        raw_text = self.custom_ocr.classification(
                            ocr_img_bytes)
                        replace_map = {
                            '0': 'O', '1': 'I', '2': 'Z', '3': 'B', '4': 'A',
                            '5': 'S', '6': 'G', '7': 'T', '8': 'B', '9': 'P'
                        }
                        corrected_text = ''.join(
                            [replace_map.get(char, char) for char in raw_text.upper()])
                        clean_text = re.sub(r'[^A-Z]', '', corrected_text)

                        print(
                            f">>> [Melon] 🤖 OCR 辨識結果: 【{clean_text}】 (原始: {raw_text})")

                        if len(clean_text) == 6:
                            self.ocr_fail_count = 0  # 🔥 成功辨識出 6 碼，重置計數器
                            fill_js = f"""
                            (function() {{
                                let docMain = document;
                                let frame = document.getElementById('oneStopFrame');
                                let docFrame = frame ? frame.contentWindow.document : null;
                                
                                let input = docMain.getElementById('label-for-captcha') || (docFrame && docFrame.getElementById('label-for-captcha')); 
                                let btnComplete = docMain.getElementById('btnComplete') || (docFrame && docFrame.getElementById('btnComplete')); 

                                if (input && btnComplete) {{
                                    let nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                                    if (nativeInputValueSetter) {{
                                        nativeInputValueSetter.call(input, '{clean_text}');
                                    }} else {{
                                        input.value = '{clean_text}';
                                    }}
                                    
                                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));

                                    btnComplete.click(); 
                                    window._captchaSubmitted = true;
                                    window._submitTime = Date.now();
                                    return true;
                                }}
                                return false;
                            }})();
                            """
                            success = await active_tab.evaluate(fill_js)
                            if success:
                                print(
                                    f">>> [Melon] 🚀 已將【{clean_text}】輸入格子並點擊 [輸入完成]！等待伺服器驗證...")
                            else:
                                print(
                                    f">>> [Melon] ⚠️ 找不到 #label-for-captcha 或 #btnComplete 元素！")

                            return "BLOCKING"

                        # 🛑 【關鍵更新區塊】：字數不符時，啟動 4 次停損重整邏輯
                        else:
                            # 讀取當前失敗次數，並 +1
                            fail_count = getattr(self, 'ocr_fail_count', 0) + 1
                            self.ocr_fail_count = fail_count

                            if fail_count <= 4:
                                print(
                                    f">>> [Melon] ⚠️ 辨識字數有誤 (長度: {len(clean_text)}，第 {fail_count}/4 次)，自動點擊 [Re Flash] 換圖...")

                                # 發送 JS 直接點擊重整按鈕
                                reload_js = """
                                (function() {
                                    let docMain = document;
                                    let frame = document.getElementById('oneStopFrame');
                                    let docFrame = frame ? frame.contentWindow.document : null;
                                    let reloadBtn = docMain.getElementById('btnReload') || (docFrame && docFrame.getElementById('btnReload'));
                                    if (reloadBtn) reloadBtn.click();
                                })();
                                """
                                await active_tab.evaluate(reload_js)

                                # 清空圖片紀錄，讓下一圈迴圈去抓新出來的驗證碼
                                self.last_captcha_src = ""
                                await asyncio.sleep(0.5)
                            else:
                                print(
                                    f">>> [Melon] ❌ 連續 {fail_count} 次辨識失敗！已達停損點，等待人工接管...")
                                if hasattr(self, 'send_telegram_message') and not getattr(self, 'is_captcha_notified', False):
                                    await self.send_telegram_message("🚨 <b>[Melon Ticket] 🛑 驗證碼辨識連續失敗！</b>\n\n系統已達 4 次自動重試上限，請立即留意畫面，進行【手動接管輸入】！")
                                    self.is_captcha_notified = True

                            return "BLOCKING"

                    except Exception as ocr_err:
                        print(f">>> [Melon] ⚠️ OCR 執行錯誤: {ocr_err}")
                        return "BLOCKING"

        except Exception as e:
            print(f">>> [例外] 驗證碼檢查過程發生錯誤: {e}")

        return "PASS"

    async def select_date_and_time(self, active_tab):
        """[Melon 第一階段] 選擇日期、場次 (舊版穩定邏輯 + 預訂開啟多語系刷新)"""

        reload_interval = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.5))
        if reload_interval <= 0:
            reload_interval = 0.5

        raw_keyword = self.config.get("date_auto_select", {}).get(
            "date_keyword", "").strip()
        import json
        keyword_list = []
        if len(raw_keyword) > 0:
            try:
                if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                    keyword_list = json.loads(raw_keyword)
                else:
                    keyword_list = json.loads("[" + raw_keyword + "]")
            except:
                keyword_list = [raw_keyword]
        else:
            keyword_list = [""]

        js_keywords = json.dumps(keyword_list, ensure_ascii=False)

        js_script = f"""
        (function() {{
            try {{
                const keywords = {js_keywords};

                let ticketBtn = document.querySelector('button.reservationBtn');
                let onSaleBox = document.querySelector('#box_tkt_txt');

                // 1. 🔥 尚未開賣的倒數狀態 (支援中/英/韓介面)
                if (!ticketBtn) {{
                    if (onSaleBox) {{
                        let boxText = onSaleBox.innerText || "";
                        // 只要包含這些「尚未開賣」的字眼，就觸發重刷
                        if (boxText.includes('On-sale') || boxText.includes('预订开启') || boxText.includes('On-sale') || boxText.includes('予約開始')) {{
                            return "REFRESH_PAGE";
                        }}
                    }}
                    if (!onSaleBox) {{
                        return "WAITING_DOM";
                    }}
                }}

                let loader = document.querySelector('#loading') || document.querySelector('.v-progress-circular');
                if (loader && window.getComputedStyle(loader).display !== 'none') {{
                    return "WAITING_DOM";
                }}

                // 2. 選擇日期
                let dateSelected = document.querySelector('#list_date li.on');
                if (!dateSelected) {{
                    let days = Array.from(document.querySelectorAll('#list_date li'));
                    if (days.length === 0) return "WAITING_DOM";

                    // 預設選擇第一天
                    let targetDate = days[0];
                    
                    if (keywords.length > 0 && keywords[0] !== "") {{
                        for (let d of days) {{
                            let text = (d.innerText || "").toUpperCase().replace(/,/g, '');
                            let dataDay = d.getAttribute('data-perfday');
                            if (dataDay && dataDay.length === 8) {{
                                let y = dataDay.substring(0, 4);
                                let m_str = dataDay.substring(4, 6);
                                let d_str = dataDay.substring(6, 8);
                                let m_int = parseInt(m_str, 10).toString();
                                let d_int = parseInt(d_str, 10).toString();
                                text += ` ${{dataDay}} ${{y}}/${{m_str}}/${{d_str}} ${{y}}/${{m_int}}/${{d_int}} ${{m_str}}/${{d_str}} ${{m_int}}/${{d_int}} ${{m_int}}月${{d_int}}日 ${{m_str}}${{d_str}}`;
                            }}

                            let isMatch = false;
                            for (let k of keywords) {{
                                let target_kws = k.trim().toUpperCase().split(/\\s+/).filter(w => w.length > 0);
                                let currentGroupMatch = true;
                                for (let w of target_kws) {{
                                    if (!text.includes(w)) {{
                                        currentGroupMatch = false; break;
                                    }}
                                }}
                                if (currentGroupMatch) {{ isMatch = true; break; }}
                            }}

                            if (isMatch) {{
                                targetDate = d;
                                break;
                            }}
                        }}
                    }}

                    let dateBtn = targetDate.querySelector('button');
                    if (dateBtn) {{
                        dateBtn.click();
                        return "CLICK_DATE";
                    }}
                }}

                // 3. 選擇時間
                let timeSelected = document.querySelector('#list_time li.on');
                let times = Array.from(document.querySelectorAll('#list_time li'));

                if (!timeSelected) {{
                    if (times.length === 0) return "WAITING_TIME";

                    // 預設選擇第一個時段
                    let targetTime = times[0];
                    
                    if (times.length > 1 && (keywords.length > 0 && keywords[0] !== "")) {{
                        for (let t of times) {{
                            let text = (t.innerText || "").toUpperCase();
                            let timeMatch = text.match(/(\\d{{2}}):(\\d{{2}})\\s*(AM|PM)/);
                            if (timeMatch) {{
                                let hr = parseInt(timeMatch[1], 10);
                                let min = timeMatch[2];
                                let ampm = timeMatch[3];
                                if (ampm === 'PM' && hr < 12) hr += 12;
                                if (ampm === 'AM' && hr === 12) hr = 0;
                                let hr24 = hr.toString().padStart(2, '0');
                                text += ` ${{hr24}}:${{min}} ${{hr24}}${{min}}`;
                            }}

                            let isMatch = false;
                            for (let k of keywords) {{
                                let target_kws = k.trim().toUpperCase().split(/\\s+/).filter(w => w.length > 0);
                                let currentGroupMatch = true;
                                for (let w of target_kws) {{
                                    if (!text.includes(w)) {{
                                        currentGroupMatch = false; break;
                                    }}
                                }}
                                if (currentGroupMatch) {{ isMatch = true; break; }}
                            }}
                            if (isMatch) {{ targetTime = t; break; }}
                        }}
                    }}

                    let timeBtn = targetTime.querySelector('button') || targetTime.children[0];
                    if (timeBtn) {{
                        timeBtn.click();
                        return "CLICK_TIME";
                    }}
                }}

                // 4. 點擊 / 聚焦送出按鈕
                if (ticketBtn) {{
                    const isBtnDisabled = ticketBtn.disabled || ticketBtn.classList.contains('disabled') || ticketBtn.classList.contains('disable');
                    if (!isBtnDisabled) {{
                        ticketBtn.focus();
                        return "FOCUS_SUBMIT";
                    }}
                }}

                return "WAITING_BTN";

            }} catch(e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_script)
            import asyncio

            if isinstance(result, str):
                # 🔥 這裡接接手 JavaScript 回傳的 REFRESH_PAGE 訊號
                if result == "REFRESH_PAGE":
                    print(
                        f">>> [Melon] ⏳ 偵測到「尚未開賣 (預訂開啟)」，{reload_interval} 秒後自動重新整理...")
                    await asyncio.sleep(reload_interval)
                    await active_tab.reload()

                elif result == "WAITING_DOM" or result == "WAITING_TIME":
                    await asyncio.sleep(0.1)

                elif result == "CLICK_DATE":
                    print(">>> [Melon] 📅 已極速選擇日期！等待場次時間載入...")
                    await asyncio.sleep(0.3)

                elif result == "CLICK_TIME":
                    print(">>> [Melon] ⏰ 已極速選擇時間！準備鎖定 Get Tickets...")
                    await asyncio.sleep(0.3)

                elif result == "FOCUS_SUBMIT":
                    print(">>> [Melon] 🚀 目標已鎖定！拋棄滑鼠，發送底層「實體鍵盤 Enter」！")

                    import nodriver.cdp.input_ as input_cdp
                    await active_tab.send(input_cdp.dispatch_key_event(
                        type_="keyDown",
                        windows_virtual_key_code=13,
                        key="Enter",
                        text="\r"
                    ))
                    await active_tab.send(input_cdp.dispatch_key_event(
                        type_="keyUp",
                        windows_virtual_key_code=13,
                        key="Enter"
                    ))

                    self.is_date_time_selected = True
                    await asyncio.sleep(1.0)

                elif result in ["LOADING", "WAITING_BTN", "NO_FRAME"]:
                    if not hasattr(self, 'area_wait_count'):
                        self.area_wait_count = 0
                    self.area_wait_count += 1
                    if self.area_wait_count % 20 == 0:
                        print(">>> [Melon] ⏳ 準備就緒，持續極速掃描 DOM 中...")
                    await asyncio.sleep(0.05)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 發生內部 JS 錯誤: {result}")

        except Exception as e:
            print(f">>> [嚴重錯誤] select_date_and_time 發生例外: {e}")

    async def select_area(self, active_tab):
        """[Melon 第二階段] 神級字尾狙擊 + 自動輪詢記憶版"""
        import json
        import time
        import random
        import asyncio

        if not hasattr(self, 'cooldown_base'):
            self.cooldown_base = 15
        if not hasattr(self, 'cooldown_until'):
            self.cooldown_until = 0
        if time.time() < self.cooldown_until:
            await asyncio.sleep(0.5)
            return

        raw_keyword = self.config.get("area_auto_select", {}).get(
            "area_keyword", "").strip()
        area_mode = self.config.get("area_auto_select", {}).get(
            "mode", "top-down").lower()
        base_interval = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.5))

        is_random_mode = self.config.get("advanced", {}).get(
            "auto_reload_random_mode", False)
        jitter = float(self.config.get("advanced", {}).get(
            "auto_reload_random_range", "0.2")) if is_random_mode else 0.0

        keyword_list = []
        if len(raw_keyword) > 0:
            try:
                if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                    keyword_list = json.loads(raw_keyword)
                else:
                    keyword_list = json.loads("[" + raw_keyword + "]")
            except:
                keyword_list = [raw_keyword]
        else:
            keyword_list = [""]

        js_keywords = json.dumps(keyword_list, ensure_ascii=False)

        js_area = f"""
        (function() {{
            try {{
                let frame = document.getElementById('oneStopFrame');
                if (!frame) return "NO_FRAME";
                let doc = frame.contentWindow.document;

                if (!frame.contentWindow._alertHooked) {{
                    frame.contentWindow.alert = function(msg) {{ frame.contentWindow._lastAlert = msg; }};
                    frame.contentWindow._alertHooked = true;
                }}
                if (frame.contentWindow._lastAlert) {{
                    let msg = frame.contentWindow._lastAlert;
                    frame.contentWindow._lastAlert = "";
                    return "COOLDOWN|" + msg;
                }}

                let loader = doc.querySelector('.seatLoading');
                if (loader && window.getComputedStyle(loader).display !== 'none') return "LOADING";

                const normalizeText = (str) => {{
                    return (str || "").toUpperCase()
                        .replace(/[區구역]/g, ' ') 
                        .replace(/[^A-Z0-9\u4e00-\u9fa5\uac00-\ud7a3]/g, ' ') 
                        .replace(/\s+/g, ' ').trim();
                }};

                const rawKeywords = {js_keywords};
                const keywords = rawKeywords.map(k => normalizeText(k)).filter(k => k.length > 0);
                const mode = "{area_mode}";

                let sectionToOpen = doc.querySelector(".seat_name:not(.open)");
                if (sectionToOpen) sectionToOpen.click();

                // ==========================================
                // 1. 一般區域比對 (area_tit)
                // ==========================================
                let areaTits = doc.querySelectorAll(".area_tit");
                let validAreas = [];

                if (areaTits.length > 0) {{
                    for (let i = 0; i < areaTits.length; i++) {{
                        let clickTarget = areaTits[i].closest('li') || areaTits[i].parentElement;
                        let rawText = areaTits[i].innerText || areaTits[i].innerHTML;
                        let normText = normalizeText(rawText); 
                        let paddedNormText = " " + normText + " "; 

                        let isMatch = false;
                        if (keywords.length === 0) {{
                            isMatch = true;
                        }} else {{
                            for (let k of keywords) {{
                                let paddedKeyword = " " + k + " "; 
                                if (paddedNormText.endsWith(paddedKeyword)) {{
                                    isMatch = true; break;
                                }}
                                if (k.length > 2 && paddedNormText.includes(paddedKeyword)) {{
                                    isMatch = true; break;
                                }}
                            }}
                        }}

                        if (isMatch) {{
                            validAreas.push({{
                                target: clickTarget,
                                text: rawText.replace(/<[^>]*>?/gm, '').trim()
                            }});
                        }}
                    }}

                    if (validAreas.length > 0) {{
                        let selectedArea = null;
                        if (mode === "random") {{
                            let randomIndex = Math.floor(Math.random() * validAreas.length);
                            selectedArea = validAreas[randomIndex];
                        }} else {{
                            // 🔥 核心修正：自動輪詢記憶 (Round-Robin)
                            if (typeof window._melon_area_idx === 'undefined') window._melon_area_idx = 0;
                            selectedArea = validAreas[window._melon_area_idx % validAreas.length];
                            window._melon_area_idx++; // 下次進來點下一個
                        }}

                        selectedArea.target.click();
                        return "AREA_CLICKED|" + selectedArea.text;
                    }}
                }}

                // ==========================================
                // 2. 零星票區比對 (partSeatGrade) 
                // ==========================================
                let singleGrades = doc.querySelectorAll('#partSeatGrade > tr');
                if (singleGrades.length > 0) {{
                    let matchedGrades = [];
                    for (let g of singleGrades) {{
                        let rawText = g.innerText || "";
                        let normText = normalizeText(rawText);
                        let paddedNormText = " " + normText + " ";
                        
                        let isMatch = false;
                        if (keywords.length === 0) {{
                            isMatch = true;
                        }} else {{
                            for (let k of keywords) {{
                                let paddedKeyword = " " + k + " ";
                                if (paddedNormText.endsWith(paddedKeyword) || (k.length > 2 && paddedNormText.includes(paddedKeyword))) {{
                                    isMatch = true; break;
                                }}
                            }}
                        }}
                        if (isMatch) matchedGrades.push(g);
                    }}

                    if (matchedGrades.length > 0) {{
                        let targetGrade = null;
                        if (mode === "random") {{
                            let randomIndex = Math.floor(Math.random() * matchedGrades.length);
                            targetGrade = matchedGrades[randomIndex];
                        }} else {{
                            // 🔥 同樣套用輪詢記憶
                            if (typeof window._melon_grade_idx === 'undefined') window._melon_grade_idx = 0;
                            targetGrade = matchedGrades[window._melon_grade_idx % matchedGrades.length];
                            window._melon_grade_idx++;
                        }}
                        targetGrade.click();
                        return "AREA_CLICKED|" + (targetGrade.innerText || "").replace(/\\n/g, ' ').trim();
                    }}
                }}

                return "WAITING_DOM";

            }} catch(e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_area)

            if isinstance(result, str):
                if result.startswith("COOLDOWN|"):
                    msg = result.split("|")[1] if "|" in result else "不明錯誤"
                    print(f">>> [Melon] 🛑 觸發伺服器阻擋警告: {msg}")
                    print(
                        f">>> [Melon] ❄️ 進入強制休息冷卻期 {self.cooldown_base} 秒...")
                    self.cooldown_until = time.time() + self.cooldown_base
                    self.cooldown_base *= 2
                    return

                elif result.startswith("AREA_CLICKED|"):
                    area_name = result.split("|")[1]
                    print(f">>> [Melon] 🎯 強制點擊區域更新：【{area_name}】！呼叫座位掃描...")

                    self.is_area_selected = True
                    self.cooldown_base = 15

                    human_delay = base_interval + \
                        random.uniform(-jitter, jitter)
                    human_delay = max(0.1, human_delay)
                    await asyncio.sleep(human_delay)

                elif result == "WAITING_DOM":
                    # 🔥 靜默等待 DOM，不洗版
                    await asyncio.sleep(0.1)

                elif result in ["LOADING", "NO_FRAME"]:
                    if not hasattr(self, 'area_wait_count'):
                        self.area_wait_count = 0
                    self.area_wait_count += 1
                    if self.area_wait_count % 20 == 0:
                        print(">>> [Melon] ⏳ 區域資料載入中，持續極速掃描 DOM...")
                    await asyncio.sleep(0.05)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 區域選擇 JS 錯誤: {result}")

        except Exception as e:
            print(f">>> [例外] select_area: {e}")

    async def select_seat(self, active_tab):
        """[Melon 第三階段] 掃描 SVG 抓取空位，加入「成功跳轉驗證機制」防被搶走卡死"""

        js_seat = """
        (function() {
            try {
                let frame = document.getElementById('oneStopFrame');
                if (!frame) return "NO_FRAME";
                let doc = frame.contentWindow.document;

                // 1. 攔截 Alert (被別人搶走時常跳出的警告)
                if (frame.contentWindow._lastAlert) {
                    let msg = frame.contentWindow._lastAlert;
                    frame.contentWindow._lastAlert = null;
                    window._melon_seat_submitted = 0; // 解除等待鎖定
                    return "ALERT_CAUGHT|" + msg;
                }

                // 2. 🔥 驗證階段：判斷是否真的成功跳轉了
                if (window._melon_seat_submitted) {
                    let canvasStillExists = doc.getElementById("ez_canvas");
                    let isCanvasVisible = canvasStillExists && window.getComputedStyle(canvasStillExists).display !== 'none';

                    // 狀況 A：座位圖消失了，代表成功進入下一步(結帳或票價頁面)
                    if (!isCanvasVisible) {
                        window._melon_seat_submitted = 0;
                        return "SEAT_SUBMITTED_SUCCESS";
                    }

                    // 狀況 B：等了超過 2 秒座位圖都還在，代表被別人搶走但系統沒跳 Alert，或是卡住了
                    if (Date.now() - window._melon_seat_submitted > 2000) {
                        window._melon_seat_submitted = 0; // 重置鎖定
                        return "SEAT_TAKEN_RETRY";
                    }

                    // 狀況 C：還在 2 秒內，繼續等
                    return "WAITING_TRANSITION";
                }

                // 3. 檢查載入中動畫
                let loader = doc.querySelector('.seatLoading');
                if (loader && window.getComputedStyle(loader).display !== 'none') {
                    window._seatEmptyCount = 0;
                    return "LOADING";
                }

                let canvas = doc.getElementById("ez_canvas");
                if (!canvas) return "NO_SEAT";

                // 4. 尋找空位
                let seats = Array.from(canvas.querySelectorAll("rect, polygon, circle, path")).filter(s => {
                    let fill = s.getAttribute("fill");
                    if (!fill) return false;
                    let fUpper = fill.toUpperCase();
                    // 排除背景色與不可點選色
                    return fUpper !== "#DDDDDD" && fUpper !== "#CCCCCC" && fUpper !== "NONE" && fUpper !== "#FFFFFF";
                });

                if (seats.length === 0) {
                    if (!window._seatEmptyCount) window._seatEmptyCount = 0;
                    window._seatEmptyCount++;
                    if (window._seatEmptyCount > 5) {
                        window._seatEmptyCount = 0;
                        return "NO_SEAT";
                    }
                    return "WAITING_RECT";
                }

                window._seatEmptyCount = 0;
                let targetSeat = seats[0];
                
                // 發動點擊
                targetSeat.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: frame.contentWindow }));

                // 點擊下一步
                let nextBtn = doc.getElementById("nextTicketSelection") || doc.getElementById("btnNext");
                if (nextBtn) {
                    nextBtn.click();
                    // 🔥 標記送出時間，進入「跳轉驗證模式」
                    window._melon_seat_submitted = Date.now();
                    return "CLICKED_NEXT_WAITING";
                }

                return "WAITING_BTN";

            } catch(e) {
                return "ERROR|" + e.toString();
            }
        })();
        """

        try:
            result = await active_tab.evaluate(js_seat)
            import asyncio

            if isinstance(result, str):

                # 🔥 新增：送出後的等待狀態
                if result == "CLICKED_NEXT_WAITING":
                    print(">>> [Melon] 🖱️ 已點選座位並送出，等待伺服器驗證...")
                    await asyncio.sleep(0.1)

                elif result == "WAITING_TRANSITION":
                    if not hasattr(self, 'verify_wait_count'):
                        self.verify_wait_count = 0
                    self.verify_wait_count += 1
                    if self.verify_wait_count % 10 == 0:
                        print(">>> [Melon] ⏳ 伺服器驗證中，確認是否成功進入結帳...")
                    await asyncio.sleep(0.1)

                # 🔥 真正成功：確定畫面跳轉了才發通知
                elif result == "SEAT_SUBMITTED_SUCCESS":
                    print(">>> [Melon] 🎉 驗證通過！成功突破座位防線！進入結帳畫面...")
                    self.is_seat_selected = True

                    if not getattr(self, 'is_telegram_sent', False):
                        await self.send_telegram_message(" <b>[Melon Ticket]</b> 🎉 搶票成功！\n機器人已成功點擊空位並送出，請立刻回視窗查看結帳！")
                        self.is_telegram_sent = True
                    await asyncio.sleep(0.5)

                # 🔥 假成功/無回應：直接退回重刷
                elif result == "SEAT_TAKEN_RETRY":
                    print(">>> [Melon] ⚠️ 點擊送出後無反應 (座位可能已被秒殺)！退回重新選區...")
                    self.is_area_selected = False
                    self.is_seat_selected = False
                    await asyncio.sleep(0.2)

                # 攔截警告
                elif result.startswith("ALERT_CAUGHT|"):
                    msg = result.split("|", 1)[1]
                    print(f"\n>>> [系統] ⚠️ 攔截到 Melon 系統警告：【{msg}】")
                    print(">>> [系統] 🔄 座位已被搶走或失效！準備退回重新點選區域...")
                    self.is_area_selected = False
                    self.is_seat_selected = False
                    await asyncio.sleep(0.2)

                # 真的沒位子
                elif result == "NO_SEAT":
                    print(">>> [Melon] ❌ 該區目前無空位！退回重選區域...")
                    self.is_area_selected = False
                    self.is_seat_selected = False

                    base_interval = float(self.config.get("advanced", {}).get(
                        "auto_reload_page_interval", 0.5) or 0.5)
                    is_random_mode = self.config.get("advanced", {}).get(
                        "auto_reload_random_mode", False)
                    import random
                    jitter = float(self.config.get("advanced", {}).get(
                        "auto_reload_random_range", 0.2) or 0.2) if is_random_mode else 0.0

                    human_delay = base_interval + \
                        random.uniform(-jitter, jitter)
                    human_delay = max(0.1, human_delay)
                    await asyncio.sleep(human_delay)

                elif result in ["LOADING", "WAITING_SVG", "WAITING_RECT", "WAITING_BTN", "NO_FRAME"]:
                    if not hasattr(self, 'seat_wait_count'):
                        self.seat_wait_count = 0
                    self.seat_wait_count += 1
                    if self.seat_wait_count % 5 == 0:
                        print(f">>> [Melon] ⏳ 座位圖掃描中，狀態: {result} ...")
                    await asyncio.sleep(0.05)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 找座位 JS 錯誤: {result}")

        except Exception as e:
            print(f">>> [例外] select_seat: {e}")


# ==========================================
# [Melon Ticket 搶票]
# ==========================================

class BillboardLiveBot:

    def __init__(self, driver, config):
        """初始化設定與狀態鎖"""
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 暫停機制 (讀取全域暫停檔案)
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        # ==========================================
        # 🚦 狀態變數鎖 (對應你的 5 個流程)
        # ==========================================
        self.is_event_selected = False   # 1. 場次是否已選
        self.is_date_selected = False    # 2. 日期是否已選
        self.is_data_filled = False      # 3. 資料是否已填寫送出
        self.is_seat_selected = False    # 4. 座位是否已選
        self.is_success_notified = False  # 5. 是否已發送成功通知

    async def run(self):
        """總控主迴圈：持續監聽網址與分發任務"""
        print(f">>> [BillboardLive] 機器人啟動！(目標張數: {self.ticket_number})")

        while True:
            try:
                # 1. 暫停攔截 (手動控制暫停/繼續)
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                # 2. 獲取當前網址
                current_url = await self.tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                # 3. 網址切換日誌 (方便除錯)
                if current_url != getattr(self, 'last_url', ''):
                    print(f"\n>>> [系統] 偵測到頁面切換: {current_url}")
                    self.last_url = current_url

                    # 💡 小技巧：如果發現退回首頁，可以自動重置所有狀態鎖
                    # if "首頁特徵網址" in current_url:
                    #     self.reset_all_states()

                # 4. 任務分發
                await self.dispatch_action(current_url, self.tab)

            except Exception as e:
                err_msg = str(e)
                # 攔截常見的底層斷線錯誤 (瀏覽器跳轉或重整時的瞬間斷線)，直接靜音略過
                if "1225" in err_msg or "10061" in err_msg or "10054" in err_msg or "WinError" in err_msg:
                    pass
                # else:
                    # 只有真正不可預期的錯誤才印出來
                    # print(f">>> [主迴圈例外] BillboardLiveBot 發生錯誤: {e}")

            # 確保每次迴圈都有極短的休息，避免 CPU 飆高
            import asyncio
            await asyncio.sleep(0.05)

    async def dispatch_action(self, url, active_tab):
        """任務分發中心：根據網址特徵決定現在該做什麼"""
        upper_url = url.upper()

        # ==========================================
        # 流程 1：場次頁面 (包含 /EVENTS/ 且不含下一步的 /REGISTRATIONS/)
        # ==========================================
        if '/EVENTS/' in upper_url and '/REGISTRATIONS/' not in upper_url:

            # 🔥 退回首頁重置機制：如果我們身上帶著「已選日期/已填資料/已選位」的標記
            # 但網址卻在第一關，代表我們被系統踢出來，或是手動按了上一頁！
            if getattr(self, 'is_date_selected', False) or getattr(self, 'is_data_filled', False) or getattr(self, 'is_seat_selected', False):
                print(">>> [系統] 🔄 偵測到退回場次頁面！已強制解除所有任務鎖定，重新開始搶票！")
                self.is_event_selected = False
                self.is_date_selected = False
                self.is_data_filled = False
                self.is_seat_selected = False

            # 取消原本 Python 的 if not self.is_event_selected 擋箭牌
            # 讓程式永遠進入 select_event，由前端 JS 來判斷要不要點擊
            await self.select_event(active_tab)

        # ==========================================
        # 流程 2、3、4：日期 ➔ 資料 ➔ 座位 (因為網址都有 /REGISTRATIONS/)
        # ==========================================
        elif '/REGISTRATIONS/' in upper_url:
            # 這裡維持順序接關的狀態機不變
            if not getattr(self, 'is_date_selected', False):
                await self.select_date(active_tab)

            elif not getattr(self, 'is_data_filled', False):
                await self.fill_data(active_tab)

            elif not getattr(self, 'is_seat_selected', False):
                await self.select_seat(active_tab)

        # ==========================================
        # 流程 5：搶票成功 (結帳) 頁面
        # ==========================================
        elif '/ORDERS/' in upper_url or '/CHECKOUT/' in upper_url:
            if not getattr(self, 'is_success_notified', False):
                print(">>> [Billboard] 🎉 搶票大成功！進入結帳頁面！")
                self.is_success_notified = True

                if getattr(self, 'config', {}).get("advanced", {}).get("telegram_enable", False):
                    if hasattr(self, 'send_telegram_message'):
                        await self.send_telegram_message("🎟️ <b>[Billboard Live]</b> 🎉 座位點選成功！\n機器人已為您鎖定座位並進入結帳，請立刻回視窗付款！")
    # ==========================================
    # 以下為具體執行的非同步函數 (等待填入 JS 邏輯)
    # ==========================================

    async def select_event(self, active_tab):
        """[流程 1] 掃描並點擊「立即購票」，支援熱重載與前端防卡死"""
        import asyncio

        reload_interval = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.5))
        if reload_interval <= 0:
            reload_interval = 0.5

        js_event = """
        (function() {
            try {
                // 1. 尋找「立即購票」按鈕
                let links = Array.from(document.querySelectorAll('a'));
                let buyBtn = links.find(el => el.innerText && el.innerText.includes('立即購票'));
                
                if (buyBtn) {
                    // 🔥 加入前端防連點鎖：只有在沒點過的情況下才點擊
                    if (!window._maxbot_event_clicked) {
                        buyBtn.click();
                        window._maxbot_event_clicked = true;
                        return "CLICK_BUY";
                    }
                    return "WAITING_TRANSITION"; // 已經點了，安靜等待跳轉
                }

                // 2. 如果沒看到按鈕，尋找是否有「開賣」的倒數提示
                let spans = Array.from(document.querySelectorAll('span'));
                let notOnSaleSpan = spans.find(el => el.innerText && el.innerText.includes('開賣'));
                
                if (notOnSaleSpan) {
                    return "NOT_ON_SALE|" + notOnSaleSpan.innerText.trim();
                }

                return "WAITING_DOM";

            } catch(e) {
                return "ERROR|" + e.toString();
            }
        })();
        """

        try:
            result = await active_tab.evaluate(js_event)

            if isinstance(result, str):
                if result == "CLICK_BUY":
                    print(">>> [Billboard] 🚀 偵測到「立即購票」！已極速點擊，準備進入下一步...")
                    self.is_event_selected = True
                    await asyncio.sleep(0.5)

                elif result == "WAITING_TRANSITION":
                    # 已經點了按鈕，安靜等待網頁跳轉，不印 log 避免洗版
                    await asyncio.sleep(0.05)

                elif result.startswith("NOT_ON_SALE|"):
                    msg = result.split("|")[1]

                    # 執行熱重載邏輯
                    try:
                        import os
                        import json
                        try:
                            import util
                            config_path = os.path.join(
                                util.get_app_root(), "settings.json")
                        except:
                            config_path = "settings.json"

                        if os.path.exists(config_path):
                            current_mtime = os.path.getmtime(config_path)
                            if not hasattr(self, '_last_config_mtime'):
                                self._last_config_mtime = current_mtime
                            elif self._last_config_mtime != current_mtime:
                                with open(config_path, 'r', encoding='utf-8') as f:
                                    self.config = json.load(f)
                                self._last_config_mtime = current_mtime
                                print(
                                    "\n>>> [系統] 🔄 偵測到 settings.json 變更，已成功熱重載最新戰術！")
                                reload_interval = float(self.config.get(
                                    "advanced", {}).get("auto_reload_page_interval", 0.5))
                                if reload_interval <= 0:
                                    reload_interval = 0.5
                    except Exception as e:
                        pass

                    print(
                        f">>> [Billboard] ⏳ 尚未開賣 ({msg})，{reload_interval} 秒後自動重新整理...")
                    await asyncio.sleep(reload_interval)
                    await active_tab.reload()

                elif result == "WAITING_DOM":
                    await asyncio.sleep(0.1)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 場次頁面腳本錯誤: {result}")

        except Exception as e:
            print(f">>> [例外] select_event 發生錯誤: {e}")

    async def select_date(self, active_tab):
        """[流程 2] 處理日期與票種的連動下拉選單"""
        import json
        import asyncio

        # 1. 讀取設定檔的關鍵字
        # 日期關鍵字 (例如 "1st", "18:00")
        raw_date_kw = self.config.get("date_auto_select", {}).get(
            "date_keyword", "").strip()
        # 票種關鍵字 (使用設定檔中的 user_guess_string，例如 "雙人席", "3000")
        raw_ticket_kw = self.config.get("advanced", {}).get(
            "user_guess_string", "").strip()

        # 格式化為 List
        def parse_kw(raw_str):
            if not raw_str:
                return [""]
            try:
                if raw_str.startswith("[") and raw_str.endswith("]"):
                    return json.loads(raw_str)
                else:
                    return json.loads("[" + raw_str + "]")
            except:
                return [raw_str.replace('"', '').strip()]

        date_keywords = parse_kw(raw_date_kw)
        ticket_keywords = parse_kw(raw_ticket_kw)

        js_keywords = json.dumps({
            "date": date_keywords,
            "ticket": ticket_keywords
        }, ensure_ascii=False)

        # 2. 核心 JS 邏輯 (處理雙重下拉選單)
        js_date_selection = f"""
        (function() {{
            try {{
                const kws = {js_keywords};
                const normalizeText = (str) => (str || "").toUpperCase().replace(/\\s+/g, '');

                // 尋找畫面上所有的下拉式選單 (Combobox)
                let comboboxes = document.querySelectorAll('button[role="combobox"]');
                if (comboboxes.length < 2) return "WAITING_DOM";

                let dateBox = comboboxes[0];
                let ticketBox = comboboxes[1];

                // ==========================================
                // 步驟 A：選擇日期
                // ==========================================
                if (!window._maxbot_date_picked) {{
                    // 如果選單還沒展開，先點擊展開
                    if (dateBox.getAttribute('aria-expanded') !== 'true') {{
                        dateBox.click();
                        return "OPENING_DATE_BOX";
                    }}

                    // 尋找展開後的選項
                    let listbox = dateBox.nextElementSibling;
                    if (!listbox) return "WAITING_DATE_LIST";
                    let options = Array.from(listbox.querySelectorAll('div[role="option"]'));
                    if (options.length === 0) return "WAITING_DATE_OPTIONS";

                    let targetOption = options[0]; // 預設選第一個
                    for (let opt of options) {{
                        let text = normalizeText(opt.innerText);
                        let isMatch = false;
                        if (kws.date.length === 0 || kws.date[0] === "") {{
                            isMatch = true;
                        }} else {{
                            isMatch = kws.date.some(k => k && text.includes(normalizeText(k)));
                        }}
                        if (isMatch) {{ targetOption = opt; break; }}
                    }}

                    targetOption.click();
                    window._maxbot_date_picked = true;
                    return "DATE_CLICKED";
                }}

                // ==========================================
                // 步驟 B：選擇票種 (等待票種載入)
                // ==========================================
                if (window._maxbot_date_picked && !window._maxbot_ticket_picked) {{
                    // 點擊日期後，票種選單可能會 disabled 或 loading，需要等待
                    if (ticketBox.disabled) return "WAITING_TICKET_UNLOCK";

                    if (ticketBox.getAttribute('aria-expanded') !== 'true') {{
                        ticketBox.click();
                        return "OPENING_TICKET_BOX";
                    }}

                    let listbox = ticketBox.nextElementSibling;
                    if (!listbox) return "WAITING_TICKET_LIST";
                    let options = Array.from(listbox.querySelectorAll('div[role="option"]'));
                    if (options.length === 0) return "WAITING_TICKET_OPTIONS";

                    let targetOption = options[0]; // 預設選第一個
                    for (let opt of options) {{
                        let text = normalizeText(opt.innerText);
                        let isMatch = false;
                        if (kws.ticket.length === 0 || kws.ticket[0] === "") {{
                            isMatch = true;
                        }} else {{
                            isMatch = kws.ticket.some(k => k && text.includes(normalizeText(k)));
                        }}
                        if (isMatch) {{ targetOption = opt; break; }}
                    }}

                    targetOption.click();
                    window._maxbot_ticket_picked = true;
                    return "TICKET_CLICKED";
                }}

                // ==========================================
                // 步驟 C：點擊下一步 / 送出
                // ==========================================
                if (window._maxbot_date_picked && window._maxbot_ticket_picked) {{
                    // ⚠️ 注意：這裡假設有一個 "下一步" 或 "確認" 的按鈕。
                    // 尋找常見的送出按鈕 (type="submit" 或是文字包含 下一步/結帳/確認 等)
                    let btns = Array.from(document.querySelectorAll('button'));
                    let submitBtn = btns.find(b =>
                        b.type === 'submit' ||
                        (b.innerText && b.innerText.includes('下一步')) ||
                        (b.innerText && b.innerText.includes('確認'))
                    );

                    if (submitBtn && !submitBtn.disabled) {{
                        submitBtn.click();
                        return "FORM_SUBMITTED";
                    }}
                    return "WAITING_SUBMIT_BTN";
                }}

                return "WAITING_DOM";

            }} catch(e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_date_selection)

            if isinstance(result, str):
                if result == "OPENING_DATE_BOX":
                    await asyncio.sleep(0.05)  # 給下拉動畫一點時間
                elif result == "DATE_CLICKED":
                    print(">>> [Billboard] 📅 日期場次已選擇！等待票種資料載入...")
                    await asyncio.sleep(0.1)
                elif result == "OPENING_TICKET_BOX":
                    await asyncio.sleep(0.05)
                elif result == "TICKET_CLICKED":
                    print(">>> [Billboard] 🎟️ 票種已成功選擇！準備進入下一步...")
                    await asyncio.sleep(0.1)
                elif result == "FORM_SUBMITTED":
                    print(">>> [Billboard] 🚀 日期與票種已送出！切換至資料填寫階段...")
                    self.is_date_selected = True  # 放行，交給下一個路由
                    await asyncio.sleep(0.5)

                # 等待狀態 (不印出 Log 避免洗版)
                elif result in ["WAITING_DOM", "WAITING_DATE_LIST", "WAITING_DATE_OPTIONS", "WAITING_TICKET_UNLOCK", "WAITING_TICKET_LIST", "WAITING_TICKET_OPTIONS", "WAITING_SUBMIT_BTN"]:
                    await asyncio.sleep(0.05)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 選擇日期 JS 錯誤: {result}")

        except Exception as e:
            print(f">>> [例外] select_date 發生錯誤: {e}")

    async def fill_data(self, active_tab):
        """[流程 3] 資料填寫頁面：無須填寫，極速點擊「下一步」略過"""
        import asyncio

        js_fill = """
        (function() {
            try {
                // 尋找畫面上所有的 button
                let btns = Array.from(document.querySelectorAll('button'));

                // 尋找文字包含「下一步」且沒有被 disabled 的按鈕
                let nextBtn = btns.find(b =>
                    b.innerText &&
                    b.innerText.includes('下一步') &&
                    !b.disabled &&
                    !b.classList.contains('disabled')
                );

                if (nextBtn) {
                    // 加入防連點機制，確保只點擊一次
                    if (!window._maxbot_data_submitted) {
                        nextBtn.click();
                        window._maxbot_data_submitted = true;
                        return "NEXT_CLICKED";
                    }
                    return "WAITING_TRANSITION"; // 已經點了，正在等網頁跳轉
                }

                return "WAITING_DOM"; // 還沒找到按鈕，網頁可能還在轉圈圈

            } catch(e) {
                return "ERROR|" + e.toString();
            }
        })();
        """

        try:
            result = await active_tab.evaluate(js_fill)

            if isinstance(result, str):
                if result == "NEXT_CLICKED":
                    print(">>> [Billboard] ⏩ 無須填寫資料！已極速點擊「下一步」略過，準備進入選位畫面...")
                    self.is_data_filled = True  # 放行，交接給下一個路由
                    await asyncio.sleep(0.3)    # 給網頁一點跳轉的時間

                elif result == "WAITING_TRANSITION":
                    # 已經點擊，安靜等待跳轉，不印出 Log 避免洗版
                    await asyncio.sleep(0.05)

                elif result == "WAITING_DOM":
                    # 尚未找到按鈕，持續極速掃描
                    if not hasattr(self, 'data_wait_count'):
                        self.data_wait_count = 0
                    self.data_wait_count += 1
                    if self.data_wait_count % 10 == 0:  # 每 0.5 秒印一次心跳
                        print(">>> [Billboard] ⏳ 等待「下一步」按鈕載入中...")
                    await asyncio.sleep(0.05)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 資料填寫 JS 錯誤: {result}")

        except Exception as e:
            print(f">>> [例外] fill_data 發生錯誤: {e}")

    async def select_seat(self, active_tab):
        """[流程 4] 掃描座位、精準關鍵字匹配，加入 DOM 延遲防護 (修復下一步卡死版)"""
        import json
        import asyncio
        import random

        target_count = self.ticket_number
        reload_interval = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.5))
        if reload_interval <= 0:
            reload_interval = 0.5

        raw_keyword = self.config.get("area_auto_select", {}).get(
            "area_keyword", "").strip()
        keyword_list = []
        if len(raw_keyword) > 0:
            try:
                if raw_keyword.startswith("[") and raw_keyword.endswith("]"):
                    keyword_list = json.loads(raw_keyword)
                else:
                    keyword_list = json.loads("[" + raw_keyword + "]")
            except:
                keyword_list = [raw_keyword]
        else:
            keyword_list = [""]

        js_keywords = json.dumps(keyword_list, ensure_ascii=False)

        js_seat = f"""
        (function() {{
            try {{
                const kws = {js_keywords};
                const targetCount = {target_count};
                const normalizeText = (str) => (str || "").toUpperCase().replace(/\\s+/g, '').replace(/-/g, '');

                // ==========================================
                // 階段 A：如果已經點選過座位，專心等待「下一步」按鈕解鎖
                // ==========================================
                if (window._maxbot_seats_clicked) {{
                    let btns = Array.from(document.querySelectorAll('button'));
                    let nextBtn = btns.find(b => 
                        b.innerText && 
                        (b.innerText.includes('下一步') || b.innerText.includes('確認')) && 
                        !b.disabled && 
                        !b.hasAttribute('disabled')
                    );

                    if (nextBtn) {{
                        nextBtn.click();
                        return "SEAT_SUBMITTED";
                    }}
                    return "WAITING_NEXT_BTN";
                }}

                // ==========================================
                // 階段 B：精準偵測「座位圖容器」是否已出現
                // ==========================================
                // 🚀 使用你提供的特徵：尋找帶有 cursor-grab (可拖曳) 的座位圖主容器
                let seatContainer = document.querySelector('div.cursor-grab');
                
                if (!seatContainer) {{
                    return "WAITING_SEAT_MAP"; // 容器連影子都沒有，網頁還在載入中
                }}

                // 容器出現了！我們只抓容器裡面的座位按鈕
                let allSeats = Array.from(seatContainer.querySelectorAll('button[title]'));

                if (allSeats.length === 0) {{
                    // 容器出現了，但按鈕還沒長出來 (給 React 0.5 秒的渲染時間)
                    if (!window._seatRenderWait) window._seatRenderWait = 0;
                    window._seatRenderWait++;
                    if (window._seatRenderWait > 10) {{ 
                        window._seatRenderWait = 0;
                        return "NO_SEAT"; // 0.5 秒還是沒按鈕，判定為空
                    }}
                    return "WAITING_SEATS_RENDER";
                }}

                // ==========================================
                // 階段 C：零延遲判定！座位已渲染，直接決勝負
                // ==========================================
                let availableSeats = allSeats.filter(btn => 
                    !btn.disabled && 
                    !btn.hasAttribute('disabled') &&
                    !btn.classList.contains('cursor-not-allowed')
                );

                // 🚨 只要空位數量不足，【不再等待 3 秒】，瞬間回傳觸發重整！
                if (availableSeats.length < targetCount) {{
                    return "NO_SEAT";
                }}

                // 關鍵字過濾
                let matchedSeats = [];
                if (kws.length === 0 || (kws.length === 1 && kws[0] === "")) {{
                    matchedSeats = availableSeats; 
                }} else {{
                    for (let seat of availableSeats) {{
                        let title = seat.getAttribute('title').trim().toUpperCase(); 
                        let normTitle = normalizeText(title); 
                        let rowPrefix = title.split('-')[0].trim(); 

                        let isMatch = false;
                        for (let k of kws) {{
                            let normK = normalizeText(k); 
                            if (normTitle === normK || rowPrefix === normK) {{
                                isMatch = true; 
                                break;
                            }}
                        }}
                        if (isMatch) matchedSeats.push(seat);
                    }}
                }}

                // 🚨 找不到符合關鍵字的座位，【不再等待】，瞬間回傳觸發重整！
                if (matchedSeats.length < targetCount) {{
                    return "NO_MATCHED_SEAT";
                }}

                // 找到足夠座位，發動點擊！
                for (let i = 0; i < targetCount; i++) {{
                    matchedSeats[i].click();
                }}

                window._maxbot_seats_clicked = true; 
                return "SEATS_CLICKED";

            }} catch(e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_seat)

            if isinstance(result, str):
                if result == "SEATS_CLICKED":
                    print(
                        f">>> [Billboard] 🎯 成功鎖定 {target_count} 個座位！等待下一步按鈕解鎖...")
                    await asyncio.sleep(0.05)

                elif result == "SEAT_SUBMITTED":
                    print(">>> [Billboard] 🎉 座位確認送出！準備進入結帳階段...")
                    self.is_seat_selected = True

                    if getattr(self, 'config', {}).get("advanced", {}).get("telegram_enable", False):
                        if not getattr(self, 'is_telegram_sent', False):
                            if hasattr(self, 'send_telegram_message'):
                                await self.send_telegram_message("🎟️ <b>[Billboard Live]</b> 🎉 座位點選成功！\n機器人已為您鎖定座位並進入結帳，請立刻回視窗付款！")
                            self.is_telegram_sent = True
                    await asyncio.sleep(0.5)

                elif result in ["NO_SEAT", "NO_MATCHED_SEAT"]:
                    msg = "該區已無空位" if result == "NO_SEAT" else "找不到符合關鍵字的座位"
                    print(
                        f">>> [Billboard] ❌ {msg}！{reload_interval} 秒後原地自動重刷...")
                    await asyncio.sleep(reload_interval)

                    await active_tab.reload()
                    await asyncio.sleep(1.0)

                elif result in ["WAITING_SEAT_MAP", "WAITING_AVAILABLE_SEATS", "WAITING_MATCHED_SEATS", "WAITING_NEXT_BTN"]:
                    if not hasattr(self, 'seat_wait_count'):
                        self.seat_wait_count = 0
                    self.seat_wait_count += 1
                    if self.seat_wait_count % 10 == 0:
                        print(f">>> [Billboard] ⏳ 座位圖載入與比對中 ({result})...")
                    await asyncio.sleep(0.05)

                elif result.startswith("ERROR"):
                    print(f">>> [DEBUG] 座位掃描 JS 錯誤: {result}")

        except Exception as e:
            print(f">>> [例外] select_seat 發生錯誤: {e}")

    def reset_all_states(self):
        """重置所有進度 (當需要退回重刷時呼叫)"""
        self.is_event_selected = False
        self.is_date_selected = False
        self.is_data_filled = False
        self.is_seat_selected = False
        self.is_success_notified = False


# ==========================================
# [Billboard 搶票]
# ==========================================


class TsgHawksBot:
    def __init__(self, driver, config):
        """初始化台鋼雄鷹機器人 (支援暫停與自動重啟版)"""
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        self.ticket_number = int(self.config.get("ticket_number", 1))
        self.last_url = ""

        self.is_event_selected = False
        self.is_area_selected = False
        self.is_seat_selected = False

        self.cooldown_until = 0
        self._wait_counts = {}

        # 🔥 建立 GUI 暫停檔案的偵測路徑
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

    def _log_wait(self, msg):
        """智能防洗版日誌系統"""
        self._wait_counts[msg] = self._wait_counts.get(msg, 0) + 1
        if self._wait_counts[msg] % 20 == 1:
            print(f">>> [TSG] ⏳ {msg}")

    def _parse_keyword(self, dict_key, default_val):
        """安全解析設定檔，防呆到底"""
        try:
            sub_dict = self.config.get(dict_key, {})
            if isinstance(sub_dict, dict):
                raw_val = sub_dict.get(dict_key.replace(
                    "auto_select", "keyword"), default_val)
            else:
                raw_val = default_val

            if isinstance(raw_val, list):
                res = str(raw_val[0]).strip() if len(raw_val) > 0 else ""
            else:
                raw_str = str(raw_val).strip()
                if raw_str.startswith("[") and raw_str.endswith("]"):
                    try:
                        res = str(json.loads(raw_str)[0]).strip()
                    except:
                        res = raw_str
                else:
                    res = raw_str
            return res.replace('"', '').replace("'", "").strip()
        except Exception:
            return default_val

    async def run(self):
        print(f">>> [TSG Hawks] 🦅 絕不漏接日誌版啟動！(目標: {self.ticket_number} 張)")

        while True:
            try:
                # 🔥 1. GUI 暫停功能偵測
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                current_url = await self.tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                if current_url != self.last_url:
                    print(f"\n>>> [系統] 網址變更: {current_url}")
                    self.last_url = current_url

                # 將目前網址傳給分發中心來決定任務
                await self.dispatch_action(current_url)

            except Exception as e:
                err_msg = str(e)
                if "1225" not in err_msg and "10061" not in err_msg and "10054" not in err_msg:
                    pass

            await asyncio.sleep(0.05)

    async def dispatch_action(self, current_url):
        if time.time() < self.cooldown_until:
            return

        upper_url = current_url.upper()

        # 🔥 2. 退回重啟機制：如果網址裡面沒有 BUYTICKET，代表我們被踢回首頁/場次頁了！
        if 'BUYTICKET' not in upper_url:
            # 如果我們身上還有之前選過位子的標記，強制洗掉它
            if self.is_event_selected or self.is_area_selected or self.is_seat_selected:
                print(">>> [系統] 🔄 偵測到退回場次選擇頁面！已清除進度鎖定，重新開始尋找場次！")
                self.is_event_selected = False
                self.is_area_selected = False
                self.is_seat_selected = False

            await self.select_event()

        # 如果網址有 BUYTICKET，代表已經在選區或選位的流程中
        else:
            if not self.is_area_selected:
                await self.select_area()
            elif not self.is_seat_selected:
                await self.select_seat()

    async def select_event(self):
        """[流程 1] 拆解式選擇場次 (加入自動重刷機制)"""
        import asyncio
        import time

        # 取得日期與 GUI 設定的刷新秒數
        date_keyword = self._parse_keyword("date_auto_select", "5/22")
        reload_interval = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.5))
        if reload_interval <= 0:
            reload_interval = 0.5

        if not date_keyword or '/' not in date_keyword:
            self._log_wait(f"日期格式錯誤: 【{date_keyword}】。請設定如 5/22")
            return

        try:
            month_int = int(date_keyword.split('/')[0])
            day_int = int(date_keyword.split('/')[1])
            month_str = str(month_int) + "月"
            day_str = str(day_int)
        except ValueError:
            self._log_wait(f"日期包含非數字: 【{date_keyword}】。請設定如 5/22")
            return

        # ==========================================
        # 步驟 A: 尋找並點擊月份
        # ==========================================
        js_month = f"""
        (function() {{
            let targetMonth = '{month_str}';
            let spans = Array.from(document.querySelectorAll('.tab_btn span.tab-a3'));
            if (spans.length === 0) return "NO_DOM";

            let target = spans.find(s => (s.textContent || "").includes(targetMonth));
            if (target) {{
                let btn = target.closest('.tab_btn');
                if (btn && !btn.classList.contains('active')) {{
                    btn.click();
                    return "CLICKED_MONTH";
                }}
                return "MONTH_IS_ACTIVE"; 
            }}
            return "MONTH_NOT_FOUND";
        }})();
        """

        try:
            res_month = await asyncio.wait_for(self.tab.evaluate(js_month), timeout=1.5)

            if res_month == "CLICKED_MONTH":
                print(f">>> [TSG] 📅 已切換至 【{month_str}】，等待場次更新...")
                self.cooldown_until = time.time() + 0.5
                return
            elif res_month == "MONTH_IS_ACTIVE":
                pass
            elif res_month == "NO_DOM":
                self._log_wait("等待網頁載入月份標籤...")
                return
            elif res_month == "MONTH_NOT_FOUND":
                # 🔥 找不到月份 ➔ 觸發重整！
                print(
                    f">>> [TSG] ⏳ 畫面上還沒有 【{month_str}】 的頁籤，{reload_interval} 秒後自動重刷...")
                await asyncio.sleep(reload_interval)
                await self.tab.reload()
                return
            else:
                self._log_wait(f"月份腳本未處理的狀態: {res_month}")
                return
        except asyncio.TimeoutError:
            print(">>> [警告] 尋找月份時腳本無回應，強制解除死鎖！")
            return

        # ==========================================
        # 步驟 B: 尋找日期並點擊購票
        # ==========================================
        js_date = f"""
        (function() {{
            let targetDay = '{day_str}';
            let dateSpans = Array.from(document.querySelectorAll('span.match-date-num'));
            if (dateSpans.length === 0) return "NO_DOM"; 

            let foundDay = false;
            for (let d of dateSpans) {{
                if ((d.textContent || "").trim() === targetDay) {{
                    foundDay = true;
                    let curr = d;
                    for (let i = 0; i < 8; i++) {{
                        if (!curr) break;
                        curr = curr.parentElement;
                        let btn = curr.querySelector('div.main_small-btn[role="button"]');
                        if (btn) {{
                            // 若按鈕被設定為 disabled 或 disable，代表無法購買
                            if (btn.classList.contains('disabled') || btn.classList.contains('disable')) {{
                                return "BTN_DISABLED";
                            }}
                            btn.click();
                            return "CLICKED_BUY";
                        }}
                    }}
                }}
            }}
            return foundDay ? "NO_BTN_NEAR_DATE" : "DATE_NOT_FOUND";
        }})();
        """

        try:
            res_date = await asyncio.wait_for(self.tab.evaluate(js_date), timeout=1.5)

            if res_date == "CLICKED_BUY":
                print(
                    f">>> [TSG] 🚀 成功點擊 {month_str} {day_str}號 的「購票」按鈕！進入下階段...")
                self.is_event_selected = True
                self.cooldown_until = time.time() + 1.0
            elif res_date == "NO_DOM":
                self._log_wait("等待場次日期載入...")

            # 🔥 找不到日期、按鈕還沒出、按鈕是灰色的 ➔ 通通觸發重整！
            elif res_date in ["NO_BTN_NEAR_DATE", "BTN_DISABLED", "DATE_NOT_FOUND"]:
                if res_date == "NO_BTN_NEAR_DATE":
                    msg = f"找到 {day_str} 號，但還沒有開放購票按鈕"
                elif res_date == "BTN_DISABLED":
                    msg = f"{day_str} 號的購票按鈕為灰色無法點擊"
                else:
                    msg = f"{month_str} 頁面中尚未出現 {day_str} 號的賽程"

                print(f">>> [TSG] ⏳ {msg}，{reload_interval} 秒後自動重刷...")
                await asyncio.sleep(reload_interval)
                await self.tab.reload()

            else:
                self._log_wait(f"日期腳本未處理的狀態: {res_date}")
        except asyncio.TimeoutError:
            print(">>> [警告] 尋找日期時腳本無回應，強制解除死鎖！")

    async def select_area(self):
        """[流程 2] 展開與選擇區域"""
        area_keyword = self._parse_keyword("area_auto_select", "2")
        target_count = self.ticket_number

        js_area = f"""
        (function() {{
            let infoBtn = document.querySelector('.seat-infor-open');
            let tableExists = document.querySelector('.table .tr_group');
            
            if (infoBtn && !tableExists) {{
                infoBtn.click();
                return "CLICKED_INFO";
            }}

            let rows = Array.from(document.querySelectorAll('.table .tr_group .tr'));
            if (rows.length === 0) return "WAITING_TABLE";

            let rawKeywordStr = "{area_keyword}";
            let keywords = rawKeywordStr.split(',').map(k => k.trim()).filter(k => k.length > 0);

            for (let r of rows) {{
                let cols = r.querySelectorAll('.td');
                if (cols.length >= 3) {{
                    let areaName = cols[0].textContent.trim();
                    let remainCount = parseInt(cols[1].textContent.trim(), 10);
                    let buyBtn = cols[2].querySelector('.small_icon-btn');

                    let isMatch = keywords.length === 0 || keywords.some(k => areaName.includes(k));

                    if (isMatch && remainCount >= {target_count} && buyBtn) {{
                        buyBtn.click();
                        return "CLICKED_AREA|" + areaName;
                    }}
                }}
            }}
            return "NO_MATCH";
        }})();
        """

        try:
            res = await asyncio.wait_for(self.tab.evaluate(js_area), timeout=1.5)
            if res == "CLICKED_INFO":
                self.cooldown_until = time.time() + 0.3
            elif res.startswith("CLICKED_AREA|"):
                area_name = res.split("|")[1]
                print(f">>> [TSG] 🏟️ 成功鎖定並點擊區域：【{area_name}】")
                self.is_area_selected = True
                self.cooldown_until = time.time() + 1.0
            elif res == "WAITING_TABLE":
                self._log_wait("等待區域表格展開...")
            elif res == "NO_MATCH":
                self._log_wait(
                    f"找不到關鍵字 '{area_keyword}' 且張數 ({target_count}) 足夠的區域...")
            else:
                self._log_wait(f"選區腳本未處理狀態: {res}")
        except asyncio.TimeoutError:
            pass

    async def select_seat(self):
        """[流程 3] 座位選擇 (加入二維座標分群演算法，就近包場)"""
        import asyncio
        import time

        target_count = self.ticket_number
        reload_interval = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.5))
        if reload_interval <= 0:
            reload_interval = 0.5

        js_seat = f"""
        (function() {{
            try {{
                const targetCount = {target_count};

                // 1. 確認按鈕保護：已點擊過座位才允許按確認
                if (window._tsg_seats_clicked) {{
                    let confirmBtn = document.querySelector('.ticket-buy-open');
                    if (confirmBtn && !confirmBtn.disabled && !confirmBtn.classList.contains('disabled')) {{
                        confirmBtn.click();
                        return "CLICKED_CONFIRM";
                    }}
                    return "WAITING_CONFIRM_BTN";
                }}

                let rows = Array.from(document.querySelectorAll('.seat_list .flex.h-7'));
                if (rows.length === 0) return "WAITING_SEATS";

                let allAvailableSeats = [];
                let seatsToClick = [];

                // 2. 賦予座標並尋找絕對連號
                for (let rIdx = 0; rIdx < rows.length; rIdx++) {{
                    let row = rows[rIdx];
                    let seats = Array.from(row.children);
                    let currentContiguous = [];
                    
                    for (let cIdx = 0; cIdx < seats.length; cIdx++) {{
                        let seat = seats[cIdx];
                        // 尋找真實座位框架
                        let inner = seat.classList.contains('seat_frame') ? seat : seat.querySelector('.seat_frame');
                        let html = seat.outerHTML.toLowerCase();
                        
                        // 判斷是否為空位
                        let isAvailable = inner && !html.includes('sold') && !html.includes('disabled');

                        if (isAvailable) {{
                            // 記錄每個空位的 DOM 與二維座標 (排, 列)
                            let seatData = {{ el: inner, r: rIdx, c: cIdx }};
                            allAvailableSeats.push(seatData); 
                            currentContiguous.push(seatData);
                            
                            // 若找到完美連號，立刻鎖定並跳出！
                            if (currentContiguous.length === targetCount && seatsToClick.length === 0) {{
                                seatsToClick = [...currentContiguous];
                            }}
                        }} else {{
                            // 遇到走道或已售出，連號中斷
                            currentContiguous = [];
                        }}
                    }}
                }}

                // 3. 總量檢查
                if (allAvailableSeats.length < targetCount) {{
                    return "NOT_ENOUGH_SEATS_TOTAL";
                }}

                let isScattered = false;
                
                // 4. 備案：就近分群演算法 (當找不到完美連號時)
                if (seatsToClick.length === 0) {{
                    isScattered = true;
                    let bestSpread = Infinity;
                    let bestCluster = [];

                    // 將每個空位輪流當作「中心點」
                    for (let i = 0; i < allAvailableSeats.length; i++) {{
                        let center = allAvailableSeats[i];
                        
                        // 計算所有空位到此中心點的「曼哈頓距離」並排序
                        // (排的物理距離通常比較遠，所以跨排的權重設為 2)
                        let sortedByDistance = [...allAvailableSeats].sort((a, b) => {{
                            let distA = Math.abs(a.r - center.r) * 2 + Math.abs(a.c - center.c);
                            let distB = Math.abs(b.r - center.r) * 2 + Math.abs(b.c - center.c);
                            return distA - distB;
                        }});

                        // 抓取離這個中心點最近的 N 個座位 (包含自己)
                        let cluster = sortedByDistance.slice(0, targetCount);
                        
                        // 計算這個群組的總擴散程度 (分數越低代表越密集)
                        let spread = cluster.reduce((sum, s) => sum + Math.abs(s.r - center.r) * 2 + Math.abs(s.c - center.c), 0);
                        
                        if (spread < bestSpread) {{
                            bestSpread = spread;
                            bestCluster = cluster;
                        }}
                    }}
                    seatsToClick = bestCluster;
                }}

                // 5. 發動點擊
                for (let s of seatsToClick) {{
                    s.el.click();
                }}

                window._tsg_seats_clicked = true;
                return isScattered ? "CLICKED_CLUSTER" : "CLICKED_CONTIGUOUS";

            }} catch(e) {{
                return "ERROR|" + e.toString();
            }}
        }})();
        """

        try:
            res = await asyncio.wait_for(self.tab.evaluate(js_seat), timeout=1.5)

            if res == "CLICKED_CONTIGUOUS":
                print(f">>> [TSG] 🎯 成功鎖定 {target_count} 個【完美連號】座位！等待確認...")
                self.cooldown_until = time.time() + 0.5

            elif res == "CLICKED_CLUSTER":
                print(
                    f">>> [TSG] ⚠️ 無法湊齊同排連號，已啟動空間演算法：成功鎖定 {target_count} 個【距離最近】的座位！")
                self.cooldown_until = time.time() + 0.5

            elif res == "CLICKED_CONFIRM":
                print(f">>> [TSG] 🎉 選位確認送出！請接手處理後續結帳！")
                self.is_seat_selected = True
                self.cooldown_until = time.time() + 2.0

            elif res == "WAITING_SEATS":
                self._log_wait("等待座位圖載入...")

            elif res == "WAITING_CONFIRM_BTN":
                self._log_wait("座位已點選，等待「確認選位」按鈕解鎖...")

            elif res == "NOT_ENOUGH_SEATS_TOTAL":
                print(
                    f">>> [TSG] ❌ 該區總空位不足 {target_count} 張！{reload_interval} 秒後自動重整...")
                await asyncio.sleep(reload_interval)
                await self.tab.reload()

            elif res.startswith("ERROR"):
                print(f">>> [DEBUG] 選位腳本出錯: {res}")

            else:
                self._log_wait(f"選位腳本未處理狀態: {res}")

        except asyncio.TimeoutError:
            pass
# ==========================================
# [台鋼雄鷹 搶票]
# ==========================================


class NolBot:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 狀態變數鎖
        self.is_activity_clicked = False
        self.is_gate_passed = False
        self.is_date_selected = False
        self.is_seat_selected = False

        # 日期關鍵字設定 (例如 "2")
        self.date_keyword = str(self.config.get(
            "date_auto_select", {}).get("date_keyword", "2")).strip()
        self.refresh_sec = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.1))

    async def run(self):
        print(
            f">>> [NOL 公園半自動] 機器人啟動！(目標張數: {self.ticket_number} | 鎖定日期: {self.date_keyword})")
        print(">>> [系統] 🛡️ 已啟動「動態分頁追蹤」與「手動接管無縫接軌」模式！")
        import asyncio

        while True:
            try:
                # 🔥 核心修正 1：永遠抓取「最後開啟/最上層」的分頁
                # 如果你手動開了新分頁，機器人會瞬間把視角切換到你的新分頁！
                active_tab = self.driver.tabs[-1]

                current_url = await active_tab.evaluate("window.location.href")

                if current_url and current_url != self.last_url:
                    print(f">>> [系統] 偵測到頁面切換: {current_url}")
                    self.last_url = current_url

                if current_url:
                    # 將 active_tab 傳遞下去，確保機器人操作的是正確的分頁
                    await self.dispatch_action(current_url, active_tab)

            except Exception as e:
                pass

            await asyncio.sleep(0.05)  # 極速迴圈

    async def dispatch_action(self, url, active_tab):
        """NOL 任務分發中心 (修正圖層判斷優先級，完美支援上一頁)"""
        upper_url = url.upper()

        if 'WORLD.NOL.COM' in upper_url:
            await self.step1_activity_page(active_tab)

        elif 'TICKETS.INTERPARK.COM/GATES' in upper_url:
            await self.step2_waiting_gate(active_tab)

        elif 'WAITINGSERVICESESSION.ASP' in upper_url:
            if not hasattr(self, 'queue_wait_log'):
                self.queue_wait_log = 0
            self.queue_wait_log += 1
            if self.queue_wait_log % 40 == 0:
                print(
                    ">>> [NOL-排隊] 🚶‍♂️ 正在神聖的排隊序列中！(機器人已進入待命保護模式，絕對不會重整，請靜候綠條跑完...)")
            import asyncio
            await asyncio.sleep(0.05)

        elif 'GPOTICKET.GLOBALINTERPARK.COM' in upper_url and 'BOOKMAIN.ASP' in upper_url:

            js_check_phase = """
            (function() {
                try {
                    let doc = document;
                    let frame = document.getElementById('ifrmBookStep');
                    if (frame && frame.contentWindow && frame.contentWindow.document) {
                        doc = frame.contentWindow.document;
                    }

                    let divMain = doc.getElementById('divBookMain') || document.getElementById('divBookMain');
                    let divSeat = doc.getElementById('divBookSeat') || document.getElementById('divBookSeat');
                    
                    let mainDisplay = divMain ? window.getComputedStyle(divMain).display : 'none';
                    let seatDisplay = divSeat ? window.getComputedStyle(divSeat).display : 'none';

                    // 🔥 核心修正：優先判斷日期圖層！
                    // 只要 divBookMain 顯示在畫面上，就必定是日期階段！
                    if (mainDisplay !== 'none') {
                        return "DATE_PHASE";
                    } 
                    // 只有當日期圖層確定被隱藏 (display: none)，才輪到座位階段！
                    else if (seatDisplay !== 'none') {
                        return "SEAT_PHASE";
                    }
                    
                    return "WAITING";
                } catch(e) { return "WAITING"; }
            })();
            """
            import asyncio
            phase = await active_tab.evaluate(js_check_phase)

            if phase == "DATE_PHASE":
                # 退回日期頁時，解開座位的點擊鎖
                if getattr(self, 'is_seat_selected', False):
                    self.is_seat_selected = False
                    try:
                        await active_tab.evaluate("window._nol_seat_clicked = false;")
                    except:
                        pass

                await self.step3_select_date(active_tab)

            elif phase == "SEAT_PHASE":
                await self.step4_select_seat(active_tab)

            else:
                await asyncio.sleep(0.05)

    # ---------------------------------------------------------
    # 核心邏輯實作區 (全部加入 active_tab 參數)
    # ---------------------------------------------------------

    async def step1_activity_page(self, active_tab):
        """[第一階段] 關閉底部彈窗並點擊 Buy Now"""
        js_activity = """
        (function() {
            try {
                let closeBtn = document.querySelector('button.nds-e-modal-bottom-sheet__actionButton');
                if (closeBtn) closeBtn.click();

                let buyBtn = document.querySelector('main > div > div > div > button');
                if (!buyBtn) {
                    let allBtns = Array.from(document.querySelectorAll('button'));
                    buyBtn = allBtns.find(b => (b.innerText || "").includes('Buy now'));
                }

                if (buyBtn) {
                    if (!buyBtn.disabled && !buyBtn.classList.contains('disabled:cursor_not-allowed')) {
                        buyBtn.click();
                        return "CLICKED_BUY";
                    }
                    return "WAITING_BUY_ENABLE";
                }
                return "WAITING_DOM";
            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """
        import asyncio
        result = await active_tab.evaluate(js_activity)
        if result == "CLICKED_BUY":
            print(">>> [NOL] 🚀 成功點擊「Buy now」！準備進入排隊閘門...")
            await asyncio.sleep(0.5)

    async def step2_waiting_gate(self, active_tab):
        """[第二階段] 排隊閘門 (伺服器對時極限狙擊版：屬性強拆 + 穿透點擊)"""
        js_gate = """
        (function() {
            try {
                // 精準鎖定排隊閘門的按鈕
                let btn = document.querySelector('div.buttons > button') || 
                          document.querySelector('#root > div > main > div > div > div.buttons > button');
                
                if (btn) {
                    let isDisabled = btn.disabled || 
                                     btn.classList.contains('_disabled_10rzo_34') || 
                                     btn.hasAttribute('disabled');
                    let btnText = (btn.innerText || "").toUpperCase();
                    
                    // 只要沒有 disabled 屬性，或者文字改變，就視為開賣
                    let isOpen = !isDisabled || btnText.includes("BOOK NOW");

                    if (isOpen) {
                        // ==========================================
                        // 🔥 狙擊發動：強拆防護網與穿透點擊 (對抗 React 渲染延遲)
                        // ==========================================
                        
                        // 1. 暴力扒掉所有可能阻擋點擊的屬性與 Class
                        btn.removeAttribute('disabled');
                        btn.classList.remove('_disabled_10rzo_34');
                        btn.style.pointerEvents = "auto"; 
                        
                        // 2. 聚焦並原生點擊
                        btn.focus(); 
                        btn.click();
                        
                        // 3. 終極穿透：發送現代化的 PointerEvent (能騙過多數 React onClick 綁定)
                        let pointerDown = new PointerEvent('pointerdown', { bubbles: true, cancelable: true, pointerType: 'mouse' });
                        let pointerUp = new PointerEvent('pointerup', { bubbles: true, cancelable: true, pointerType: 'mouse' });
                        let clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
                        
                        btn.dispatchEvent(pointerDown);
                        btn.dispatchEvent(pointerUp);
                        btn.dispatchEvent(clickEvent);

                        return "SNIPER_CLICKED";
                    }
                    return "WAITING_OPEN";
                }
                return "WAITING_DOM";
            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """

        import asyncio
        result = await active_tab.evaluate(js_gate)

        if result == "SNIPER_CLICKED":
            print(">>> [NOL] ⚡ 開賣瞬間捕捉！防護網已強拆，穿透點擊成功發射！")
            await asyncio.sleep(1.0)  # 給予跳轉緩衝，避免重複擊發

        elif result == "WAITING_OPEN":
            if not hasattr(self, 'gate_wait_log'):
                self.gate_wait_log = 0
            self.gate_wait_log += 1
            if self.gate_wait_log % 20 == 0:
                print(">>> [NOL] ⏳ 狙擊手就位... 監控伺服器對時與按鈕狀態中...")

            # 極速監控：維持 0.05 秒的超高頻率掃描
            await asyncio.sleep(0.05)

        elif result == "WAITING_DOM":
            await asyncio.sleep(0.05)

    async def step3_select_date(self, active_tab):
        """[第三階段] 專職：日期選擇 (修復無限重複點擊 Bug)"""
        clean_date_keyword = self.date_keyword.replace(
            '"', '').replace("'", "").strip()

        js_date = f"""
        (function() {{
            try {{
                let doc = document;
                let frame = document.getElementById('ifrmBookStep');
                let targetWin = window;

                if (frame && frame.contentWindow && frame.contentWindow.document) {{
                    doc = frame.contentWindow.document;
                    targetWin = frame.contentWindow;
                }}

                if (!targetWin._ipHooked_Date) {{
                    targetWin._lastAlert = "";
                    targetWin.originalAlert = targetWin.alert;
                    targetWin.alert = function(msg) {{ targetWin._lastAlert = msg; }};
                    targetWin._ipHooked_Date = true;
                }}
                if (targetWin._lastAlert !== "") {{
                    let msg = targetWin._lastAlert;
                    targetWin._lastAlert = ""; 
                    window._nol_date_clicked = false;
                    window._nol_next_clicked = false;
                    return "ALERT|" + msg;
                }}

                const targetDateRaw = '{clean_date_keyword}';
                const targetDateNum = parseInt(targetDateRaw.replace(/[^0-9]/g, ''), 10);
                
                let dateCells = Array.from(doc.querySelectorAll('a#CellPlayDate, a[name="CellPlayDate"]'))
                                .concat(Array.from(document.querySelectorAll('a#CellPlayDate, a[name="CellPlayDate"]')));

                if (dateCells.length > 0) {{
                    let foundDate = false;
                    for (let cell of dateCells) {{
                        let cellText = (cell.childNodes.length > 0 && cell.childNodes[0].nodeType === 3) 
                                     ? cell.childNodes[0].nodeValue : cell.innerText;
                        let cellNum = parseInt(cellText.replace(/[^0-9]/g, ''), 10);

                        if (!isNaN(cellNum) && !isNaN(targetDateNum) && cellNum === targetDateNum) {{
                            foundDate = true;
                            
                            if (!window._nol_date_clicked) {{
                                cell.click();
                                window._nol_date_clicked = true;
                                return "DATE_CLICKED|" + cellNum;
                            }}

                            let nextBtn = doc.querySelector('#LargeNextBtnImage') || document.querySelector('#LargeNextBtnImage') || 
                                          doc.querySelector('img[src*="btn_next_on"]') || document.querySelector('img[src*="btn_next_on"]');
                            if (nextBtn) {{
                                if (!window._nol_next_clicked) {{
                                    let parentA = nextBtn.closest('a');
                                    parentA ? parentA.click() : nextBtn.click();
                                    window._nol_next_clicked = true;
                                    window._nol_next_click_time = Date.now();
                                    return "NEXT_CLICKED";
                                }}
                            }}

                            // 放寬防卡死時間到 5 秒，避免誤觸發打斷網頁載入
                            if (window._nol_next_clicked && (Date.now() - window._nol_next_click_time > 5000)) {{
                                window._nol_next_clicked = false;
                            }}
                            return "WAITING_TRANSITION";
                        }}
                    }}
                    if (!foundDate) return "DATE_NOT_FOUND";
                }}
                return "WAITING_DOM";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        import asyncio
        result = await active_tab.evaluate(js_date)

        if isinstance(result, str):
            if result.startswith("ALERT|"):
                print(f">>> [系統] 💥 攔截到警告: 【{result.split('|')[1]}】，已解除鎖定。")
                self.is_date_selected = False  # 被退回就取消通關標記
                await asyncio.sleep(0.1)

            elif result.startswith("DATE_CLICKED|"):
                print(
                    f">>> [NOL-日期] 📅 已點擊日期「{result.split('|')[1]}號」，尋找下一步...")

            elif result == "NEXT_CLICKED":
                print(">>> [NOL-日期] 🚀 已點擊下一步！強制鎖定，將控制權切換至座位掃描...")
                self.is_date_selected = True  # 🔥 核心修正：蓋上通關印章！

            elif result == "DATE_NOT_FOUND":
                if not hasattr(self, 'date_not_found_log'):
                    self.date_not_found_log = 0
                self.date_not_found_log += 1
                if self.date_not_found_log % 20 == 0:
                    print(f">>> [NOL-日期] ⚠️ 找不到設定的日期: {clean_date_keyword}")

    async def step4_select_seat(self, active_tab):
        """[第四階段] 專職：座位選擇 (IFrame 穿透 + 全狀態捕捉)"""
        js_seat = """
        (function() {
            try {
                let doc = document;
                let frame = document.getElementById('ifrmBookStep');
                if (frame && frame.contentWindow) {
                    try { doc = frame.contentWindow.document; } catch(e) {}
                }

                // 1. 判斷是否真的切換到座位圖層了 (解決網頁延遲問題)
                let divSeat = doc.getElementById('divBookSeat') || document.getElementById('divBookSeat');
                if (!divSeat || window.getComputedStyle(divSeat).display === 'none') {
                    return "WAITING_PHASE_SWITCH";
                }

                // 2. 尋找第一層 iframe (ifrmSeat)
                let ifrmSeat = doc.getElementById('ifrmSeat') || document.getElementById('ifrmSeat');
                if (!ifrmSeat) return "WAITING_IFRAME_1";

                let seatDoc1;
                try {
                    seatDoc1 = ifrmSeat.contentWindow.document;
                    // 攔截 Alert
                    if (!ifrmSeat.contentWindow._ipHooked_Seat) {
                        ifrmSeat.contentWindow._lastAlert = "";
                        ifrmSeat.contentWindow.originalAlert = ifrmSeat.contentWindow.alert;
                        ifrmSeat.contentWindow.alert = function(msg) { ifrmSeat.contentWindow._lastAlert = msg; };
                        ifrmSeat.contentWindow._ipHooked_Seat = true;
                    }
                    if (ifrmSeat.contentWindow._lastAlert !== "") {
                        let msg = ifrmSeat.contentWindow._lastAlert;
                        ifrmSeat.contentWindow._lastAlert = "";
                        window._nol_seat_clicked = false;
                        return "ALERT|" + msg;
                    }
                } catch(e) { return "WAITING_IFRAME_1_READY"; }

                // 3. 尋找第二層 iframe (ifrmSeatDetail)
                let seatDoc2 = seatDoc1; // 預設使用第一層
                let ifrmSeatDetail = seatDoc1.getElementById('ifrmSeatDetail');
                if (ifrmSeatDetail) {
                    try {
                        seatDoc2 = ifrmSeatDetail.contentWindow.document;
                    } catch(e) { return "WAITING_IFRAME_2_READY"; }
                }

                // 4. 靈活抓取空位 (同時掃描兩層，防呆)
                let availableSeats = Array.from(seatDoc2.querySelectorAll('span.SeatN'));
                if (availableSeats.length === 0) availableSeats = Array.from(seatDoc1.querySelectorAll('span.SeatN'));
                if (availableSeats.length === 0) availableSeats = Array.from(doc.querySelectorAll('span.SeatN'));

                let seatMapTable = seatDoc2.querySelector('#TmgsTable') || seatDoc1.querySelector('#TmgsTable');
                
                if (seatMapTable || availableSeats.length > 0) {
                    if (availableSeats.length > 0) {
                        if (!window._nol_seat_clicked) {
                            availableSeats[0].click();
                            window._nol_seat_clicked = true; 
                        }
                        
                        // 找下一步按鈕 (可能在第一層或外層)
                        let nextBtn = seatDoc1.querySelector('#NextStepImage') || seatDoc1.querySelector('img[src*="btn_seat_confirm"]') ||
                                      doc.querySelector('#NextStepImage') || doc.querySelector('img[src*="btn_seat_confirm"]');
                        if (nextBtn) {
                            let parentA = nextBtn.closest('a');
                            parentA ? parentA.click() : nextBtn.click();
                            return "SEAT_SELECTED";
                        }
                        return "WAITING_NEXT_BTN";
                    } else {
                        window._nol_seat_clicked = false; 
                        return "NO_SEATS_LEFT";
                    }
                }
                return "WAITING_SEAT_MAP";
            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """
        import asyncio
        result = await active_tab.evaluate(js_seat)

        if isinstance(result, str):
            if result.startswith("ALERT|"):
                print(f">>> [系統] 💥 座位攔截: 【{result.split('|')[1]}】，準備點擊下一個！")
                await active_tab.evaluate("window._nol_seat_clicked = false;")
                await asyncio.sleep(0.1)

            elif result == "SEAT_SELECTED":
                print(">>> [NOL-座位] 🎯 成功抓取座位並送出！等待跳轉...")
                await asyncio.sleep(0.5)

            elif result == "NO_SEATS_LEFT":
                if not hasattr(self, 'seat_wait_log'):
                    self.seat_wait_log = 0
                self.seat_wait_log += 1
                if self.seat_wait_log % 20 == 0:
                    print(">>> [NOL-座位] ❌ 畫面上已無可用座位 (全為 SeatR)，等待釋票中...")

            # 🔥 終極修正：將所有漏網的狀態全部捕捉，並立刻印出 Log！
            elif result in [
                "WAITING_IFRAME_1", "WAITING_IFRAME_2",
                "WAITING_IFRAME_1_READY", "WAITING_IFRAME_2_READY",
                "WAITING_SEAT_MAP", "WAITING_PHASE_SWITCH", "WAITING_NEXT_BTN"
            ]:
                if not hasattr(self, 'seat_dom_log'):
                    self.seat_dom_log = 0
                self.seat_dom_log += 1
                # % 10 == 1 代表一進來就會立刻印出第一次，之後每 0.5 秒印一次
                if self.seat_dom_log % 10 == 1:
                    print(f">>> [NOL-座位] 🔍 載入座位圖中... (當前防禦層狀態: {result})")
                await asyncio.sleep(0.05)

            elif result.startswith("ERROR|"):
                print(f">>> [DEBUG] 座位選擇發生 JavaScript 錯誤: {result}")
                await asyncio.sleep(0.2)

# ==========================================
# [公園 搶票 半自動]
# ==========================================


class NolBot_AUTO:

    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 狀態變數鎖
        self.is_activity_clicked = False
        self.is_gate_passed = False
        self.is_date_selected = False
        self.is_seat_selected = False

        # 日期關鍵字設定 (例如 "2")
        self.date_keyword = str(self.config.get(
            "date_auto_select", {}).get("date_keyword", "2")).strip()
        self.refresh_sec = float(self.config.get(
            "advanced", {}).get("auto_reload_page_interval", 0.1))

    async def run(self):
        print(
            f">>> [NOL 公園全自動] 機器人啟動！(目標張數: {self.ticket_number} | 鎖定日期: {self.date_keyword})")
        print(">>> [系統] 🛡️ 已啟動「動態分頁追蹤」與「手動接管無縫接軌」模式！")
        import asyncio

        while True:
            try:
                active_tab = self.driver.tabs[-1]
                current_url = await active_tab.evaluate("window.location.href")

                # 動態調整掃描頻率
                loop_delay = 0.05
                if "BOOKMAIN.ASP" in current_url.upper():
                    loop_delay = 0.03  # 進入選位區，全力衝刺
                elif "WAITING" in current_url.upper():
                    loop_delay = 0.5   # 排隊中，放慢速度降低 CPU 負載與特徵

                await self.dispatch_action(current_url, active_tab)
                await asyncio.sleep(loop_delay)
            except:
                await asyncio.sleep(0.1)

    async def dispatch_action(self, url, active_tab):
        """NOL 任務分發中心 (修正圖層判斷優先級，完美支援上一頁)"""
        upper_url = url.upper()

        if 'WORLD.NOL.COM' in upper_url:
            await self.step1_activity_page(active_tab)

        elif 'TICKETS.INTERPARK.COM/GATES' in upper_url:
            await self.step2_waiting_gate(active_tab)

        elif 'WAITINGSERVICESESSION.ASP' in upper_url:
            if not hasattr(self, 'queue_wait_log'):
                self.queue_wait_log = 0
            self.queue_wait_log += 1
            if self.queue_wait_log % 40 == 0:
                print(
                    ">>> [NOL-排隊] 🚶‍♂️ 正在神聖的排隊序列中！(機器人已進入待命保護模式，絕對不會重整，請靜候綠條跑完...)")
            import asyncio
            await asyncio.sleep(0.05)

        elif 'GPOTICKET.GLOBALINTERPARK.COM' in upper_url and 'BOOKMAIN.ASP' in upper_url:

            js_check_phase = """
            (function() {
                try {
                    let doc = document;
                    let seatFrame = document.getElementById('ifrmSeat');
                    let seatDoc = seatFrame && seatFrame.contentWindow ? seatFrame.contentWindow.document : null;

                    // 1. 穿透檢查：驗證碼是否真實可見？
                    let captchaDiv = doc.querySelector('.capchaInner');
                    if (!captchaDiv && seatDoc) {
                        captchaDiv = seatDoc.querySelector('.capchaInner');
                    }

                    if (captchaDiv) {
                        // 🔥 嚴格檢查：必須不是 display: none 且 visibility 不是 hidden
                        let style = window.getComputedStyle(captchaDiv);
                        if (seatDoc && captchaDiv.ownerDocument === seatDoc) {
                            style = seatDoc.defaultView.getComputedStyle(captchaDiv);
                        }
                        
                        if (style.display !== 'none' && style.visibility !== 'hidden' && captchaDiv.offsetWidth > 0) {
                            return "CAPTCHA_PHASE";
                        }
                    }

                    // 2. 如果驗證碼消失了，才判斷是日期還是座位階段
                    let divMain = doc.getElementById('divBookMain');
                    let divSeat = doc.getElementById('divBookSeat');
                    
                    let mainDisplay = divMain ? window.getComputedStyle(divMain).display : 'none';
                    let seatDisplay = divSeat ? window.getComputedStyle(divSeat).display : 'none';

                    if (mainDisplay !== 'none') {
                        return "DATE_PHASE";
                    } 
                    else if (seatDisplay !== 'none') {
                        return "SEAT_PHASE";
                    }
                    
                    return "WAITING";
                } catch(e) { return "WAITING"; }
            })();
            """
            import asyncio
            phase = await active_tab.evaluate(js_check_phase)

            if phase == "CAPTCHA_PHASE":
                await self.step3_5_solve_captcha(active_tab)

            elif phase == "DATE_PHASE":
                if getattr(self, 'is_seat_selected', False) or getattr(self, 'is_area_selected', False):
                    print(">>> [系統] 偵測到返回操作！啟動 2.5 秒防禦冷卻，清洗機器人特徵...")
                    self.is_seat_selected = False
                    self.is_area_selected = False
                    await asyncio.sleep(3)  # 🔥 強制大洗牌冷卻
                    try:
                        await active_tab.evaluate("window._nol_seat_clicked = false;")
                    except:
                        pass
                await self.step3_select_date(active_tab)

            elif phase == "SEAT_PHASE":
                # 🔥 新增：如果還沒選過區域，就先去選區域！
                if not getattr(self, 'is_area_selected', False):
                    await self.step3_8_select_area(active_tab)
                else:
                    await self.step4_select_seat(active_tab)

            else:
                await asyncio.sleep(0.05)

    # ---------------------------------------------------------
    # 核心邏輯實作區 (全部加入 active_tab 參數)
    # ---------------------------------------------------------

    async def step1_activity_page(self, active_tab):
        """[第一階段] 關閉底部彈窗並點擊 Buy Now"""
        js_activity = """
        (function() {
            try {
                let closeBtn = document.querySelector('button.nds-e-modal-bottom-sheet__actionButton');
                if (closeBtn) closeBtn.click();

                let buyBtn = document.querySelector('main > div > div > div > button');
                if (!buyBtn) {
                    let allBtns = Array.from(document.querySelectorAll('button'));
                    buyBtn = allBtns.find(b => (b.innerText || "").includes('Buy now'));
                }

                if (buyBtn) {
                    if (!buyBtn.disabled && !buyBtn.classList.contains('disabled:cursor_not-allowed')) {
                        buyBtn.click();
                        return "CLICKED_BUY";
                    }
                    return "WAITING_BUY_ENABLE";
                }
                return "WAITING_DOM";
            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """
        import asyncio
        result = await active_tab.evaluate(js_activity)
        if result == "CLICKED_BUY":
            print(">>> [NOL] 🚀 成功點擊「Buy now」！準備進入排隊閘門...")
            await asyncio.sleep(0.5)

    async def step2_waiting_gate(self, active_tab):
        """[第二階段] 排隊閘門 (伺服器對時極限狙擊 + 20CPS 脈衝盲狙備用方案)"""
        js_gate = """
        (function() {
            try {
                // 精準鎖定排隊閘門的按鈕
                let btn = document.querySelector('div.buttons > button') || 
                          document.querySelector('#root > div > main > div > div > div.buttons > button');
                
                if (btn) {
                    let isDisabled = btn.disabled || 
                                     btn.classList.contains('_disabled_10rzo_34') || 
                                     btn.hasAttribute('disabled');
                    let btnText = (btn.innerText || "").toUpperCase();
                    
                    // 🛡️ 防禦升級：擴大判定範圍。只要出現以下任何字眼，都視為開賣！
                    let isOpen = !isDisabled || 
                                 btnText.includes("BOOK NOW") || 
                                 btnText.includes("GET TICKET") || 
                                 btnText.includes("BUY") ||
                                 btnText === "예매하기";

                    if (isOpen) {
                        // ==========================================
                        // 🔥 狙擊發動：強拆防護網與穿透點擊
                        // ==========================================
                        btn.removeAttribute('disabled');
                        btn.classList.remove('_disabled_10rzo_34');
                        btn.style.pointerEvents = "auto"; 
                        
                        btn.focus(); 
                        btn.click();
                        
                        let pointerDown = new PointerEvent('pointerdown', { bubbles: true, cancelable: true, pointerType: 'mouse' });
                        let pointerUp = new PointerEvent('pointerup', { bubbles: true, cancelable: true, pointerType: 'mouse' });
                        let clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
                        
                        btn.dispatchEvent(pointerDown);
                        btn.dispatchEvent(pointerUp);
                        btn.dispatchEvent(clickEvent);

                        return "SNIPER_CLICKED";
                    } else {
                        // ==========================================
                        // 🔫 備用方案 (Plan B)：20 CPS 脈衝盲狙
                        // ==========================================
                        // 就算我們判定還沒開賣，依然每 0.05 秒對它發送一次最基本的點擊。
                        // 只要網站偷偷解鎖，這發盲狙就能立功！
                        try { btn.click(); } catch(e) {}

                        return "WAITING_OPEN";
                    }
                }
                return "WAITING_DOM";
            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """

        import asyncio
        result = await active_tab.evaluate(js_gate)

        if result == "SNIPER_CLICKED":
            print(">>> [NOL-排隊] ⚡ 開賣瞬間捕捉！防護網已強拆，穿透點擊成功發射！")
            await asyncio.sleep(1.0)  # 給予跳轉緩衝，避免重複擊發

        elif result == "WAITING_OPEN":
            if not hasattr(self, 'gate_wait_log'):
                self.gate_wait_log = 0
            self.gate_wait_log += 1
            if self.gate_wait_log % 20 == 0:
                print(">>> [NOL-排隊] ⏳ 狙擊手就位... (同步啟動 20次/秒 盲狙模式探測中)")

            # 極速監控：維持 0.05 秒的超高頻率掃描與盲狙
            await asyncio.sleep(0.05)

        elif result == "WAITING_DOM":
            await asyncio.sleep(0.05)

    async def step3_select_date(self, active_tab):
        """[第三階段] 專職：日期選擇 (修復無限重複點擊 Bug)"""
        clean_date_keyword = self.date_keyword.replace(
            '"', '').replace("'", "").strip()

        js_date = f"""
        (function() {{
            try {{
                let doc = document;
                let frame = document.getElementById('ifrmBookStep');
                let targetWin = window;

                if (frame && frame.contentWindow && frame.contentWindow.document) {{
                    doc = frame.contentWindow.document;
                    targetWin = frame.contentWindow;
                }}

                if (!targetWin._ipHooked_Date) {{
                    targetWin._lastAlert = "";
                    targetWin.originalAlert = targetWin.alert;
                    targetWin.alert = function(msg) {{ targetWin._lastAlert = msg; }};
                    targetWin._ipHooked_Date = true;
                }}
                if (targetWin._lastAlert !== "") {{
                    let msg = targetWin._lastAlert;
                    targetWin._lastAlert = ""; 
                    window._nol_date_clicked = false;
                    window._nol_next_clicked = false;
                    return "ALERT|" + msg;
                }}

                const targetDateRaw = '{clean_date_keyword}';
                const targetDateNum = parseInt(targetDateRaw.replace(/[^0-9]/g, ''), 10);
                
                let dateCells = Array.from(doc.querySelectorAll('a#CellPlayDate, a[name="CellPlayDate"]'))
                                .concat(Array.from(document.querySelectorAll('a#CellPlayDate, a[name="CellPlayDate"]')));

                if (dateCells.length > 0) {{
                    let foundDate = false;
                    for (let cell of dateCells) {{
                        let cellText = (cell.childNodes.length > 0 && cell.childNodes[0].nodeType === 3) 
                                     ? cell.childNodes[0].nodeValue : cell.innerText;
                        let cellNum = parseInt(cellText.replace(/[^0-9]/g, ''), 10);

                        if (!isNaN(cellNum) && !isNaN(targetDateNum) && cellNum === targetDateNum) {{
                            foundDate = true;
                            
                            if (!window._nol_date_clicked) {{
                                cell.click();
                                window._nol_date_clicked = true;
                                return "DATE_CLICKED|" + cellNum;
                            }}

                            let nextBtn = doc.querySelector('#LargeNextBtnImage') || document.querySelector('#LargeNextBtnImage') || 
                                          doc.querySelector('img[src*="btn_next_on"]') || document.querySelector('img[src*="btn_next_on"]');
                            if (nextBtn) {{
                                if (!window._nol_next_clicked) {{
                                    let parentA = nextBtn.closest('a');
                                    parentA ? parentA.click() : nextBtn.click();
                                    window._nol_next_clicked = true;
                                    window._nol_next_click_time = Date.now();
                                    return "NEXT_CLICKED";
                                }}
                            }}

                            // 放寬防卡死時間到 5 秒，避免誤觸發打斷網頁載入
                            if (window._nol_next_clicked && (Date.now() - window._nol_next_click_time > 5000)) {{
                                window._nol_next_clicked = false;
                            }}
                            return "WAITING_TRANSITION";
                        }}
                    }}
                    if (!foundDate) return "DATE_NOT_FOUND";
                }}
                return "WAITING_DOM";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """
        import asyncio
        result = await active_tab.evaluate(js_date)

        if isinstance(result, str):
            if result.startswith("ALERT|"):
                print(f">>> [系統] 💥 攔截到警告: 【{result.split('|')[1]}】，已解除鎖定。")
                self.is_date_selected = False  # 被退回就取消通關標記
                await asyncio.sleep(0.1)

            elif result.startswith("DATE_CLICKED|"):
                print(
                    f">>> [NOL-日期] 📅 已點擊日期「{result.split('|')[1]}號」，尋找下一步...")

            elif result == "NEXT_CLICKED":
                print(">>> [NOL-日期] 🚀 已點擊下一步！強制鎖定，將控制權切換至座位掃描...")
                self.is_date_selected = True  # 🔥 核心修正：蓋上通關印章！

            elif result == "DATE_NOT_FOUND":
                if not hasattr(self, 'date_not_found_log'):
                    self.date_not_found_log = 0
                self.date_not_found_log += 1
                if self.date_not_found_log % 20 == 0:
                    print(f">>> [NOL-日期] ⚠️ 找不到設定的日期: {clean_date_keyword}")

    async def step3_5_solve_captcha(self, active_tab):
        """[第 3.5 階段] 專職：破解防不當訂票驗證碼 (修復 display:none 對焦與打字亂碼 Bug)"""
        import asyncio
        import base64
        import re
        import random

        js_captcha = """
        (function() {
            try {
                let doc = document;
                let frame = document.getElementById('ifrmSeat');
                if (frame && frame.contentWindow) {
                    doc = frame.contentWindow.document;
                }

                let captchaImg = doc.getElementById('imgCaptcha');
                let captchaInput = doc.getElementById('txtCaptcha');
                
                // 如果找不到元素，直接跳出等 DOM 載入
                if (!captchaImg || !captchaInput) return "WAITING_DOM";

                // 檢查圖片是否已經載入 base64
                if (!captchaImg.src || !captchaImg.src.includes('base64')) {
                    return "WAITING_IMG";
                }

                // 如果已經標記為送出中
                if (window._nol_captcha_submitted) {
                    return "SUBMITTING_WAIT";
                }

                return "CAPTCHA_PENDING|" + captchaImg.src;

            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """

        try:
            result = await active_tab.evaluate(js_captcha)

            if isinstance(result, str):
                if result.startswith("WAITING_"):
                    await asyncio.sleep(0.1)
                    return

                elif result == "SUBMITTING_WAIT":
                    check_fail_js = """
                    (function() {
                        let doc = document;
                        let frame = document.getElementById('ifrmSeat');
                        let win = window;
                        if (frame && frame.contentWindow) {
                            doc = frame.contentWindow.document;
                            win = frame.contentWindow;
                        }
                        
                        // 參考插件 hooks.js：檢查是否有產出 sessionID 或驗證通過標記
                        let isVerified = win.isCaptchaVerified === true || 
                                        (win.__BTS_GPO_INTERNAL__ && win.__BTS_GPO_INTERNAL__.store.captchaVerified);
                        
                        if (isVerified) return "SUCCESS";

                        let captchaDiv = doc.querySelector('.capchaInner');
                        let input = doc.getElementById('txtCaptcha');
                        
                        if (!captchaDiv || !input) return "SUCCESS";
                        
                        // 檢查是否因為錯誤被清空
                        if (input.value === "" && window._nol_captcha_submitted) {
                            window._nol_captcha_submitted = false;
                            return "FAILED";
                        }
                        return "WAITING";
                    })();
                    """
                    status = await active_tab.evaluate(check_fail_js)

                    if status == "FAILED":
                        print(">>> [NOL-驗證碼] ⚠️ 驗證碼錯誤，系統已自動刷新圖片，準備重新辨識...")
                        self.last_captcha_src = ""
                        await asyncio.sleep(0.3)
                    elif status == "SUCCESS":
                        print(">>> [NOL-驗證碼] 🎉 驗證成功！視窗已消失，準備進入區域選擇...")
                        await active_tab.evaluate("window._nol_captcha_submitted = false;")
                        await asyncio.sleep(0.2)
                    else:
                        await asyncio.sleep(0.1)
                    return

                elif result.startswith("CAPTCHA_PENDING|"):
                    base64_src = result.split("|")[1]

                    if getattr(self, 'last_captcha_src', '') == base64_src:
                        if not hasattr(self, 'captcha_wait_count'):
                            self.captcha_wait_count = 0
                        self.captcha_wait_count += 1
                        if self.captcha_wait_count > 10:
                            print(">>> [NOL-驗證碼] ⚠️ 驗證碼疑似卡住，嘗試自動點擊刷新按鈕換圖...")
                            refresh_js = """
                                (function() {
                                    let doc = document;
                                    let frame = document.getElementById('ifrmSeat');
                                    if (frame && frame.contentWindow) doc = frame.contentWindow.document;
                                    let refreshBtn = doc.querySelector('a.refreshBtn') || doc.querySelector('a[onclick*="fnCapchaRefresh"]');
                                    if (refreshBtn) refreshBtn.click();
                                })();
                            """
                            await active_tab.evaluate(refresh_js)
                            self.captcha_wait_count = 0
                            await asyncio.sleep(0.5)
                        return

                    self.last_captcha_src = base64_src
                    print(">>> [NOL-驗證碼] 🛡️ 遭遇驗證碼防線！啟動 ddddocr 嘗試破解...")

                    try:
                        if getattr(self, 'ocr', None) is None:
                            print(">>> [NOL-驗證碼] ⚙️ 首次載入 ddddocr 模型...")
                            import ddddocr
                            self.ocr = ddddocr.DdddOcr(show_ad=False)

                        img_data = base64_src.split(
                            ',')[1] if ',' in base64_src else base64_src
                        img_bytes = base64.b64decode(img_data)

                        raw_text = self.ocr.classification(img_bytes)
                        clean_text = re.sub(r'[^A-Za-z]', '', raw_text).upper()

                        print(
                            f">>> [NOL-驗證碼] 🤖 ddddocr 辨識結果: 【{clean_text}】 (原始: {raw_text}, 長度: {len(clean_text)})")

                        if len(clean_text) == 6:
                            # =========================================================
                            # 🔥 核心修正 1：針對 display:none 的暴力拆解與座標轉移
                            # =========================================================
                            get_coords_js = """
                            (function() {
                                let doc = document;
                                let frame = document.getElementById('ifrmSeat');
                                if (frame && frame.contentWindow) doc = frame.contentWindow.document;

                                let input = doc.getElementById('txtCaptcha');
                                let submitBtn = doc.querySelector('.capchaBtns a[onclick*="fnCheck"]');
                                
                                if (input && submitBtn) {
                                    // 強制拔除隱藏屬性，並主動上焦
                                    input.style.display = 'inline-block';
                                    input.value = '';
                                    input.focus();
                                    
                                    // 抓取包含 input 的外層框 .validationTxt (這是人類真正點擊的視覺目標)
                                    let clickTarget = doc.querySelector('.validationTxt') || input;
                                    
                                    function getAbsCenter(el) {
                                        el.scrollIntoView({block: 'center', inline: 'center'});
                                        let rect = el.getBoundingClientRect();
                                        
                                        // 預防萬一寬高是 0，改抓父元素的寬高
                                        if (rect.width === 0 && el.parentElement) {
                                            rect = el.parentElement.getBoundingClientRect();
                                        }
                                        
                                        let x = rect.left + rect.width / 2;
                                        let y = rect.top + rect.height / 2;
                                        let win = doc.defaultView || window;
                                        while (win && win !== window.top) {
                                            if (win.frameElement) {
                                                let fRect = win.frameElement.getBoundingClientRect();
                                                x += fRect.left;
                                                y += fRect.top;
                                            }
                                            win = win.parent;
                                        }
                                        return Math.round(x) + "|" + Math.round(y);
                                    }
                                    return getAbsCenter(clickTarget) + "|" + getAbsCenter(submitBtn);
                                }
                                return false;
                            })();
                            """
                            coords = await active_tab.evaluate(get_coords_js)

                            if coords and isinstance(coords, str):
                                parts = coords.split("|")
                                ix, iy = int(parts[0]), int(
                                    parts[1])  # 視覺輸入框容器的座標
                                sx, sy = int(parts[2]), int(
                                    parts[3])  # 送出按鈕的座標

                                import nodriver.cdp.input_ as cdp_input
                                mouse_btn = cdp_input.MouseButton.LEFT

                                # 1. 真實滑鼠移動並點擊「視覺容器」，觸發網頁原生對焦機制
                                await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseMoved", x=ix, y=iy))
                                await asyncio.sleep(0.05)
                                await active_tab.send(cdp_input.dispatch_mouse_event(type_="mousePressed", x=ix, y=iy, button=mouse_btn, click_count=1))
                                await asyncio.sleep(random.uniform(0.03, 0.08))
                                await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseReleased", x=ix, y=iy, button=mouse_btn, click_count=1))
                                await asyncio.sleep(0.1)  # 給予游標閃爍反應時間

                                # =========================================================
                                # 🔥 核心修正 2：淨化鍵盤敲擊事件，根除打字亂碼
                                # =========================================================
                                for char in clean_text:
                                    # 只送出 keyDown 與 keyUp，讓 Chrome 自行產生字元，不重複發送 char
                                    await active_tab.send(cdp_input.dispatch_key_event(type_="keyDown", text=char))
                                    await asyncio.sleep(random.uniform(0.01, 0.03))
                                    await active_tab.send(cdp_input.dispatch_key_event(type_="keyUp", text=char))
                                    # 擬真人打字停頓
                                    await asyncio.sleep(random.uniform(0.05, 0.12))

                                await asyncio.sleep(0.1)

                                # 3. 生成滑鼠軌跡滑動到「送出」按鈕
                                steps = random.randint(8, 12)
                                for i in range(steps):
                                    t = i / steps
                                    ease_t = t * (2 - t)
                                    cur_x = ix + (sx - ix) * \
                                        ease_t + random.uniform(-2, 2)
                                    cur_y = iy + (sy - iy) * \
                                        ease_t + random.uniform(-2, 2)
                                    await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseMoved", x=int(cur_x), y=int(cur_y)))
                                    await asyncio.sleep(random.uniform(0.008, 0.012))

                                await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseMoved", x=sx, y=sy))
                                await asyncio.sleep(random.uniform(0.05, 0.1))

                                # 4. 真實滑鼠點擊送出
                                await active_tab.send(cdp_input.dispatch_mouse_event(type_="mousePressed", x=sx, y=sy, button=mouse_btn, click_count=1))
                                await asyncio.sleep(random.uniform(0.05, 0.1))
                                await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseReleased", x=sx, y=sy, button=mouse_btn, click_count=1))

                                await active_tab.evaluate("window._nol_captcha_submitted = true;")
                                print(
                                    ">>> [NOL-驗證碼] 🚀 已透過 CDP 真實打字並送出！等待伺服器放行...")

                        else:
                            print(
                                f">>> [NOL-驗證碼] ⚠️ 辨識結果長度異常 ({len(clean_text)} 個字)，直接自動刷新換圖...")
                            refresh_js = """
                                (function() {
                                    let doc = document;
                                    let frame = document.getElementById('ifrmSeat');
                                    if (frame && frame.contentWindow) doc = frame.contentWindow.document;
                                    
                                    let refreshBtn = doc.querySelector('a.refreshBtn') || 
                                                     doc.querySelector('a[onclick*="fnCapchaRefresh"]');
                                    if (refreshBtn) refreshBtn.click();
                                })();
                            """
                            await active_tab.evaluate(refresh_js)
                            await asyncio.sleep(0.3)
                            self.last_captcha_src = ""

                    except Exception as ocr_err:
                        print(f">>> [NOL-驗證碼] ⚠️ 執行發生例外錯誤: {ocr_err}")
                        await asyncio.sleep(0.5)

        except Exception as e:
            pass

    async def step3_8_select_area(self, active_tab):
        """[第 3.8 階段] 區域選擇 (精準 JS 實體事件點擊 + 嚴格冷卻)"""
        import json
        import asyncio
        import random
        import time

        # 🛡️ 區域切換冷卻鎖：防 CF 偵測 (極度重要，保持 2.5 秒以上)
        if hasattr(self, 'last_area_action_time'):
            elapsed = time.time() - self.last_area_action_time
            if elapsed < 2.5:
                await asyncio.sleep(random.uniform(2.5, 3.5) - elapsed)

        area_auto_select = self.config.get("area_auto_select", {})
        raw_keyword = area_auto_select.get("area_keyword", "").strip()
        area_mode = area_auto_select.get("mode", "from top to bottom").lower()

        keyword_list = [
            raw_keyword] if raw_keyword and not raw_keyword.startswith("[") else []
        if raw_keyword.startswith("["):
            try:
                keyword_list = json.loads(raw_keyword)
            except:
                keyword_list = [""]

        clean_keywords = [str(k).replace('"', '').replace(
            "'", "").strip() for k in keyword_list]
        js_keywords = json.dumps(clean_keywords, ensure_ascii=False)

        # 直接使用 JS 觸發點擊，解決右側列表捲軸導致 CDP 算錯座標的問題
        js_click_area = f"""
        (function() {{
            try {{
                let doc = document;
                let frame = document.getElementById('ifrmSeat');
                if (frame && frame.contentWindow) doc = frame.contentWindow.document;

                const keywords = {js_keywords}.map(k => k.trim().toUpperCase());
                const mode = "{area_mode}";

                let blockLinks = Array.from(doc.querySelectorAll('a[href*="fnBlockSeatUpdate"], a[onclick*="fnBlockSeatUpdate"]'));
                
                if (blockLinks.length > 0) {{
                    let candidates = [];
                    for (let l of blockLinks) {{
                        let text = l.innerText.toUpperCase().replace(/\\s/g, '');
                        // 過濾沒票的區域
                        if (text.includes('(0座)') || text.includes('(0석)') || text.includes('(0SEATS)')) continue;

                        let isMatch = keywords.length === 0 || keywords[0] === "" || keywords.some(k => text.includes(k));
                        if (isMatch) candidates.push({{ el: l, text: text }});
                    }}

                    if (candidates.length > 0) {{
                        let target = candidates[0]; 
                        if (mode === "random") target = candidates[Math.floor(Math.random() * candidates.length)];
                        
                        // 滾動到可視範圍並發送真實的滑鼠點擊事件
                        target.el.scrollIntoView({{block: 'center', inline: 'center'}});
                        target.el.dispatchEvent(new MouseEvent('click', {{ bubbles: true, cancelable: true, view: window }}));
                        
                        return "CLICKED_BLOCK|" + target.text;
                    }} else {{
                        // 若無票，看看有沒有其他大標題可以點
                        let activeSelect = doc.querySelector('tr.selected span.select') || doc.querySelector('tr[class*="selected"] span.select');
                        if (activeSelect) {{
                            activeSelect.dispatchEvent(new MouseEvent('click', {{ bubbles: true, cancelable: true, view: window }}));
                            return "CLOSED_GRADE";
                        }}
                    }}
                }}

                // 如果還沒展開，點大標題
                let availSpans = Array.from(doc.querySelectorAll('tr span.select')).filter(s => !s.innerText.replace(/\\s/g, '').includes('0'));
                if (availSpans.length > 0) {{
                    let targetSpan = availSpans[0];
                    if (mode === "random") targetSpan = availSpans[Math.floor(Math.random() * availSpans.length)];
                    targetSpan.dispatchEvent(new MouseEvent('click', {{ bubbles: true, cancelable: true, view: window }}));
                    return "EXPANDED_GRADE";
                }}
                
                return "ALL_EMPTY";
            }} catch(e) {{ return "ERROR|" + e.toString(); }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_click_area)

            if isinstance(result, str):
                if result.startswith("CLICKED_BLOCK|"):
                    print(
                        f">>> [NOL-區域] 🖱️ 已成功點擊切換區域：【{result.split('|')[1]}】")
                    self.last_area_action_time = time.time()
                    self.is_area_selected = True
                    await asyncio.sleep(1.0)  # 給予 AJAX 載入座位圖的時間
                    return
                elif result in ["EXPANDED_GRADE", "CLOSED_GRADE"]:
                    self.last_area_action_time = time.time()
                    await asyncio.sleep(0.8)
                    return
        except Exception as e:
            pass

        if not getattr(self, 'is_area_selected', False):
            await asyncio.sleep(max(0.5, float(self.config.get("advanced", {}).get("auto_reload_page_interval", 0.5))))

    async def step4_select_seat(self, active_tab):
        """[第 4 階段] 座位選擇 (保留完美 CDP，精簡退場邏輯)"""
        import asyncio
        import random
        import time

        if not getattr(self, '_step4_entered', False):
            self._step4_entered = True
            self._step4_enter_time = time.time()
        # 區域點進後看到座位有元素的延遲時間 原始 0.8秒
        if time.time() - self._step4_enter_time < 0.35:  # 改成 0.35 秒
            await asyncio.sleep(0.075)  # 這裡的等待頻率也可以從 0.1 壓到 0.05，讓它偵測更敏銳
            return

        if hasattr(self, 'last_cdp_click_time'):
            if time.time() - self.last_cdp_click_time < 2.5:
                await asyncio.sleep(0.1)
                return

        js_seat = """
        (function() {
            try {
                let doc = document;
                let frame = document.getElementById('ifrmBookStep');
                if (frame && frame.contentWindow) { try { doc = frame.contentWindow.document; } catch(e) {} }

                let ifrmSeat = doc.getElementById('ifrmSeat') || document.getElementById('ifrmSeat');
                if (!ifrmSeat) return "WAITING_IFRAME_1";

                let seatDoc1;
                try {
                    seatDoc1 = ifrmSeat.contentWindow.document;
                    if (!ifrmSeat.contentWindow._ipHooked_Seat) {
                        ifrmSeat.contentWindow._lastAlert = "";
                        ifrmSeat.contentWindow.originalAlert = ifrmSeat.contentWindow.alert;
                        ifrmSeat.contentWindow.alert = function(msg) { ifrmSeat.contentWindow._lastAlert = msg; };
                        ifrmSeat.contentWindow._ipHooked_Seat = true;
                    }
                    if (ifrmSeat.contentWindow._lastAlert !== "") {
                        let msg = ifrmSeat.contentWindow._lastAlert;
                        ifrmSeat.contentWindow._lastAlert = "";
                        window._nol_seat_clicked = false;
                        return "ALERT|" + msg;
                    }
                } catch(e) { return "WAITING_IFRAME_1_READY"; }

                let seatDoc2 = seatDoc1; 
                let ifrmSeatDetail = seatDoc1.getElementById('ifrmSeatDetail');
                if (ifrmSeatDetail) { try { seatDoc2 = ifrmSeatDetail.contentWindow.document; } catch(e) { return "WAITING_IFRAME_2_READY"; } }

                function getAbs(el, win) {
                    let rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) return null; 
                    let x = rect.left + rect.width / 2, y = rect.top + rect.height / 2;
                    while (win && win !== window.top) {
                        if (win.frameElement) {
                            let fRect = win.frameElement.getBoundingClientRect();
                            x += fRect.left; y += fRect.top;
                        }
                        win = win.parent;
                    }
                    return { x: Math.round(x), y: Math.round(y) };
                }

                let availableSeats = Array.from(seatDoc2.querySelectorAll('span.SeatN'));
                if (availableSeats.length === 0) availableSeats = Array.from(seatDoc1.querySelectorAll('span.SeatN'));

                if (seatDoc2.querySelector('#TmgsTable') || availableSeats.length > 0) {
                    if (availableSeats.length > 0) {
                        if (window._nol_seat_clicked) return "WAITING_CDP";
                        
                        // 找下一步 (Seat selection completed) 按鈕
                        let nextBtn = seatDoc1.querySelector('#NextStepImage') || seatDoc1.querySelector('img[src*="btn_seat_confirm"]');
                        if (nextBtn) {
                            let seatPos = getAbs(availableSeats[0], seatDoc2.defaultView || window);
                            let nextPos = getAbs(nextBtn.closest('a') || nextBtn, seatDoc1.defaultView || window);
                            if (!seatPos || !nextPos) return "WAITING_VISIBILITY";
                            
                            window._nol_seat_clicked = true; 
                            return "READY_TO_CDP|" + seatPos.x + "|" + seatPos.y + "|" + nextPos.x + "|" + nextPos.y;
                        }
                        return "WAITING_NEXT_BTN";
                    } else {
                        // 沒座位，直接回報空區，讓外層去點其他區域
                        window._nol_seat_clicked = false; 
                        return "NO_SEATS_LEFT";
                    }
                }
                return "WAITING_SEAT_MAP";
            } catch(e) { return "ERROR|" + e.toString(); }
        })();
        """

        try:
            result = await active_tab.evaluate(js_seat)

            if isinstance(result, str):
                import nodriver.cdp.input_ as cdp_input
                mouse_btn = cdp_input.MouseButton.LEFT

                if result.startswith("ALERT|"):
                    print(f">>> [系統] 💥 座位攔截: 【{result.split('|')[1]}】")
                    await active_tab.evaluate("window._nol_seat_clicked = false;")
                    self.last_cdp_click_time = 0
                    self._step4_entered = False
                    await asyncio.sleep(0.1)

                elif result.startswith("READY_TO_CDP|"):
                    parts = result.split("|")
                    sx, sy = float(parts[1]), float(parts[2])
                    nx, ny = float(parts[3]), float(parts[4])

                    print(">>> [NOL-座位] 🎯 座位確認！發動 CDP 極速連擊...")
                    try:
                        # === 1. 點擊座位 ===
                        await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseMoved", x=int(sx), y=int(sy)))
                        await asyncio.sleep(0.02)  # [原本 0.08] 極限 Hover 對焦
                        await active_tab.send(cdp_input.dispatch_mouse_event(type_="mousePressed", x=int(sx), y=int(sy), button=mouse_btn, click_count=1))
                        await asyncio.sleep(0.02)  # [原本 0.08] 極限按壓時間
                        await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseReleased", x=int(sx), y=int(sy), button=mouse_btn, click_count=1))

                        # 🔥 核心調整區：點位子與點結帳之間的間隔 🔥
                        # [原本 0.20] 縮短至 0.05 秒。
                        # 注意：不能設定為 0，必須給網頁 JS 一點點時間將座位標記為「已選取」，否則點結帳會跳出「請先選擇座位」的警告。
                        await asyncio.sleep(0.05)

                        # === 2. 點擊結帳 (Seat selection completed) ===
                        await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseMoved", x=int(nx), y=int(ny)))
                        await asyncio.sleep(0.02)  # [原本 0.10] 結帳按鈕極限 Hover
                        await active_tab.send(cdp_input.dispatch_mouse_event(type_="mousePressed", x=int(nx), y=int(ny), button=mouse_btn, click_count=1))
                        await asyncio.sleep(0.02)  # [原本 0.08] 極限按壓時間
                        await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseReleased", x=int(nx), y=int(ny), button=mouse_btn, click_count=1))

                        self.last_cdp_click_time = time.time()
                    except:
                        await active_tab.evaluate("window._nol_seat_clicked = false;")
                    await asyncio.sleep(0.5)

                elif result == "NO_SEATS_LEFT":
                    # 🚀 精簡退場：不再找按鈕，直接解除鎖定，控制權交回 step3_8
                    print(">>> [NOL-座位] ❌ 此區已空！準備切換下一個區域...")
                    self.is_area_selected = False
                    self._step4_entered = False
                    # 給予一點緩衝，避免瞬間切換
                    await asyncio.sleep(0.5)

        except Exception as e:
            pass
# ==========================================
# [公園 搶票 全自動]
# ==========================================


class FubonBot:
    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config

        # 1. 抓取路徑
        self.settings_path = config.get("config_filepath", "settings.json")

        # 🔥 新增這行 Debug Log，這能讓你立刻知道是誰的錯
        print(f">>> [系統檢查] 機器人目前綁定的設定檔路徑為: {self.settings_path}")

        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 狀態鎖變數
        self.is_date_selected = False
        self.is_area_selected = False
        self.is_seat_selected = False

        self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

        print(">>> [富邦悍將] 正在載入 ddddocr 辨識模型...")
        import ddddocr
        self.ocr = ddddocr.DdddOcr(show_ad=False)

    async def reload_config_if_changed(self):
        """讀取最新設定檔"""
        # 🔥 把寫死的字串，換成剛剛存好的動態變數
        settings_path = self.settings_path
        try:
            if not os.path.exists(settings_path):
                return
            with open(settings_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)

            # 同步更新變數
            for key in ["area_auto_select", "date_auto_select", "advanced", "keyword_exclude", "ticket_number"]:
                if key in new_config:
                    self.config[key] = new_config[key]
            self.ticket_number = int(new_config.get("ticket_number", 1))
        except:
            pass

    async def run(self):
        print(f">>> [富邦悍將] 機器人啟動！(目標張數: {self.ticket_number})")
        while True:
            try:
                if os.path.exists(self.PAUSE_FILE):
                    await asyncio.sleep(0.5)
                    continue

                current_url = await self.tab.evaluate("window.location.href")

                if current_url and current_url != self.last_url:
                    upper_url = current_url.upper()

                    # 1. 區域選擇頁 (UTK0204)
                    if 'UTK0204_' in upper_url:
                        pass  # 進入區域不重置日期鎖

                    # 2. 日期選擇頁 (UTK0201，嚴格排除 0204/0205)
                    elif 'UTK0201_' in upper_url and 'UTK0204_' not in upper_url and 'UTK0205_' not in upper_url:
                        if getattr(self, 'is_date_selected', False):
                            print(">>> [系統] 退回日期選擇頁，重置日期鎖！")
                            self.is_date_selected = False
                        await self.reload_config_if_changed()

                    # 3. 票數/座位圖選擇頁 (新增 UTK0203_)
                    elif ('UTK0202_' in upper_url or 'UTK0203_' in upper_url or 'UTK0205_' in upper_url) and getattr(self, 'is_seat_selected', False):
                        print(">>> [系統] 退回票數/座位頁，重置座位鎖！")
                        self.is_seat_selected = False

                    self.last_url = current_url

                if current_url:
                    await self.dispatch_action(current_url)

            except Exception as e:
                pass
            await asyncio.sleep(0.05)

    async def dispatch_action(self, url):
        """任務分發中心"""
        upper_url = url.upper()

        if 'UTK0204_' in upper_url:
            self.is_seat_selected = False
            if not getattr(self, 'is_area_selected', False):
                await self.select_area()

        elif 'UTK0201_' in upper_url and 'UTK0204_' not in upper_url:
            self.is_area_selected = False
            self.is_seat_selected = False
            if not getattr(self, 'is_date_selected', False):
                await self.select_date()

        # (新增 UTK0203_)
        elif 'UTK0202_' in upper_url or 'UTK0203_' in upper_url or 'UTK0205_' in upper_url:
            if not getattr(self, 'is_seat_selected', False):
                seat_success = await self.select_tickets()
                if seat_success:
                    import asyncio
                    await asyncio.sleep(0.5)

                    ocr_success = await self.process_captcha()

                    if ocr_success:
                        await self.tab.evaluate("let btn=document.querySelector('#addcart'); if(btn) btn.click();")
                    else:
                        print(">>> [系統] ⚠️ OCR 辨識失敗，解除座位鎖，準備重新選位！")
                        self.is_seat_selected = False

    async def select_date(self):
        """[第一階段] 日期選擇"""
        date_auto_select = self.config.get("date_auto_select", {})
        raw_keyword = date_auto_select.get("date_keyword", "").strip()
        js_keywords = json.dumps(
            [x.strip() for x in raw_keyword.split(',') if x.strip()], ensure_ascii=False)

        js_date = f"""
        (function() {{
            try {{
                const keywords = {js_keywords};
                let rows = Array.from(document.querySelectorAll('table tbody tr'));
                let candidates = [];

                for (let row of rows) {{
                    let btn = row.querySelector('button#buy_btn');
                    if (!btn) continue;

                    let btnText = (btn.innerText || "").toUpperCase();
                    if (btnText.includes('售完') || btn.disabled) continue;

                    let spanText = row.querySelector('td:nth-child(3) span');
                    let rowText = spanText ? spanText.innerText.toUpperCase() : row.innerText.toUpperCase();

                    let isMatch = keywords.length === 0;
                    if (!isMatch) {{
                        for (let k of keywords) {{
                            if (rowText.includes(k.toUpperCase())) {{
                                isMatch = true; break;
                            }}
                        }}
                    }}

                    if (isMatch && btnText.includes('購買')) {{
                        candidates.push(btn);
                    }}
                }}

                if (candidates.length > 0) {{
                    candidates[0].click();
                    return 1; // 成功點擊
                }}
                return 2; // 找不到或售完，需要重整
            }} catch(e) {{ return -1; }}
        }})();
        """
        result = await self.tab.evaluate(js_date)
        if result == 1:
            print(">>> [日期] 🎉 成功點擊購買！等待跳轉...")
            self.is_date_selected = True
            await asyncio.sleep(0.5)
        elif result == 2:
            base_wait = float(self.config.get("advanced", {}).get(
                "auto_reload_page_interval", 0.5))
            print(">>> [日期] 尚未開賣或已售完，準備刷新...")
            await self.tab.reload()
            await asyncio.sleep(base_wait if base_wait > 0 else 0.2)

    async def select_area(self):
        """[第二階段] 區域選擇 (Angular 穿透讀取 + 無敵字串清洗防呆)"""
        area_auto_select = self.config.get("area_auto_select", {})

        # ==========================================
        # 🔥 防呆 1：最強字串清洗機 (暴力拔除所有多餘的空白與引號)
        # ==========================================
        def parse_and_clean(raw_val):
            if not raw_val:
                return []
            # 如果傳進來就已經是陣列 (List)
            if isinstance(raw_val, list):
                # 連續脫掉 空白 -> 雙引號 -> 單引號 -> 空白
                return [str(x).strip().strip('"').strip("'").strip() for x in raw_val if str(x).strip()]

            # 如果傳進來是一長串字串
            val_str = str(raw_val).replace('，', ',').strip()

            # 嘗試解開像 '["A5", "A6"]' 這樣的 JSON 格式
            if val_str.startswith('[') and val_str.endswith(']'):
                import json
                try:
                    parsed = json.loads(val_str)
                    return [str(x).strip().strip('"').strip("'").strip() for x in parsed if str(x).strip()]
                except:
                    pass

            # 用逗號切開，並強制脫去每一項的引號
            return [x.strip().strip('"').strip("'").strip() for x in val_str.split(',') if x.strip()]

        # 清洗包含與排除的關鍵字
        raw_keyword = area_auto_select.get("area_keyword", "")
        k_list = parse_and_clean(raw_keyword)

        raw_exclude = self.config.get("keyword_exclude", "")
        e_list = parse_and_clean(raw_exclude)

        import json
        js_keywords = json.dumps(k_list, ensure_ascii=False)
        js_excludes = json.dumps(e_list, ensure_ascii=False)
        ticket_num = self.ticket_number

        js_area = f"""
        (function() {{
            try {{
                const keywords = {js_keywords};
                const excludes = {js_excludes};
                const reqNum = {ticket_num};
                
                let rows = Array.from(document.querySelectorAll('table tbody tr'));
                
                // 🔥 防呆 2：Angular 渲染防護
                if (rows.length === 0) return 0; 
                let hasData = rows.some(r => r.textContent.includes('區') || r.textContent.match(/\d/));
                if (!hasData) return 0; // 資料還沒生出來，原地等待！

                let candidates = [];

                for (let row of rows) {{
                    // 使用 textContent 穿透讀取
                    let fullText = (row.textContent || "").replace(/,/g, '').toUpperCase();
                    let areaTag = (row.getAttribute('data-area-tag') || "").toUpperCase();
                    fullText += " " + areaTag;

                    if (!fullText.includes('區') && !fullText.includes('票') && !fullText.includes('席')) continue;

                    // 1. 排除關鍵字
                    let isExcluded = false;
                    for (let exc of excludes) {{
                        if (exc && fullText.includes(exc.toUpperCase())) {{ isExcluded = true; break; }}
                    }}
                    if (isExcluded) continue;

                    // 2. 包含關鍵字
                    let isMatch = keywords.length === 0;
                    if (!isMatch) {{
                        for (let k of keywords) {{
                            if (k && fullText.includes(k.toUpperCase())) {{ isMatch = true; break; }}
                        }}
                    }}
                    
                    if (isMatch) {{
                        // 3. 判斷空位狀態評分
                        let seatText = "";
                        let seatTd = Array.from(row.querySelectorAll('td')).find(td => td.getAttribute('data-title') && td.getAttribute('data-title').includes('空位'));
                        
                        if (seatTd) {{
                            seatText = seatTd.textContent.trim();
                        }} else {{
                            let seatEl = row.querySelector('#SEAT');
                            if (seatEl) seatText = seatEl.textContent.trim();
                            else seatText = fullText; 
                        }}

                        let score = 0;
                        if (seatText.includes("熱賣中")) score = 3;
                        else if (seatText.includes("售完") || seatText.includes("已售完")) score = 1; 
                        else {{
                            let numMatch = seatText.match(/\d+/);
                            if (numMatch) {{
                                let num = parseInt(numMatch[0]);
                                if (num >= reqNum) score = 2; // 數量足夠
                                else score = 1.5; // 數量不足
                            }} else {{
                                score = 1;
                            }}
                        }}

                        candidates.push({{ element: row, score: score }});
                    }}
                }}

                if (candidates.length > 0) {{
                    candidates.sort((a, b) => b.score - a.score);
                    candidates[0].element.click();
                    return 1;
                }}
                
                return 2;
            }} catch(e) {{ return -1; }}
        }})();
        """
        import asyncio
        result = await self.tab.evaluate(js_area)

        if result == 1:
            print(">>> [區域] 👉 成功鎖定區域並點擊！")
            self.is_area_selected = True
            await asyncio.sleep(0.3)

        elif result == 0:
            if not hasattr(self, 'area_wait_log'):
                self.area_wait_log = 0
            self.area_wait_log += 1
            if self.area_wait_log % 10 == 0:
                print(">>> [區域] ⏳ 網頁資料載入中 (等待 Angular 渲染)...")
            await asyncio.sleep(0.1)

        elif result == 2:
            # 這裡顯示的是清洗過後乾淨的字串，不再有引號了
            clean_kws = ", ".join(k_list) if k_list else "任意"
            print(f">>> [區域] 畫面上沒有符合 [{clean_kws}] 的區域，刷新頁面...")
            await self.tab.reload()
            await asyncio.sleep(0.5)

    async def select_tickets(self):
        """[第三階段] 票數與座位選擇 (雙模式相容 + 強制鎖定全票 + 無差別空位辨識)"""
        ticket_num = self.ticket_number
        raw_exclude = self.config.get("keyword_exclude", "")

        # 清洗排除關鍵字 (支援陣列與字串)
        if isinstance(raw_exclude, list):
            e_list = [str(x).strip() for x in raw_exclude if str(x).strip()]
        else:
            e_list = [x.strip() for x in str(raw_exclude).replace(
                '，', ',').split(',') if x.strip()]

        import json
        js_excludes = json.dumps(e_list, ensure_ascii=False)

        js_tickets = f"""
        (function() {{
            try {{
                const targetTickets = {ticket_num};
                const excludes = {js_excludes};
                
                // =====================================
                // 模式 A：座位圖模式
                // =====================================
                let seatTable = document.querySelector('#TBL');
                if (seatTable) {{
                    
                    // 防禦 1：Angular 渲染確認
                    let allSeatsInTable = document.querySelectorAll('#TBL td[title]');
                    if (allSeatsInTable.length === 0) return 0; // 資料還在路上，原地等待！

                    // ==========================================
                    // 🔥 修正：強制鎖定「全票」並確實擊發
                    // ==========================================
                    let typeBtns = Array.from(document.querySelectorAll('div.seatype button, button.f1'));
                    let targetBtn = null;

                    // 優先策略：直接尋找包含「全票」的按鈕，且避開身心障礙
                    for (let btn of typeBtns) {{
                        let btnText = (btn.textContent || "").toUpperCase();
                        if (btnText.includes('全票') && !btnText.includes('身心') && !btnText.includes('障礙')) {{
                            targetBtn = btn;
                            break;
                        }}
                    }}

                    // 備用策略：如果真的沒有叫全票的，用排除法抓第一個合法的
                    if (!targetBtn) {{
                        for (let btn of typeBtns) {{
                            let isExc = false;
                            let btnText = (btn.textContent || "").toUpperCase();
                            for (let ex of excludes) {{
                                if (ex && btnText.includes(ex.toUpperCase())) {{ isExc = true; break; }}
                            }}
                            if (!isExc) {{ targetBtn = btn; break; }}
                        }}
                    }}
                    
                    // 霸道點擊：不管它是不是 active，為了確保系統有收到 setType 的訊號，直接再點一次！
                    if (targetBtn) {{
                        targetBtn.click();
                    }}
                    // ==========================================

                    // 防禦 2：無差別空位辨識法
                    function isAvailable(cell) {{
                        let bg = (cell.getAttribute('style') || "").toLowerCase();
                        let hasTitle = cell.hasAttribute('title');
                        let notSold = !bg.includes('people') && !bg.includes('lock');
                        let isEmptyIcon = bg.includes('empty');
                        let isClickable = bg.includes('cursor: pointer') || cell.style.cursor === 'pointer';
                        
                        return hasTitle && notSold && (isEmptyIcon || isClickable);
                    }}

                    // 尋找空位 (優先找連號)
                    let rows = document.querySelectorAll('#TBL tbody tr');
                    let targetSeats = [];
                    for (let row of rows) {{
                        let cells = row.querySelectorAll('td');
                        let consec = [];
                        for (let cell of cells) {{
                            if (isAvailable(cell)) {{
                                consec.push(cell);
                                if (consec.length === targetTickets) {{ targetSeats = consec; break; }}
                            }} else if (cell.hasAttribute('title') || (cell.getAttribute('style') || "").includes('people')) {{
                                consec = []; 
                            }}
                        }}
                        if (targetSeats.length > 0) break;
                    }}
                    
                    // 防呆：沒有連號就全場硬抓
                    if (targetSeats.length === 0) {{
                        let allEmpty = Array.from(document.querySelectorAll('#TBL td')).filter(c => isAvailable(c));
                        if (allEmpty.length >= targetTickets) {{
                            targetSeats = allEmpty.slice(0, targetTickets);
                        }}
                    }}

                    // 點擊座位並聚焦驗證碼
                    if (targetSeats.length === targetTickets) {{
                        targetSeats.forEach(s => s.click());
                        let chk = document.querySelector('#CHK') || document.querySelector('#ctl00_ContentPlaceHolder1_CHK');
                        if(chk) chk.focus();
                        return 1; // 成功
                    }}
                    return 2; // 真的是沒票了
                }}
                
                // =====================================
                // 模式 B：張數選擇模式 (無座位圖)
                // =====================================
                let rows = Array.from(document.querySelectorAll('table tbody tr'));
                if (rows.length <= 1) return 0; // 渲染防護

                for(let row of rows) {{
                    let rowText = (row.textContent || "").toUpperCase();
                    let isExc = false;
                    for (let ex of excludes) {{
                        if (ex && rowText.includes(ex.toUpperCase())) {{ isExc = true; break; }}
                    }}
                    if (isExc) continue;

                    let input = row.querySelector('input.numbox[type="number"]');
                    if (input && !input.disabled) {{
                        input.value = targetTickets;
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        if (typeof checkNum === "function") checkNum(input);
                        
                        let chk = document.querySelector('#CHK') || document.querySelector('#ctl00_ContentPlaceHolder1_CHK');
                        if(chk) chk.focus();
                        return 1;
                    }}
                }}
                return 2;

            }} catch(e) {{ return -1; }}
        }})();
        """
        import asyncio
        result = await self.tab.evaluate(js_tickets)

        if result == 1:
            print(f">>> [票數/座位] ✅ 成功鎖定 {ticket_num} 張「全票」並點選座位！準備 OCR...")
            self.is_seat_selected = True
            return True

        elif result == 0:
            if not hasattr(self, 'seat_wait_log'):
                self.seat_wait_log = 0
            self.seat_wait_log += 1
            if self.seat_wait_log % 10 == 0:
                print(">>> [票數/座位] ⏳ 座位圖渲染中，請稍候...")
            await asyncio.sleep(0.1)
            return False

        elif result == 2:
            print(f">>> [票數/座位] ❌ 殘念...剩餘空位不足 {ticket_num} 張！準備重新整理頁面...")
            try:
                base_wait = float(self.config.get("advanced", {}).get(
                    "auto_reload_page_interval", 0.5))
                if base_wait <= 0:
                    base_wait = 0.2
                await self.tab.reload()
                await asyncio.sleep(base_wait)
            except:
                pass
            return False

        return False

    async def process_captcha(self):
        """處理圖形驗證碼 (完整 Debug 版 + 圖片載入防護)"""
        print(">>> [OCR] 啟動驗證碼辨識程序...")
        js_get_image = """
            (function() {
                try {
                    var img = document.querySelector('#chk_pic');
                    if (!img) return "ERROR_NO_IMG";
                    // 檢查圖片是否真的載入完成了
                    if (!img.complete || img.naturalWidth === 0) return "ERROR_NOT_LOADED";
                    
                    var canvas = document.createElement('canvas');
                    canvas.width = img.naturalWidth || img.width;
                    canvas.height = img.naturalHeight || img.height;
                    var ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    return canvas.toDataURL('image/png').split(',')[1];
                } catch(e) {
                    return "ERROR_CANVAS";
                }
            })();
            """

        try:
            for attempt in range(3):
                import asyncio
                base64_data = await self.tab.evaluate(js_get_image)

                if base64_data == "ERROR_NO_IMG":
                    print(">>> [OCR] 找不到驗證碼圖片，網頁可能還沒載入完畢...")
                    await asyncio.sleep(0.5)
                    continue
                elif base64_data == "ERROR_NOT_LOADED":
                    print(">>> [OCR] 圖片還在轉圈圈，等它一下...")
                    await asyncio.sleep(0.5)
                    continue
                elif str(base64_data).startswith("ERROR_CANVAS") or not base64_data:
                    print(">>> [OCR] 畫布擷取失敗，可能被瀏覽器安全機制擋下。")
                    return False

                import base64
                img_bytes = base64.b64decode(base64_data)

                # 呼叫 ddddocr 進行辨識
                ocr_answer = self.ocr.classification(img_bytes)
                ocr_answer = ocr_answer.strip() if ocr_answer else ""
                print(f">>> [OCR] 第 {attempt + 1} 次辨識結果: '{ocr_answer}'")

                if len(ocr_answer) == 4:
                    js_fill = f"""
                        (function() {{
                            let el = document.querySelector('#CHK'); 
                            if(el) {{ 
                                el.value = '{ocr_answer}'; 
                                el.dispatchEvent(new Event('input', {{bubbles:true}})); 
                                el.dispatchEvent(new Event('change', {{bubbles:true}})); 
                                return true; 
                            }} 
                            return false;
                        }})();
                        """
                    if await self.tab.evaluate(js_fill):
                        print(f">>> [OCR] ✅ 已自動填入驗證碼: {ocr_answer}")
                        return True
                    else:
                        print(">>> [OCR] 找不到驗證碼輸入框 (#CHK)！")

                # 辨識失敗換圖
                print(">>> [OCR] ⚠️ 辨識長度不對，點擊圖片重新整理...")
                await self.tab.evaluate("let img = document.querySelector('#chk_pic'); if(img) img.click();")
                await asyncio.sleep(0.8)  # 換圖需要一點時間讀取

            return False
        except Exception as e:
            print(f">>> [OCR] 發生例外錯誤: {e}")
            return False
# ==========================================
# [富邦棒球搶票]
# ==========================================


class FunoneBot:
    """FunOne Tickets 專用機器人 (直攻張數選擇頁面掛機版)"""

    def __init__(self, driver, config):
        self.driver = driver
        self.tab = driver.main_tab
        self.config = config
        self.settings_path = config.get("config_filepath", "settings.json")
        self.ticket_number = int(config.get("ticket_number", 1))
        self.last_url = ""

        # 唯一的狀態鎖
        self.is_ticket_assigned = False

        # 暫停鎖
        import os
        try:
            import util
            self.PAUSE_FILE = os.path.join(
                util.get_app_root(), "MAXBOT_INT28_IDLE.txt")
        except:
            self.PAUSE_FILE = "MAXBOT_INT28_IDLE.txt"

    async def run(self):
        print(f">>> [FunOne] 機器人啟動！(目標張數: {self.ticket_number})")
        print(">>> [FunOne] 💡 戰術提示：請手動進入「目標區域」的張數選擇頁面，機器人會在此幫您掛機刷新撿漏！")
        import asyncio
        import os

        while True:
            try:
                # 1. 暫停攔截
                if os.path.exists(self.PAUSE_FILE):
                    if not getattr(self, 'is_printing_pause', False):
                        print("\n>>> [系統] ⏸️ 程式已暫停！等待您在 GUI 按下繼續...")
                        self.is_printing_pause = True
                    await asyncio.sleep(0.5)
                    continue
                self.is_printing_pause = False

                # 2. 確保連線活著
                if hasattr(self.driver, 'main_tab'):
                    self.tab = self.driver.main_tab
                active_tab = self.tab

                current_url = await active_tab.evaluate("window.location.href")
                if not current_url:
                    await asyncio.sleep(0.05)
                    continue

                # 3. 網址狀態機 (防呆解鎖與 SPA 狀態重置)
                if current_url != getattr(self, 'last_url', ''):
                    print(f">>> [路由] 偵測到頁面切換: {current_url}")
                    self.last_url = current_url

                    self.is_ticket_assigned = False

                    reset_js = """
                    (function() {
                        window._funone_ticket_added = false;
                        window._funone_agreed = false;
                        window._funone_submit_clicked = false;
                        window._funone_refresh_clicked = false;
                        window._funone_socket_refresh_clicked = false;
                    })();
                    """
                    try:
                        await active_tab.evaluate(reset_js)
                    except:
                        pass

                # =========================================================
                # 🔥 核心修復：放寬 URL 檢查，相容 has_map 與 no_map (無座位圖) 版型
                # =========================================================
                if '/purchase/purchase_choose_ticket_' in current_url.lower() or '/purchase/purchase_fill_form/' in current_url.lower():
                    await self.dispatch_action(active_tab)
                else:
                    await asyncio.sleep(0.1)

            except Exception as e:
                err_str = str(e)
                if "500" in err_str or "closed" in err_str:
                    await asyncio.sleep(0.1)
                else:
                    pass
            await asyncio.sleep(0.05)

    async def dispatch_action(self, active_tab):
        """[FunOne] 單一任務分發：只處理錯誤彈窗與選票階段"""
        js_scout = """
        (function() {
            try {
                let doc = document;
                
                // 1. 偵測錯誤彈窗 (最高優先級)
                let popups = document.querySelectorAll('div[role="dialog"]');
                for (let dialog of popups) {
                    if (dialog.offsetParent !== null) {
                        let text = dialog.innerText || "";
                        if (text.includes('失敗') || text.includes('售完') || text.includes('我知道了')) {
                            return "STAGE_ERROR";
                        }
                    }
                }

                // 2. 判斷是否在「選票數與結帳 / 開賣倒數」畫面
                let buyBtn = Array.from(doc.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('立即購買'));
                let refreshBtn = doc.querySelector('button.web_round_info_refresh');
                
                // 🔥 核心修改：擴大特徵偵測，相容「有座位圖」與「無座位圖(多票種清單)」兩種版型
                let hasMapContainer = doc.querySelector('.choose_ticket_has_map');
                let noMapContainer = doc.querySelector('.choose_ticket_no_seat');
                let plusSvg = doc.querySelector('svg path[d^="M11 13H6C5"]'); 
                
                if (buyBtn || refreshBtn || hasMapContainer || noMapContainer || plusSvg) {
                    if (window._funone_submit_clicked) {
                        return "STAGE_TICKET_DONE"; 
                    }
                    return "STAGE_TICKET"; 
                }

                return "WAITING_DOM";
            } catch(e) { return "ERROR"; }
        })();
        """
        import asyncio
        scout_result = await active_tab.evaluate(js_scout)

        if scout_result == "STAGE_ERROR":
            print(">>> [FunOne-系統] 💥 偵測到「購票失敗/售完」彈窗！重置狀態準備撿漏...")
            self.is_ticket_assigned = False
            await active_tab.reload()
            await asyncio.sleep(0.5)

        elif scout_result == "STAGE_TICKET":
            if not getattr(self, 'is_ticket_assigned', False):
                await self.select_tickets(active_tab)
            else:
                await asyncio.sleep(0.1)

        elif scout_result == "STAGE_TICKET_DONE":
            self.is_ticket_assigned = True
            await asyncio.sleep(0.1)

        elif scout_result == "WAITING_DOM":
            await asyncio.sleep(0.05)

    async def dispatch_action(self, active_tab):
        """[FunOne] 單一任務分發：只處理錯誤彈窗與選票階段"""
        js_scout = """
        (function() {
            try {
                let doc = document;
                
                // 1. 偵測錯誤彈窗 (最高優先級)
                let popups = document.querySelectorAll('div[role="dialog"]');
                for (let dialog of popups) {
                    if (dialog.offsetParent !== null) {
                        let text = dialog.innerText || "";
                        if (text.includes('失敗') || text.includes('售完') || text.includes('我知道了')) {
                            return "STAGE_ERROR";
                        }
                    }
                }

                // 2. 判斷是否在「選票數與結帳 / 開賣倒數」畫面
                let buyBtn = Array.from(doc.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('立即購買'));
                let refreshBtn = doc.querySelector('button.web_round_info_refresh');
                let plusSvg = doc.querySelector('svg path[d^="M11 13H6C5"]'); 
                
                if (buyBtn || refreshBtn || plusSvg) {
                    return "STAGE_TICKET";
                }

                return "WAITING_DOM";
            } catch(e) { return "ERROR"; }
        })();
        """
        import asyncio
        scout_result = await active_tab.evaluate(js_scout)

        if scout_result == "STAGE_ERROR":
            print(">>> [FunOne-系統] 💥 偵測到「購票失敗/售完」彈窗！重置狀態準備撿漏...")
            self.is_ticket_assigned = False
            await active_tab.reload()
            await asyncio.sleep(0.5)

        elif scout_result == "STAGE_TICKET":
            # 確保還沒結帳才進去執行
            if not getattr(self, 'is_ticket_assigned', False):
                await self.select_tickets(active_tab)
            else:
                await asyncio.sleep(0.1)

        elif scout_result == "WAITING_DOM":
            await asyncio.sleep(0.05)

    async def select_tickets(self, active_tab):
        """[唯一主力] 刷重整、分配張數、同意條款並送出 (相容多票種 Table 版型)"""
        import asyncio
        import json

        target_tickets = self.ticket_number

        base_interval = float(self.config.get("advanced", {}).get(
            "auto_reload_page_interval", 0.5) or 0.5)
        is_random = self.config.get("advanced", {}).get(
            "auto_reload_random_mode", False)
        jitter = float(self.config.get("advanced", {}).get(
            "auto_reload_random_range", 0.2) or 0.2) if is_random else 0.0

        area_auto_select = self.config.get("area_auto_select", {})
        raw_keyword = area_auto_select.get("area_keyword", "").strip()
        area_mode = area_auto_select.get("mode", "from top to bottom").lower()

        keyword_list = []
        if raw_keyword:
            try:
                if raw_keyword.startswith("["):
                    keyword_list = json.loads(raw_keyword)
                else:
                    keyword_list = json.loads("[" + raw_keyword + "]")
            except:
                keyword_list = [raw_keyword]
        clean_keywords = [str(k).replace('"', '').replace(
            "'", "").strip().upper() for k in keyword_list]

        raw_keyword_exclude = self.config.get("keyword_exclude", "").strip()
        exclude_list = []
        if raw_keyword_exclude:
            try:
                if raw_keyword_exclude.startswith("["):
                    exclude_list = json.loads(raw_keyword_exclude)
                else:
                    exclude_list = json.loads("[" + raw_keyword_exclude + "]")
            except:
                exclude_list = [raw_keyword_exclude]
        clean_excludes = [str(k).replace('"', '').replace(
            "'", "").strip().upper() for k in exclude_list]

        js_keywords = json.dumps(clean_keywords, ensure_ascii=False)
        js_excludes = json.dumps(clean_excludes, ensure_ascii=False)

        js_ticket = f"""
        (function() {{
            try {{
                let doc = document;
                const targetCount = {target_tickets};
                const keywords = {js_keywords};
                const excludes = {js_excludes};
                const mode = "{area_mode}";

                // ==========================================
                // 1. 開賣前倒數邏輯
                // ==========================================
                let refreshPageBtn = doc.querySelector('button.web_round_info_refresh');
                let waitBtn = Array.from(doc.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('開賣'));
                
                if (refreshPageBtn && waitBtn && waitBtn.disabled) {{
                    if (!window._funone_refresh_clicked) {{
                        refreshPageBtn.click();
                        window._funone_refresh_clicked = true;
                        return "REFRESH_PAGE_CLICKED";
                    }}
                    return "WAITING_REFRESH";
                }}

                let buyBtn = Array.from(doc.querySelectorAll('button')).find(b => b.innerText && b.innerText.includes('立即購買'));
                
                if (buyBtn) {{
                    let needsWait = false;

                    // ==========================================
                    // 2. 動作 A: 票種過濾與分配張數
                    // ==========================================
                    if (!window._funone_ticket_added) {{
                        
                        // 🔥 核心修改：相容「多票種 table 結構」與「單一票種 list 結構」
                        let rows = Array.from(doc.querySelectorAll('.choose_ticket_no_seat tbody tr')); 
                        if (rows.length === 0) {{
                            // 如果沒有 table，退回去找舊版的結構
                            rows = Array.from(doc.querySelectorAll('.choose_ticket_has_map ul li'));
                        }}
                        
                        if (rows.length === 0) return "WAITING_DOM"; // 畫面還沒長出來

                        let candidates = [];

                        for (let row of rows) {{
                            let typeEl = row.querySelector('.ticket_type') || row; // 如果沒有分類就拿整行
                            let priceEl = row.querySelector('.price');
                            let rowText = ((typeEl ? typeEl.innerText : "") + " " + (priceEl ? priceEl.innerText : "")).toUpperCase().replace(/,/g, '');
                            
                            // 過濾售完
                            let soldOutSpan = row.querySelector('.zone_sales_state');
                            let isSoldOut = soldOutSpan && soldOutSpan.innerText.includes('售完');
                            
                            // 排除與包含比對
                            let isExcluded = false;
                            if (excludes.length > 0 && excludes[0] !== "") {{
                                for (let exc of excludes) {{
                                    if (exc !== "" && rowText.includes(exc)) {{ isExcluded = true; break; }}
                                }}
                            }}
                            if (isExcluded) continue;

                            let isMatch = false;
                            if (keywords.length === 0 || keywords[0] === "") {{
                                isMatch = true; 
                            }} else {{
                                for (let k of keywords) {{
                                    if (k !== "" && rowText.includes(k)) {{ isMatch = true; break; }}
                                }}
                            }}
                            
                            if (isMatch) candidates.push({{ el: row, text: rowText, isSoldOut: isSoldOut }});
                        }}

                        if (candidates.length === 0) return "NO_MATCH_TICKET";

                        // 選出最終目標
                        let targetRowObj = candidates[0];
                        if (mode === "random") {{
                            targetRowObj = candidates[Math.floor(Math.random() * candidates.length)];
                        }} else if (mode === "from bottom to top") {{
                            targetRowObj = candidates[candidates.length - 1];
                        }}

                        let targetRow = targetRowObj.el;

                        // 判斷售完與刷新撿漏
                        if (targetRowObj.isSoldOut) {{
                            let socketRefreshBtn = doc.querySelector('button.socket_round_info_refresh');
                            if (socketRefreshBtn && !socketRefreshBtn.disabled) {{
                                if (!window._funone_socket_refresh_clicked) {{
                                    socketRefreshBtn.click();
                                    window._funone_socket_refresh_clicked = true;
                                    return "SOCKET_REFRESH_CLICKED|" + targetRowObj.text;
                                }}
                                return "WAITING_REFRESH";
                            }}
                            return "SOLD_OUT_NO_BTN|" + targetRowObj.text; 
                        }}
                        
                        // 🔥 核心修改：精準鎖定輸入框右邊那個加號按鈕 (通常是該區塊的第二個按鈕)
                        let plusSvg = targetRow.querySelector('svg path[d^="M11 13H6C5"]');
                        if (plusSvg) {{
                            let plusBtn = plusSvg.closest('button');
                            if (plusBtn && !plusBtn.disabled) {{
                                for(let i=0; i<targetCount; i++) {{ plusBtn.click(); }}
                                window._funone_ticket_added = true;
                                needsWait = true; 
                            }}
                        }}
                    }}

                    // ==========================================
                    // 3. 動作 B: 勾選同意條款
                    // ==========================================
                    if (!window._funone_agreed) {{
                        let checkSvg = doc.querySelector('.form svg path[d^="M9.54999 15.15"]'); // 加上 .form 避免選錯
                        if (checkSvg) {{
                            let checkWrapper = checkSvg.closest('div') || checkSvg.parentElement;
                            if (checkWrapper) {{
                                checkWrapper.click();
                                window._funone_agreed = true;
                                needsWait = true; 
                            }}
                        }}
                    }}

                    if (needsWait) return "PROCESSING_INPUTS";

                    // ==========================================
                    // 4. 動作 C: 送出！(CDP 座標獲取)
                    // ==========================================
                    if (window._funone_ticket_added && window._funone_agreed) {{
                        if (!buyBtn.disabled && !buyBtn.classList.contains('v-btn--disabled')) {{
                            if (!window._funone_submit_clicked) {{
                                window._funone_submit_clicked = true;
                                
                                function getAbsCenter(el) {{
                                    el.scrollIntoView({{block: 'center', inline: 'center'}});
                                    let rect = el.getBoundingClientRect();
                                    return Math.round(rect.left + rect.width / 2) + "|" + Math.round(rect.top + rect.height / 2);
                                }}
                                
                                return "READY_TO_SUBMIT|" + getAbsCenter(buyBtn);
                            }}
                            return "WAITING_TRANSITION";
                        }}
                        return "WAITING_BTN_ENABLE";
                    }}
                }}
                return "WAITING_DOM";
            }} catch(e) {{ return "ERROR"; }}
        }})();
        """

        try:
            result = await active_tab.evaluate(js_ticket)
            import random
            human_delay = max(0.05, base_interval +
                              random.uniform(-jitter, jitter))

            if result == "REFRESH_PAGE_CLICKED":
                if not hasattr(self, 'refresh_log_count'):
                    self.refresh_log_count = 0
                self.refresh_log_count += 1
                if self.refresh_log_count % 3 == 0:
                    print(
                        f">>> [FunOne-張數] ⏳ 尚未開賣，點擊「更新頁面」刷新中... (冷卻 {round(human_delay, 2)} 秒)")

                await active_tab.evaluate("window._funone_refresh_clicked = false;")
                await asyncio.sleep(human_delay)

            elif isinstance(result, str) and result.startswith("SOCKET_REFRESH_CLICKED|"):
                target_name = result.split("|")[1]
                if not hasattr(self, 'socket_log_count'):
                    self.socket_log_count = 0
                self.socket_log_count += 1
                if self.socket_log_count % 5 == 0:
                    print(
                        f">>> [FunOne-張數] ♻️ 目標【{target_name}】已售完！極速點擊「即時更新票況」撿漏中... (冷卻 {round(human_delay, 2)} 秒)")

                await active_tab.evaluate("window._funone_socket_refresh_clicked = false;")
                await asyncio.sleep(human_delay)

            elif isinstance(result, str) and result.startswith("SOLD_OUT_NO_BTN|"):
                target_name = result.split("|")[1]
                print(
                    f">>> [FunOne-張數] ⚠️ 目標【{target_name}】已售完且無即時更新按鈕，執行網頁重整 (F5)...")
                await active_tab.reload()
                await asyncio.sleep(base_interval)

            elif result == "NO_MATCH_TICKET":
                if not hasattr(self, 'no_match_log_count'):
                    self.no_match_log_count = 0
                self.no_match_log_count += 1
                if self.no_match_log_count % 10 == 0:
                    print(f">>> [FunOne-張數] ⚠️ 畫面上找不到符合關鍵字的票種，或全數被排除！等待中...")
                await asyncio.sleep(0.5)

            elif result == "PROCESSING_INPUTS":
                print(">>> [FunOne-張數] ⚙️ 已填寫張數與同意條款，等待按鈕解鎖...")
                await asyncio.sleep(0.1)

            elif result == "WAITING_BTN_ENABLE":
                await asyncio.sleep(0.05)

            elif isinstance(result, str) and result.startswith("READY_TO_SUBMIT|"):
                parts = result.split("|")
                cx, cy = int(parts[1]), int(parts[2])

                print(f">>> [FunOne-張數] 🚀 票數與條款已就緒，發送 CDP 實體點擊結帳！")

                try:
                    import nodriver.cdp.input_ as cdp_input
                    mouse_btn = cdp_input.MouseButton.LEFT
                    await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseMoved", x=cx, y=cy))
                    await asyncio.sleep(0.05)
                    await active_tab.send(cdp_input.dispatch_mouse_event(type_="mousePressed", x=cx, y=cy, button=mouse_btn, click_count=1))
                    await asyncio.sleep(0.05)
                    await active_tab.send(cdp_input.dispatch_mouse_event(type_="mouseReleased", x=cx, y=cy, button=mouse_btn, click_count=1))
                except Exception as e:
                    print(f">>> [系統] ⚠️ CDP 點擊失敗: {e}")

                self.is_ticket_assigned = True
                await asyncio.sleep(1.0)

            elif result in ["WAITING_TRANSITION", "WAITING_DOM", "WAITING_REFRESH"]:
                await asyncio.sleep(0.05)

        except Exception as e:
            pass

# ==========================================
# [Funone搶票]
# ==========================================


async def main(args):
    print("main: 程式開始")

    # 1. 讀取設定與 Token
    config_dict = get_config_dict(args)
    if config_dict is None:
        print("Load config error! 請檢查 settings.json")
        return

    config_dict["token"] = util.get_token()

    driver = None
    tab = None

    # 2. 啟動瀏覽器 (nodriver)
    print("正在啟動瀏覽器...")
    try:
        conf = get_extension_config(config_dict)
        nodriver_overwrite_prefs(conf)
        driver = await uc.start(conf)
    except Exception as e:
        print(f"瀏覽器啟動失敗: {e}")
        import sys
        sys.exit()

    if driver is not None:
        tab = driver.main_tab

        # ==========================================
        # [核心修改] 強力版 Shadow DOM 解鎖
        # ==========================================
        print("正在注入強力版 Shadow DOM 解鎖腳本...")

        shadow_unlock_script = """
        (function() {
            'use strict';
            if (Element.prototype._originalAttachShadow) return;
            console.log("🔥 [Bot] Shadow DOM Unlocker injected!");
            Element.prototype._originalAttachShadow = Element.prototype.attachShadow;
            Element.prototype.attachShadow = function (params) {
                let newParams = params || {};
                newParams.mode = "open";
                return this._originalAttachShadow(newParams);
            };
        })();
        """
        try:
            await tab.send(cdp.page.enable())
            await tab.send(cdp.page.add_script_to_evaluate_on_new_document(source=shadow_unlock_script))
            print(">>> Shadow DOM 解鎖腳本注入成功")
        except Exception as e:
            print(f"Shadow DOM 腳本注入失敗: {e}")

        tab = await nodriver_goto_homepage(driver, tab, config_dict)
        tab = await nodrver_block_urls(tab, config_dict)

        if not config_dict["advanced"]["headless"]:
            await nodriver_resize_window(driver, config_dict)
    else:
        print("無法使用 nodriver，程式無法繼續工作")
        import sys
        sys.exit()

    # 3. 初始化變數
    url = ""
    last_url = ""
    is_quit_bot = False
    is_refresh_datetime_sent = False

    # 【刪除原本的 premature run】
    # 這裡不要直接 await ibon_bot.run()，否則會卡死在這裡進不到下面的 while True

    print(">>> [系統] 總路由迴圈啟動，監聽網址中...")

    # 4. 主迴圈 (監控網址並執行對應邏輯)
    while True:
        import time
        time.sleep(0.05)

        if driver is None:
            print("nodriver not accessible!")
            break

        if not is_quit_bot:
            url, is_quit_bot, reset_act_tab = await nodriver_current_url(driver, tab)
            if reset_act_tab is not None:
                tab = reset_act_tab

        if is_quit_bot:
            print("正在關閉機器人...")
            try:
                await driver.stop()
                driver = None
            except Exception:
                pass
            break

        if url is None or len(url) == 0:
            continue

        # 定時刷新檢查
        if not is_refresh_datetime_sent:
            is_refresh_datetime_sent = await check_refresh_datetime_occur(driver, config_dict["refresh_datetime"])

        # 暫停機制
        is_maxbot_paused = False
        import os
        if os.path.exists(CONST_MAXBOT_INT28_FILE):
            is_maxbot_paused = True
        sync_status_to_extension(not is_maxbot_paused)

        # 網址變更 Log
        if url != last_url:
            print(f"目前網址: {url}")
            write_last_url_to_file(url)
            if is_maxbot_paused:
                print("MAXBOT Paused.")
            last_url = url

        await sendkey_to_browser(driver, config_dict, url)
        await eval_to_browser(driver, config_dict, url)

        # ==========================================
        # 【核心新增】：多重網站路由分發中心 (Router)
        # 根據不同的 URL 網域，將控制權交給對應的 Bot 類別
        # ==========================================

        # --- 路由 1：富邦勇士 (UTK 系統) ---
        if 'tix.fubonbraves.com' in url:
            print(">>> [路由] 偵測到「富邦勇士」，轉交控制權給 FubonBot...")
            try:
                # 這裡假設你把之前的 IbonBot 改名為 FubonBot 了
                fubon_bot = FubonBot(driver, config_dict)
                await fubon_bot.run()  # 程式會進入 FubonBot 的無限迴圈
            except Exception as e:
                print(f">>> [錯誤] FubonBot 崩潰: {e}")
                await asyncio.sleep(2)

        # --- 路由 2：年代售票 (ERA Ticket) ---
        elif 'ticket.com.tw' in url:
            print(">>> [路由] 偵測到「年代售票」，轉交控制權給 EraBot...")
            try:
                # 之後只要建立一個名為 EraBot 的 class 就能無縫接軌
                era_bot = EraBot(driver, config_dict)
                await era_bot.run()
            except Exception as e:
                print(f">>> [錯誤] EraBot 崩潰: {e}")
                await asyncio.sleep(2)

        # --- 路由 3：遠大售票 (TicketPlus) ---
        elif 'ticketplus.com.tw' in url:
            print(">>> [路由] 偵測到「遠大售票」，轉交控制權給 TicketPlusBot...")
            try:
                ticketplus_bot = TicketPlusBot(driver, config_dict)
                await ticketplus_bot.run()
            except Exception as e:
                print(f">>> [錯誤] TicketPlusBot 崩潰: {e}")
                await asyncio.sleep(2)

        # --- 路由 4：KKTIX ---
        elif 'kktix.com' in url:
            print(">>> [路由] 偵測到「KKTIX售票」，轉交控制權給 KKTIXBot...")
            try:
                KKTIX_Bot = KKTIXBot(driver, config_dict)
                await KKTIX_Bot.run()
            except Exception as e:
                print(f">>> [錯誤] TicketPlusBot 崩潰: {e}")
                await asyncio.sleep(2)

        #  新增路由 5：寬宏售票 (Kham)

        elif 'kham.com.tw' in url:
            print(">>> [路由] 偵測到「寬宏售票」，轉交控制權給 KhamBot...")
            try:
                # 確保您剛剛寫的類別名稱是 KhamBot
                kham_bot = KhamBot(driver, config_dict)
                await kham_bot.run()
            except Exception as e:
                print(f">>> [錯誤] KhamBot 崩潰: {e}")
                await asyncio.sleep(2)

        # --- 路由：Melon Ticket ---
        elif 'melon.com' in url:
            print(">>> [路由] 偵測到「Melon Ticket」，轉交控制權給 MelonBot...")
            try:
                # 確保只實例化一次
                if not 'melon_bot' in locals():
                    melon_bot = MelonBot(driver, config_dict)
                await melon_bot.run()
            except Exception as e:
                print(f">>> [錯誤] MelonBot 崩潰: {e}")
                import asyncio
                await asyncio.sleep(2)

        # --- 路由：Billboard Live Taipei ---
        elif 'billboardlivetaipei.tw' in url:
            print(
                ">>> [路由] 偵測到「Billboard Live Taipei」，轉交控制權給 BillboardLiveBot...")
            try:
                # 確保只實例化一次
                if not 'billboard_bot' in locals():
                    # 記得要在 main 檔案的開頭或這裡 import BillboardLiveBot
                    billboard_bot = BillboardLiveBot(driver, config_dict)
                await billboard_bot.run()
            except Exception as e:
                print(f">>> [錯誤] BillboardLiveBot 崩潰: {e}")
                import asyncio
                await asyncio.sleep(2)

         # --- 路由：台鋼雄鷹 棒球 ---
        elif 'tsghawks.com' in url:
            print(">>> [路由] 偵測到「台鋼雄鷹售票網」，轉交控制權給 TsgHawksBot...")
            try:
                # 確保您剛剛寫的類別名稱是 TsgHawksBot
                tsghawks_bot = TsgHawksBot(driver, config_dict)
                await tsghawks_bot.run()
            except Exception as e:
                print(f">>> [錯誤] TsgHawksBot 崩潰: {e}")
                await asyncio.sleep(2)

        # --- 路由：NOL (公園 / Interpark Global) ---
        elif 'nol.com' in url or 'interpark.com' in url:
            print(">>> [路由] 偵測到「NOL (公園)售票」...")
            try:
                # 判斷是否啟用 Telegram 通知來決定自動化模式
                is_auto_mode = config_dict.get(
                    "advanced", {}).get("telegram_enable", False)

                if is_auto_mode:
                    print(
                        ">>> [系統] 🤖 偵測到 Telegram 通知已啟用，啟動【NolBot_AUTO (全自動極速版)】！")
                    nol_bot = NolBot_AUTO(driver, config_dict)
                else:
                    print(">>> [系統] 🎯 Telegram 通知未啟用，啟動【NolBot (半自動狙擊版)】！")
                    nol_bot = NolBot(driver, config_dict)

                await nol_bot.run()
            except Exception as e:
                print(f">>> [錯誤] NOL 機器人崩潰: {e}")
                import traceback
                traceback.print_exc()  # 印出詳細錯誤軌跡，方便後續除錯
                await asyncio.sleep(2)
        # --- 路由：富邦棒球購票 ---

        elif 'guardians.fami.life' in url:
            print(">>> [路由] 偵測到「富邦悍將售票網」，轉交控制權給 FubonBot...")
            try:
                # 確保我們呼叫的是剛剛寫好的 FubonBot 類別
                fubon_bot = FubonBot(driver, config_dict)
                await fubon_bot.run()
            except Exception as e:
                print(f">>> [錯誤] FubonBot 崩潰: {e}")
                import asyncio
                await asyncio.sleep(2)

        # --- 路由：FunOne ---
        elif 'funone.io' in url:
            print(">>> [路由] 偵測到「FunOne 售票」，轉交控制權給 FunoneBot...")
            try:
                funone_bot = FunoneBot(driver, config_dict)
                await funone_bot.run()
            except Exception as e:
                print(f">>> [錯誤] FunoneBot 崩潰: {e}")
                import traceback
                traceback.print_exc()  # 印出詳細錯誤軌跡，方便後續除錯
                await asyncio.sleep(2)
# 修改函式定義，多接收一個 tab 參數


async def nodriver_goto_homepage(driver, tab, config_dict):
    print("nodriver_goto_homepage")
    homepage = config_dict["homepage"]

    # 移除原本內部的 tab = None，改用傳進來的 tab
    # tab = None

    if 'kktix.c' in homepage:
        try:
            # [修改] 改用 tab.get，確保在同一個分頁操作
            await tab.get(homepage)
            await tab.sleep(5)  # 改用 tab.sleep (雖然 driver.sleep 也可以)
        except Exception as e:
            pass

        if len(config_dict["advanced"]["kktix_account"]) > 0:
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

    try:
        # [修改] 核心關鍵：確保使用已注入腳本的 tab 進行導航
        await tab.get(homepage)
        # await driver.sleep(5)
        await asyncio.sleep(5)  # 建議改用標準 sleep 避免混淆
    except Exception as e:
        pass

    # ... (中間處理 tixcraft cookie 的部分保持不變) ...
    # 略過中間代碼...

    # 處理 ibon cookie
    if 'ibon.com' in homepage:
        # ... (Cookie 設定保持不變) ...
        pass

        if 'https://ticket.ibon.com.tw/ActivityInfo/Details/' in homepage:
            time.sleep(3)
            try:
                # [修改] 只刷新當前 tab 即可
                await tab.reload()
            except Exception as exc:
                print(exc)
                pass

    return tab


async def nodrver_block_urls(tab, config_dict):
    print("nodrver_block_urls")

    NETWORK_BLOCKED_URLS = []

    if config_dict["advanced"]["adblock"]:
        NETWORK_BLOCKED_URLS = [
            '*.clarity.ms/*',
            '*.doubleclick.net/*',
            '*.lndata.com/*',
            '*.rollbar.com/*',
            '*.twitter.com/i/*',
            '*/adblock.js',
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
        NETWORK_BLOCKED_URLS.append('*fonts.googleapis.com/earlyaccess/*')
        NETWORK_BLOCKED_URLS.append('*/ajax/libs/font-awesome/*')
        NETWORK_BLOCKED_URLS.append('*.ico')
        NETWORK_BLOCKED_URLS.append(
            '*ticketimg2.azureedge.net/image/ActivityImage/*')
        NETWORK_BLOCKED_URLS.append('*static.tixcraft.com/images/activity/*')
        NETWORK_BLOCKED_URLS.append(
            '*static.ticketmaster.sg/images/activity/*')
        NETWORK_BLOCKED_URLS.append(
            '*static.ticketmaster.com/images/activity/*')
        NETWORK_BLOCKED_URLS.append(
            '*ticketimg2.azureedge.net/image/ActivityImage/ActivityImage_*')
        NETWORK_BLOCKED_URLS.append('*.azureedge.net/QWARE_TICKET//images/*')
        NETWORK_BLOCKED_URLS.append('*static.ticketplus.com.tw/event/*')

        # NETWORK_BLOCKED_URLS.append('https://kktix.cc/change_locale?locale=*')
        NETWORK_BLOCKED_URLS.append('https://t.kfs.io/assets/logo_*.png')
        NETWORK_BLOCKED_URLS.append('https://t.kfs.io/assets/icon-*.png')
        NETWORK_BLOCKED_URLS.append('https://t.kfs.io/upload_images/*.jpg')

    if config_dict["advanced"]["block_facebook_network"]:
        NETWORK_BLOCKED_URLS.append('*facebook.com/*')
        NETWORK_BLOCKED_URLS.append('*.fbcdn.net/*')

    # --- [修正重點開始] ---
    try:
        await tab.send(cdp.network.enable())
        # 新版 nodriver v0.48+ 不支援直接傳字串清單，這行會導致崩潰
        # 我們將其註解掉，跳過阻擋功能以確保程式能跑
        # await tab.send(cdp.network.set_blocked_ur_ls(NETWORK_BLOCKED_URLS))
        print("已跳過廣告阻擋功能 (避免版本衝突閃退)")
    except Exception as e:
        print(f"阻擋網址設定失敗 (可忽略): {e}")
    # --- [修正重點結束] ---

    return tab


async def nodriver_resize_window(driver, config_dict):
    print("nodriver_resize_window")
    window_size = config_dict["advanced"]["window_size"]
    # print("window_size", window_size)
    if len(window_size) > 0:
        if "," in window_size:
            print("start to resize window")
            launch_counter = 1
            target_left = 0
            target_top = 30
            target_width = 480
            target_height = 1024
            size_array = window_size.split(",")
            if len(size_array) >= 2:
                target_width = int(size_array[0])
                target_height = int(size_array[1])
            if len(size_array) >= 3:
                if len(size_array[2]) > 0:
                    launch_counter = int(size_array[2])
                target_left = target_width * launch_counter
                if target_left >= 1440:
                    target_left = 0
            # tab = await driver.main_tab()
            try:
                for i, tab in enumerate(driver):
                    await tab.set_window_size(left=target_left, top=target_top, width=target_width, height=target_height)
            except Exception as exc:
                # cannot unpack non-iterable NoneType object
                print(exc)
                # print("請關閉所有視窗後，重新操作一次")
                pass


async def nodriver_current_url(driver, tab):
    print("nodriver_current_url")
    exit_bot_error_strings = [
        "server rejected WebSocket connection: HTTP 500",
        "[Errno 61] Connect call failed ('127.0.0.1',",
        "[WinError 1225] ",
    ]
    # return value
    url = ""
    is_quit_bot = False
    last_active_tab = None

    driver_info = await driver._get_targets()
    if not tab.target in driver_info:
        print("tab may closed by user before, or popup confirm dialog.")
        tab = None
        await driver
        try:
            for i, each_tab in enumerate(driver):
                target_info = each_tab.target.to_json()
                target_url = ""
                if target_info:
                    if "url" in target_info:
                        target_url = target_info["url"]
                if len(target_url) > 4:
                    if target_url[:4] == "http" or target_url == "about:blank":
                        print("found tab url:", target_url)
                        last_active_tab = each_tab
        except Exception as exc:
            print(exc)
            if str(exc) == "list index out of range":
                print("Browser closed, start to exit bot.")
                is_quit_bot = True
                tab = None
                last_active_tab = None

        if not last_active_tab is None:
            tab = last_active_tab

    if tab:
        try:
            target_info = tab.target.to_json()
            if target_info:
                if "url" in target_info:
                    url = target_info["url"]
            # url = await tab.evaluate('window.location.href')
        except Exception as exc:
            print(exc)
            str_exc = ""
            try:
                str_exc = str(exc)
            except Exception as exc2:
                pass
            if len(str_exc) > 0:
                if str_exc == "server rejected WebSocket connection: HTTP 404":
                    print("目前 nodriver 還沒準備好..., 請等到沒出現這行訊息再開始使用。")

                for each_error_string in exit_bot_error_strings:
                    if each_error_string in str_exc:
                        # print('quit bot by error:', each_error_string, driver)
                        is_quit_bot = True
    return url, is_quit_bot, last_active_tab


def nodriver_overwrite_prefs(conf):
    # print(conf.user_data_dir)
    prefs_filepath = os.path.join(conf.user_data_dir, "Default")
    if not os.path.exists(prefs_filepath):
        os.mkdir(prefs_filepath)
    prefs_filepath = os.path.join(prefs_filepath, "Preferences")

    prefs_dict = {
        "credentials_enable_service": False,
        "ack_existing_ntp_extensions": False,
        "translate": {"enabled": False}}
    prefs_dict["in_product_help"] = {}
    prefs_dict["in_product_help"]["snoozed_feature"] = {}
    prefs_dict["in_product_help"]["snoozed_feature"]["IPH_LiveCaption"] = {}
    prefs_dict["in_product_help"]["snoozed_feature"]["IPH_LiveCaption"]["is_dismissed"] = True
    prefs_dict["in_product_help"]["snoozed_feature"]["IPH_LiveCaption"]["last_dismissed_by"] = 4
    prefs_dict["media_router"] = {}
    prefs_dict["media_router"]["show_cast_sessions_started_by_other_devices"] = {}
    prefs_dict["media_router"]["show_cast_sessions_started_by_other_devices"]["enabled"] = False
    prefs_dict["net"] = {}
    prefs_dict["net"]["network_prediction_options"] = 3
    prefs_dict["privacy_guide"] = {}
    prefs_dict["privacy_guide"]["viewed"] = True
    prefs_dict["privacy_sandbox"] = {}
    prefs_dict["privacy_sandbox"]["first_party_sets_enabled"] = False
    prefs_dict["profile"] = {}
    # prefs_dict["profile"]["cookie_controls_mode"]=1
    prefs_dict["profile"]["default_content_setting_values"] = {}
    prefs_dict["profile"]["default_content_setting_values"]["notifications"] = 2
    prefs_dict["profile"]["default_content_setting_values"]["sound"] = 2
    prefs_dict["profile"]["name"] = CONST_APP_VERSION
    prefs_dict["profile"]["password_manager_enabled"] = False
    prefs_dict["safebrowsing"] = {}
    prefs_dict["safebrowsing"]["enabled"] = False
    prefs_dict["safebrowsing"]["enhanced"] = False
    prefs_dict["sync"] = {}
    prefs_dict["sync"]["autofill_wallet_import_enabled_migrated"] = False

    json_str = json.dumps(prefs_dict)
    with open(prefs_filepath, 'w') as outfile:
        outfile.write(json_str)

    state_filepath = os.path.join(conf.user_data_dir, "Local State")
    state_dict = {}
    state_dict["dns_over_https"] = {}
    state_dict["dns_over_https"]["mode"] = "off"
    json_str = json.dumps(state_dict)
    with open(state_filepath, 'w') as outfile:
        outfile.write(json_str)


def get_extension_config(config_dict):
    no_sandbox = True
    browser_args = get_nodriver_browser_args()
    if len(config_dict["advanced"]["proxy_server_port"]) > 2:
        browser_args.append('--proxy-server=%s' %
                            config_dict["advanced"]["proxy_server_port"])
    conf = Config(browser_args=browser_args, no_sandbox=no_sandbox,
                  headless=config_dict["advanced"]["headless"])
    if config_dict["advanced"]["chrome_extension"]:
        ext = get_maxbot_extension_path(CONST_MAXBOT_EXTENSION_NAME)
        if len(ext) > 0:
            clone_ext = ext.replace(CONST_MAXBOT_EXTENSION_NAME, "tmp_" +
                                    CONST_MAXBOT_EXTENSION_NAME + "_" + config_dict["token"])
            if not os.path.exists(clone_ext):
                os.mkdir(clone_ext)
            util.copytree(ext, clone_ext)

            conf.add_extension(clone_ext)
            util.dump_settings_to_maxbot_plus_extension(
                clone_ext, config_dict, CONST_MAXBOT_CONFIG_FILE)
    return conf


async def check_refresh_datetime_occur(driver, target_time):
    print("check_refresh_datetime_occur")
    is_refresh_datetime_sent = False
    if len(target_time) > 0:
        system_clock_data = datetime.now()
        current_time = system_clock_data.strftime('%H:%M:%S')
        if target_time == current_time:
            try:
                for tab in driver.tabs:
                    await tab.reload()
                    is_refresh_datetime_sent = True
                    print("send refresh at time:", current_time)
            except Exception as exc:
                print(exc)
                pass

    return is_refresh_datetime_sent


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


def write_last_url_to_file(url):
    working_dir = os.path.dirname(os.path.realpath(__file__))
    target_path = os.path.join(working_dir, CONST_MAXBOT_LAST_URL_FILE)

    util.write_string_to_file(target_path, url)


async def sendkey_to_browser(driver, config_dict, url):
    print("sendkey_to_browser")
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
            # print("nodriver start to sendkey")
            for each_tab in driver.tabs:
                all_command_done = await sendkey_to_browser_exist(each_tab, sendkey_dict, url)

                # must all command success to delete tmp file.
                if all_command_done:
                    try:
                        os.unlink(tmp_filepath)
                        # print("remove file:", tmp_filepath)
                    except Exception as e:
                        pass


async def sendkey_to_browser_exist(tab, sendkey_dict, url):
    print("sendkey_to_browser_exist")
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
                        element = await tab.query_selector(cmd_dict["selector"])
                        if element:
                            await element.click()
                            await element.apply('function (element) {element.value = ""; } ')
                            await element.send_keys(target_text)
                        else:
                            # print("element not found:", select_query)
                            pass
                    except Exception as e:
                        all_command_done = False
                        # print("click fail for selector:", select_query)
                        print(e)
                        pass

                if cmd_dict["type"] == "click":
                    print("click")
                    try:
                        element = await tab.query_selector(cmd_dict["selector"])
                        if element:
                            await element.click()
                        else:
                            # print("element not found:", select_query)
                            pass
                    except Exception as e:
                        all_command_done = False
                        # print("click fail for selector:", select_query)
                        print(e)
                        pass
            time.sleep(0.05)
    return all_command_done


async def eval_to_browser(driver, config_dict, url):
    print("eval_to_browser")
    tmp_filepath = ""
    if "token" in config_dict:
        app_root = util.get_app_root()
        tmp_file = config_dict["token"] + "_eval.tmp"
        tmp_filepath = os.path.join(app_root, tmp_file)

    if os.path.exists(tmp_filepath):
        eval_dict = None
        try:
            with open(tmp_filepath) as json_data:
                eval_dict = json.load(json_data)
                print(eval_dict)
        except Exception as e:
            print("error on open file")
            print(e)
            pass

        if eval_dict:
            # print("nodriver start to eval")
            for each_tab in driver.tabs:
                all_command_done = await eval_to_browser_exist(each_tab, eval_dict, url)

                # must all command success to delete tmp file.
                if all_command_done:
                    try:
                        os.unlink(tmp_filepath)
                        # print("remove file:", tmp_filepath)
                    except Exception as e:
                        pass


def get_nodriver_browser_args():
    browser_args = [
        "--disable-animations",
        "--disable-app-info-dialog-mac",
        "--disable-background-networking",
        "--disable-backgrounding-occluded-windows",
        "--disable-breakpad",
        "--disable-component-update",
        "--disable-default-apps",
        "--disable-dev-shm-usage",
        "--disable-device-discovery-notifications",
        "--disable-dinosaur-easter-egg",
        "--disable-domain-reliability",
        "--disable-features=IsolateOrigins,site-per-process,TranslateUI",
        "--disable-infobars",
        "--disable-logging",
        "--disable-login-animations",
        "--disable-login-screen-apps",
        "--disable-notifications",
        "--disable-password-generation",
        "--disable-popup-blocking",
        "--disable-renderer-backgrounding",
        "--disable-session-crashed-bubble",
        "--disable-smooth-scrolling",
        "--disable-suggestions-ui",
        "--disable-sync",
        "--disable-translate",
        "--hide-crash-restore-bubble",
        "--homepage=about:blank",
        "--no-default-browser-check",
        "--no-first-run",
        "--no-pings",
        "--no-service-autorun",
        "--password-store=basic",
        "--remote-debugging-host=127.0.0.1",
        # "--disable-remote-fonts",
    ]

    return browser_args


async def eval_to_browser_exist(tab, eval_dict, url):
    print("eval_to_browser_exist")
    all_command_done = True
    if "command" in eval_dict:
        for cmd_dict in eval_dict["command"]:
            # print("cmd_dict", cmd_dict)
            matched_location = True
            if "location" in cmd_dict:
                if cmd_dict["location"] != url:
                    matched_location = False

            if matched_location:
                if cmd_dict["type"] == "eval":
                    print("eval")
                    target_script = cmd_dict["script"]
                    try:
                        await tab.evaluate(target_script)
                    except Exception as e:
                        all_command_done = False
                        # print("click fail for selector:", select_query)
                        print(e)
                        pass

            time.sleep(0.05)
    return all_command_done


def get_maxbot_extension_path(extension_folder):
    app_root = util.get_app_root()
    extension_path = "webdriver"
    extension_path = os.path.join(extension_path, extension_folder)
    config_filepath = os.path.join(app_root, extension_path)
    # print("config_filepath:", config_filepath)

    # double check extesion mainfest
    path = pathlib.Path(config_filepath)
    if path.exists():
        if path.is_dir():
            # print("found extension dir")
            for item in path.rglob("manifest.*"):
                path = item.parent
            # print("final path:", path)
    return config_filepath


def cli():
    parser = argparse.ArgumentParser(description="MaxBot Launcher")
    parser.add_argument("--input", type=str)
    parser.add_argument("--homepage", type=str)
    parser.add_argument("--ticket_number", type=int)
    parser.add_argument("--tixcraft_sid", type=str)
    parser.add_argument("--kktix_account", type=str)
    parser.add_argument("--kktix_password", type=str)
    parser.add_argument("--ibonqware", type=str)
    parser.add_argument("--headless", type=str)
    parser.add_argument("--browser", type=str, default='chrome')
    parser.add_argument("--window_size", type=str)
    parser.add_argument("--proxy_server", type=str)
    args = parser.parse_args()
    uc.loop().run_until_complete(main(args))


if __name__ == "__main__":
    cli()


# 日期選擇已修復 , 區域選擇待修中
