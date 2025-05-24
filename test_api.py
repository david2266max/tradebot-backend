import requests

BASE_URL = "http://localhost:8000"

def test_status():
    r = requests.get(f"{BASE_URL}/status")
    assert r.status_code == 200
    print("✅ /status funcionando")

def test_operacoes():
    r = requests.get(f"{BASE_URL}/operacoes")
    assert r.status_code == 200
    print("✅ /operacoes funcionando")

def test_start_stop_bot():
    r = requests.post(f"{BASE_URL}/bot/start")
    assert r.status_code == 200
    print("✅ /bot/start funcionando")

    r = requests.post(f"{BASE_URL}/bot/stop")
    assert r.status_code == 200
    print("✅ /bot/stop funcionando")

if __name__ == "__main__":
    test_status()
    test_operacoes()
    test_start_stop_bot()