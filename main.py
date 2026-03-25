import configparser
import requests
from bs4 import BeautifulSoup
import sys
import os

# 載入漏洞測試模組
from exploits.command_injection import CommandInjectionTester
# 預留未來要載入的模組
# from exploits.sql_injection import SQLInjectionTester
# from exploits.sqli_blind import SQLiBlindTester

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
    
    token = get_csrf_token(session, login_url)
    if not token:
        print("[-] 無法取得登入頁面的 Token，程式終止。")
        sys.exit(1)

    data = {
        'username': username,
        'password': password,
        'Login': 'Login',
        'user_token': token
    }
    response = session.post(login_url, data=data, timeout=5.0)
    
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
    config = configparser.ConfigParser()
    if not os.path.exists('config.ini'):
        print("[-] 找不到 config.ini 檔案！")
        sys.exit(1)

    config.read('config.ini')

    url_linux = config['DVWA']['base_url_linux']
    url_alone_win = config['DVWA']['base_url_alone_win']
    url_ad_win = config['DVWA']['base_url_ad_win']
    username = config['DVWA']['username']
    password = config['DVWA']['password']
    security_level = config['DVWA']['default_security_level']

    # --- 第一層選單：選擇靶機 ---
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

    if os_choice == 1:
        base_url = url_linux
    elif os_choice == 2:
        base_url = url_alone_win
    elif os_choice == 3:
        base_url = url_ad_win

    # --- 第二層選單：選擇攻擊類型 ---
    print("\n" + "="*40)
    print("請選擇要執行的漏洞測試模組:")
    print("1. Command Injection")
    print("2. SQL Injection")
    print("3. SQL Injection Blind")
    print("="*40)

    try:
        attack_choice = int(input("請輸入選項 (1-3): "))
        if attack_choice not in [1, 2, 3]:
            raise ValueError
    except ValueError:
        print("[-] 輸入錯誤，請輸入 1, 2 或 3。")
        sys.exit(1)

    session = requests.Session()
    login_dvwa(session, base_url, username, password)
    set_security_level(session, base_url, security_level)

    # --- 執行對應模組 ---
    print(f"\n[*] 準備執行安全等級 [{security_level}] 的測試...")
    
    if attack_choice == 1:
        print("[*] 啟動 Command Injection 模組...")
        tester = CommandInjectionTester(session, base_url, os_choice, security_level)
        tester.run()
    elif attack_choice == 2:
        print("[*] 啟動 SQL Injection 模組...")
        # tester = SQLInjectionTester(session, base_url, security_level)
        # tester.run()
        print("[-] SQL Injection 模組尚未實作，請由架構師補齊。")
    elif attack_choice == 3:
        print("[*] 啟動 SQL Injection Blind 模組...")
        # tester = SQLiBlindTester(session, base_url, security_level)
        # tester.run()
        print("[-] SQL Injection Blind 模組尚未實作，請由架構師補齊。")

if __name__ == "__main__":
    main()
