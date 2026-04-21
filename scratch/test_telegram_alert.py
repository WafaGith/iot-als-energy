import urllib.request
import json
import time

def mock_esp_post():
    url = "http://127.0.0.1:5000/api/sensor/data"
    
    # We will simulate the energy (e) growing to be greater than 90
    # Assuming quota is 100, if e hits 92 (total), sisa is 8. This triggers boundary < 10.
    
    payload = {
        "m1": {"v": 220.1, "i": 1.2, "p": 264.12, "e": 50.0, "f": 50.0, "pf": 0.98},
        "m2": {"v": 219.5, "i": 0.5, "p": 109.75, "e": 42.0, "f": 50.0, "pf": 0.95}
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urllib.request.urlopen(req) as res:
            print("Response:", res.status, res.read().decode('utf-8'))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    print("Sending mock data where total energy = 92...")
    mock_esp_post()
