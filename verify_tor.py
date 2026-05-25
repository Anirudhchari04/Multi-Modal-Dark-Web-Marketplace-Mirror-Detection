import requests
import sys
import os

def check_tor_port(port):
    """Check connectivity on a specific local SOCKS port."""
    proxies = {
        'http': f"socks5h://127.0.0.1:{port}",
        'https': f"socks5h://127.0.0.1:{port}"
    }
    
    try:
        print(f"Testing port {port}...", end=" ", flush=True)
        response = requests.get(
            "https://check.torproject.org/api/ip",
            proxies=proxies,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("IsTor"):
                print("✅ Success!")
                print(f"   -> Connected via Tor! (IP: {data.get('IP')})")
                return True
            else:
                print("⚠️ Connected, but NOT via Tor (Check proxy settings).")
        else:
            print(f"❌ HTTP {response.status_code}")
            
    except Exception:
        print("❌ Connection Failed")
        
    return False

if __name__ == "__main__":
    print("--- 🧅 Tor Connectivity Check ---")
    
    # Check default system Tor
    if check_tor_port(9050):
        print("\n✅ READY! Your system is configured for port 9050.")
        sys.exit(0)
    
    # Check Tor Browser Bundle
    if check_tor_port(9150):
        print("\n✅ READY! Found Tor Browser on port 9150.")
        print("⚠️ ACTION REQUIRED: Update config.py to use TOR_PROXY_PORT = 9150")
        sys.exit(0)
        
    print("\n❌ NO TOR CONNECTION DETECTED.")
    print("1. Ensure Tor Browser or Tor Service is running.")
    print("2. If using Tor Browser, it typically uses port 9150.")
    print("3. If using system Tor ('brew install tor'), it uses port 9050.")
