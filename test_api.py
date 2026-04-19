import urllib.request
import urllib.error
import re

try:
    urllib.request.urlopen('http://localhost:8000/api/search/supplier-transactions/?name=Lactalis%20Ingredients&query=1702.1110&intent=BUY')
except urllib.error.HTTPError as e:
    html = e.read().decode('utf-8')
    match = re.search(r'<div class="exception_value">(.*?)</div>', html, re.DOTALL)
    if match:
        print("EXCEPTION:", match.group(1).strip())
    else:
        print("COULD NOT FIND EXCEPTION IN HTML")
        m2 = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
        if m2: print("TITLE:", m2.group(1).strip())
