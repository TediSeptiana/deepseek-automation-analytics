"""Script Klien untuk Pengujian Endpoint DeepSeek FastAPI."""

import time
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

def wait_for_service_ready(timeout_sec: int = 60) -> bool:
    """Memeriksa status health check hingga browser siap."""
    print("[INFO] Mengecek readiness status server...")
    start_time = time.time()
    
    while time.time() - start_time < timeout_sec:
        try:
            res = requests.get(f"{BASE_URL}/health", timeout=5)
            if res.status_code == 200:
                data = res.json()
                status = data.get("service_status")
                print(f"[STATUS] Engine Browser: {status}")
                
                if status == "ready":
                    return True
                if status == "human_intervention_required":
                    print("[WARN] Selesaikan CAPTCHA di browser yang terbuka!")
        except requests.RequestException:
            print("[WAIT] Menunggu FastAPI server berjalan...")
            
        time.sleep(3)
        
    return False


def main() -> None:
    if not wait_for_service_ready():
        print("[ERROR] Server/Browser tidak siap dalam batas waktu.")
        return

    payload = {"prompt": """buatkan saya function segitiga python sederhana 1 saja

"""}
    
    print("\n[INFO] Mengirim request ke /api/v1/chat...")
    response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=60)

    if response.status_code == 200:
        data = response.json()
        print("\n" + "=" * 50)
        print("Status   :", data.get("status"))
        print("Session  :", data.get("session_id"))
        print("Response :\n", data.get("response"))
        print("=" * 50)
    else:
        print(f"[ERROR] HTTP {response.status_code}: {response.text}")


if __name__ == "__main__":
    main()