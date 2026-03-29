DVWA_AutoTester/  
├── config.ini               # (A) 存放 DVWA URL, 預設帳密, Snort Log 路徑等  
├── declaimer.txt            # 免責聲明
├── main.py                  # (B) 主程式 (提供 OS 選單、漏洞選單、執行邏輯)  
└── exploits/  
    ├── command_injection.py # 針對 Command Injection 的測試腳本  
    ├── custom_lfi_linux.txt # 針對 Linux作業系統，客製化 Local File Inclsion的測試路徑
    ├── custom_lfi_linux.txt # 針對 Windows作業系統，客製化 Local File Inclsion的測試路徑:
    ├── file_upload.py       # 針對 File Upload 的測試腳本  
    ├── lfi.py               # 針對 Local File Inclusion 的測試腳本
    └── sql_injection.py     # 針對 SQL Injection 的測試腳本

