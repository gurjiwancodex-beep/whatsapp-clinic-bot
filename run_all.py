import os
import sys
import time
import re
import subprocess
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED_PATH = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"
PYTHON_PATH = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")

def main():
    print("\n" + "="*70)
    print("🏥 Starting WhatsApp Clinic Bot & Live Mobile Tunnel...")
    print("="*70)

    # 1. Start Uvicorn Server in background
    print("\n[1/3] Starting FastAPI server on port 8000...")
    server_cmd = [PYTHON_PATH, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    server_proc = subprocess.Popen(
        server_cmd,
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)

    # 2. Start Cloudflare Tunnel
    print("[2/3] Connecting Cloudflare secure tunnel...")
    tunnel_cmd = [CLOUDFLARED_PATH, "tunnel", "--url", "http://localhost:8000"]
    tunnel_proc = subprocess.Popen(
        tunnel_cmd,
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    tunnel_url = None
    print("[3/3] Generating your mobile public link...")
    start_time = time.time()
    while time.time() - start_time < 20:
        line = tunnel_proc.stderr.readline()
        if "trycloudflare.com" in line:
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                tunnel_url = match.group(0)
                break
        time.sleep(0.1)

    if not tunnel_url:
        print("\n❌ Could not get Cloudflare URL. Please make sure internet is working.")
        server_proc.terminate()
        tunnel_proc.terminate()
        sys.exit(1)

    admin_url = f"{tunnel_url}/admin"
    appts_url = f"{tunnel_url}/appointments"
    webhook_url = f"{tunnel_url}/webhook"

    # Save to a convenient text file
    links_file = os.path.join(BASE_DIR, "MY_MOBILE_LINKS.txt")
    with open(links_file, "w", encoding="utf-8") as f:
        f.write(f"ADMIN PANEL (Control Clinic): {admin_url}\n")
        f.write(f"APPOINTMENTS DASHBOARD:       {appts_url}\n")
        f.write(f"META WEBHOOK URL:             {webhook_url}\n")
        f.write("VERIFY TOKEN:                 clinic_bot_secret_verify_token_123\n")

    print("\n" + "="*70)
    print("🎉 SUCCESS! YOUR BOT & ADMIN ARE LIVE ONLINE!")
    print("="*70)
    print(f"\n📱 1. OPEN ON YOUR MOBILE PHONE (Admin Control Panel):")
    print(f"   👉  {admin_url}")
    print(f"\n📋 2. VIEW LIVE APPOINTMENTS ON MOBILE:")
    print(f"   👉  {appts_url}")
    print(f"\n🌐 3. META WHATSAPP WEBHOOK URL:")
    print(f"   👉  {webhook_url}")
    print(f"   👉  Verify Token: clinic_bot_secret_verify_token_123")
    print("\n" + "-"*70)
    print("💡 Note: These links have also been saved to:")
    print(f"   {links_file}")
    print("="*70)
    print("\n⚠️  DO NOT CLOSE THIS WINDOW!")
    print("   (ਇਸ ਸਕ੍ਰੀਨ ਨੂੰ ਬੰਦ ਨਹੀਂ ਕਰਨਾ, ਮਿਨੀਮਾਈਜ਼ ਕਰ ਦਿਓ ਤਾਂ ਜੋ ਬੋਟ ਚੱਲਦਾ ਰਹੇ)")
    print("   Press Ctrl+C to stop the bot anytime.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping bot and tunnel...")
        server_proc.terminate()
        tunnel_proc.terminate()
        print("Shutdown complete. Have a nice day!")

if __name__ == "__main__":
    main()
