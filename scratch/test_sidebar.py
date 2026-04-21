import urllib.request

try:
    with urllib.request.urlopen('http://127.0.0.1:5000/components/sidebar.html') as res:
        print("Status:", res.status)
        print("Content-Type:", res.headers.get('Content-Type'))
        content = res.read().decode('utf8')
        print("Content sample:", content[:100])
except Exception as e:
    print("Failed:", e)
