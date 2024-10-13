import subprocess
import time
import platform
import requests
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo # type: ignore

class ServerMonitor:
    def __init__(self):
        # Server settings
        self.SERVER_IP = "XXXXXX" #target
        self.GOOGLE_DNS = "8.8.8.8"
        self.INTERVAL = 10
        self.MAX_RETRIES = 5
        # LINE Notify settings
        self.LINE_NOTIFY_TOKEN = "XXXXXX" #token
        self.LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"

    def notify(self, message):
        headers = {"Authorization": f"Bearer {self.LINE_NOTIFY_TOKEN}"}
        payload = {"message": message}
        try:
            response = requests.post(self.LINE_NOTIFY_API, headers=headers, data=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to send LINE notification: {e}")

    def now_time(self):
        now_utc = datetime.now(ZoneInfo("UTC"))
        taipei_time = now_utc.astimezone(ZoneInfo("Asia/Taipei"))
        return taipei_time.strftime("%Y-%m-%d %H:%M:%S")

    def ping_server(self, target):
        system = platform.system()
        ping_command = ["ping", "-n", "1", target] if system == "Windows" else ["ping", "-c", "1", target]
        
        try:
            result = subprocess.run(ping_command, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
            
    def fail_check(self):
        message = f"{self.now_time()}: Host is unreachable after {self.MAX_RETRIES} attempts!!!"
        print(message)
        self.notify(message)
        
        offline_time = 0
        while not self.ping_server(self.SERVER_IP):
            offline_time += self.INTERVAL
            message = f"{self.now_time()}: Server is still OFFLINE. Total offline time: {offline_time} seconds"
            print(message)
            if offline_time % 1800 == 0:  # Notify every 30 minutes
                self.notify(message)
            time.sleep(self.INTERVAL)
        
    def monitor_server(self):
        while True:
            is_online = False
            for attempt in range(self.MAX_RETRIES):
                if self.ping_server(self.SERVER_IP):
                    is_online = True
                    break
                time.sleep(1)  # Short delay between retries

            if is_online:
                print(f"{self.now_time()}: Host is online.")
            else:
                if not self.ping_server(self.GOOGLE_DNS):
                    print(f"{self.now_time()}: VPS Internet is down.")
                    break
                self.fail_check()

                
                message = f"{self.now_time()}: Server is back ONLINE."
                print(message)
                self.notify(message)
            
            time.sleep(self.INTERVAL)

    def run(self):
        self.monitor_server()

if __name__ == "__main__":
    monitor = ServerMonitor()
    monitor.run()