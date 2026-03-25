DVWA_AutoTester/
├── config.ini               # (A) 存放 DVWA URL, 預設帳密, Snort Log 路徑等
├── main.py                  # (B) 主程式 (提供 OS 選單、漏洞選單、執行邏輯)
├── core/
│   ├── session_manager.py   # 負責 Login、切換 Security Level、維持 Cookie
│   └── utils.py             # 負責解析 HTML 提取 Anti-CSRF Token
└── exploits/
    ├── command_injection.py # 針對 Command Injection 的測試腳本
    ├── sqli.py              # 針對 SQL Injection 的測試腳本
    └── xss.py               # 針對 XSS 的測試腳本
