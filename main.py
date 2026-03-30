import configparser
import requests
from bs4 import BeautifulSoup
import sys
import os

# 載入漏洞測試模組
from exploits.command_injection import CommandInjectionTester
# 預留未來要載入的模組
from exploits.sql_injection import SQLInjectionTester
# from exploits.sqli_blind import SQLiBlindTester
from exploits.file_upload import FileUploadTester
from exploits.lfi import LFITester

def show_disclaimer_and_agree():
    """讀取免責聲明並要求使用者同意"""
    disclaimer_file = 'disclaimer.txt'
    
    # 防錯機制：檢查聲明檔是否存在
    if not os.path.exists(disclaimer_file):
        print(f"[-] 找不到免責聲明檔案 ({disclaimer_file})！")
        print("[-] 為確保安全與合規，程式終止。請確保 disclaimer.txt 存在於同一目錄下。")
        sys.exit(1)
        
    # 讀取並印出免責聲明
    with open(disclaimer_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    print("="*60)
    print(content)
    print("="*60)
    
    # 強制要求同意
    choice = input("\n[?] 您是否已詳細閱讀並同意上述免責聲明與使用條款？(輸入 Y 同意，其他按鍵退出): ").strip().upper()
    if choice != 'Y':
        print("[-] 您未同意免責聲明，程式已安全終止。")
        sys.exit(0)
        
    print("[+] 感謝您的配合，程式即將啟動...\n")



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
    # 1. 最優先執行：檢查並要求同意免責聲明
    #show_disclaimer_and_agree()

    # 2. 讀取設定檔
    config = configparser.ConfigParser()
    if not os.path.exists('config.ini'):
        print("[-] 找不到 config.ini 檔案！")
        sys.exit(1)
    # 加上 utf-8 編碼處理，避免中文與 Emoji 造成讀取報錯
    config.read('config.ini', encoding='utf-8')

    url_linux = config['DVWA']['base_url_linux']
    url_alone_win = config['DVWA']['base_url_alone_win']
    url_ad_win = config['DVWA']['base_url_ad_win']
    username = config['DVWA']['username']
    password = config['DVWA']['password']
    security_level = config['DVWA']['default_security_level']
    # 防錯機制：嘗試讀取 User-Agent，若未設定則保留為空
    try:
        user_agent = config['Browser user-agent']['user_agent']
    except KeyError:
        user_agent = None
        print("[!] 警告: config.ini 缺少 user_agent 設定，將使用 requests 預設值。")

    # --- 讀取 OOB Listener 設定 ---
    try:
        attacker_ip = config['OOB_Listener']['attacker_ip']
        attacker_port = int(config['OOB_Listener']['attacker_port'])
        listen_timeout = int(config['OOB_Listener']['listen_timeout'])
    except KeyError:
        print("[!] 警告: config.ini 缺少 OOB_Listener 設定，將使用預設值。")
        attacker_ip = "127.0.0.1"
        attacker_port = 8080
        listen_timeout = 10


    # --- 讀取自訂字典檔設定 ---
    try:
        # 變數與 Key 都統一使用乾淨的全小寫
        lfi_linux_list = config['Custom_Wordlists']['lfi_linux']
        lfi_windows_list = config['Custom_Wordlists']['lfi_windows']
        cmd_injection_list = config['Custom_Wordlists']['cmd_injection']
    except KeyError:
        print("[!] 警告: config.ini 缺少 Custom_Wordlists 設定，將使用預設檔名。")
        lfi_linux_list = "custom_lfi_linux.txt"
        lfi_windows_list = "custom_lfi_windows.txt"
        cmd_injection_list = "./exploits/custom_cmd_injection.txt"
    # --- 第一層選單：選擇靶機 ---
    print("="*40)
    print("   DVWA 自動化滲透與 IDS 規則驗證工具")
    print("="*40)
    print("請選擇要測試的目標靶機:")
    print(f" [1] Ubuntu 20.04 (Linux)   [{url_linux}]")
    print(f" [2] Standalone Windows     [{url_alone_win}]")
    print(f" [3] Windows in AD          [{url_ad_win}]")
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
    print(" [1] Command Injection")
    print(" [2] SQL Injection")
    print(" [3] SQL Injection Blind")
    print(" [4] File Upload")
    print(" [5] Local File Inclusion")
    print("="*40)

    try:
        attack_choice = int(input("請輸入選項 (1-5): "))
        if attack_choice not in [1, 2, 3, 4, 5]:
            raise ValueError
    except ValueError:
        print("[-] 輸入錯誤，請輸入 1 到 5 之間的數字。")
        sys.exit(1)

    # 初始化 Session 並套用全域 User-Agent

    session = requests.Session()
    if user_agent:
        session.headers.update({'User-Agent': user_agent})
        print(f"\n[*] 已載入自訂 User-Agent: {user_agent}")

    login_dvwa(session, base_url, username, password)
    set_security_level(session, base_url, security_level)

    # --- 執行對應模組 ---
    print(f"\n[*] 準備執行安全等級 [{security_level}] 的測試...")
    
    if attack_choice == 1:
        print("[*] 啟動 Command Injection 模組...")
        # 將 OOB 所需參數一併傳入
        tester = CommandInjectionTester(session, base_url, os_choice, security_level, attacker_ip, attacker_port, listen_timeout, custom_payload_file=cmd_injection_list)
        tester.run()
    elif attack_choice == 2:
        print("[*] 啟動 SQL Injection 模組...")
        tester = SQLInjectionTester(session, base_url, security_level)
        tester.run()
        #print("[-] SQL Injection 模組尚未實作。")
    elif attack_choice == 3:
        print("[*] 啟動 SQL Injection Blind 模組...")
        # tester = SQLiBlindTester(session, base_url, security_level)
        # tester.run()
        print("[-] SQL Injection Blind 模組尚未實作。")
    elif attack_choice == 4:
        print("[*] 啟動 File Upload 模組...")
        tester = FileUploadTester(session, base_url, security_level)
        tester.run()
    elif attack_choice == 5:
        print("[*] 啟動 Local File Inclusion 模組...")
        tester = LFITester(session, base_url, os_choice, security_level, lfi_linux_list, lfi_windows_list)
        tester.run()


if __name__ == "__main__":
    main()
