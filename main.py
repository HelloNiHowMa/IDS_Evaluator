import configparser
import requests
from bs4 import BeautifulSoup
import sys
import os

# 載入我們稍早寫好的漏洞測試模組
from exploits.command_injection import CommandInjectionTester

def get_csrf_token(session, url):
    """通用的防錯機制：從指定 URL 取得 anti-CSRF token"""
    try:
        response = session.get(url, timeout=5.0)
        soup = BeautifulSoup(response.text, 'html.parser')
        token_input = soup.find('input', {'name': 'user_token'})
        return token_input.get('value') if token_input else None
    except Exception as e:
        print(f"[!] 獲取 Token 失敗 ({url}): {e}")
        return None

def login_dvwa(session, base_url, username, password):
    """處理 DVWA 登入流程"""
    print("[*] 正在嘗試登入 DVWA...")
    login_url = f"{base_url}/login.php"
    
    # 1. 先 GET 登入頁面以獲取 user_token
    token = get_csrf_token(session, login_url)
    if not token:
        print("[-] 無法取得登入頁面的 Token，程式終止。")
        sys.exit(1)

    # 2. 夾帶 Token 發送 POST 登入請求
    data = {
        'username': username,
        'password': password,
        'Login': 'Login',
        'user_token': token
    }
    response = session.post(login_url, data=data, timeout=5.0)
    
    # 3. 驗證是否登入成功 (檢查網頁內容是否還有登入表單)
    if "Welcome to Damn Vulnerable Web Application" in response.text or "login.php" not in response.url:
        print("[+] 登入成功！")
        return True
    else:
        print("[-] 登入失敗，請檢查 config.ini 中的帳密。")
        sys.exit(1)

def set_security_level(session, base_url, level):
    """設定 DVWA 的安全等級"""
    print(f"[*] 正在設定安全等級為: {level}")
    security_url = f"{base_url}/security.php"
    
    token = get_csrf_token(session, security_url)
    if not token:
        print("[-] 無法取得安全設定頁面的 Token。")
        sys.exit(1)

    data = {
        'security': level,
        'seclev_submit': 'Submit',
        'user_token': token
    }
    session.post(security_url, data=data, timeout=5.0)
    print(f"[+] 安全等級已設為 {level}。")

def main():
    # --- 步驟 A：讀取 config.ini ---
    config = configparser.ConfigParser()
    if not os.path.exists('config.ini'):
        print("[-] 找不到 config.ini 檔案！")
        sys.exit(1)

    config.read('config.ini')

    # 注意防錯：configparser 預設會將 key 轉為小寫
    url_linux = config['DVWA']['base_url_linux']
    url_alone_win = config['DVWA']['base_url_alone_win']
    url_ad_win = config['DVWA']['base_url_ad_win']

    username = config['DVWA']['username']
    password = config['DVWA']['password']
    security_level = config['DVWA']['default_security_level']

    # --- 步驟 B：顯示主選單 ---
    print("="*40)
    print("   DVWA 自動化滲透與 IDS 規則驗證工具")
    print("="*40)
    print("請選擇要測試的目標靶機:")
    print(f"1. Ubuntu 20.04 (Linux)   [{url_linux}]")
    print(f"2. Standalone Windows     [{url_alone_win}]")
    print(f"3. Windows in AD          [{url_ad_win}]")
    print("="*40)

    try:
        os_choice = int(input("請輸入選項 (1-3): "))
        if os_choice not in [1, 2, 3]:
            raise ValueError
    except ValueError:
        print("[-] 輸入錯誤，請輸入 1, 2 或 3。")
        sys.exit(1)

    # --- 步驟 C：根據選擇動態指派 base_url ---
    if os_choice == 1:
        base_url = url_linux
        print("\n[*] 已鎖定目標: Ubuntu 20.04 (Linux)")
    elif os_choice == 2:
        base_url = url_alone_win
        print("\n[*] 已鎖定目標: Standalone Windows")
    elif os_choice == 3:
        base_url = url_ad_win
        print("\n[*] 已鎖定目標: Windows in AD")

    # --- 步驟 D：初始化 Session 並登入 ---
    # 使用動態決定的 base_url 進行後續所有操作
    session = requests.Session()

    # login_dvwa 和 set_security_level 函式不需要改，直接傳入選定的 base_url
    login_dvwa(session, base_url, username, password)
    set_security_level(session, base_url, security_level)

    # --- 步驟 E：執行漏洞測試 ---
    print("\n[*] 啟動 Command Injection 模組...")
    # 將選定的 base_url 與 os_choice 傳入測試模組
    tester = CommandInjectionTester(session, base_url, os_choice, security_level)
    tester.run()

if __name__ == "__main__":
    main()
