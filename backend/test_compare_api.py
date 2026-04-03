import urllib.request
import urllib.error

url = "http://localhost:8000/api/search/compare/?suppliers=Seawall%20Enterprise%20Ltd&query=sell%20dextrose&scope=worldwide&intent=SELL"

try:
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req) as response:
        print("Success:", response.read().decode())
except urllib.error.HTTPError as e:
    body = e.read().decode()
    if 'traceback_area' in body:
        start = body.find('<textarea id="traceback_area"')
        if start != -1:
            end = body.find('</textarea>', start)
            print("Traceback:\n", body[start:end])
    else:
        # Just rip out all pre tags and search for traceback
        import re
        pres = re.findall(r'<pre[^>]*>(.*?)</pre>', body, re.DOTALL)
        for pre in pres:
            if 'Traceback' in pre or 'File "' in pre or 'Invalid filter' in pre:
                print("PRE TAG CONTENT:\n", pre)
except Exception as e:
    print("Request failed:", e)
