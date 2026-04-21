import urllib.request
import json

req = urllib.request.Request('http://127.0.0.1:5000/api/auth/login', 
                             data=json.dumps({'username': 'admin', 'password': 'password123'}).encode('utf8'),
                             headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode('utf8'))
        print("Login status:", res.status)
        print("Login data:", data)
        token = data.get('token')
        
        req2 = urllib.request.Request('http://127.0.0.1:5000/api/realtime',
                                      headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(req2) as res2:
            print("Realtime status:", res2.status)
            print("Realtime data:", json.loads(res2.read().decode('utf8')))
except Exception as e:
    print("Failed:", e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf8'))
