#!/usr/bin/env python3
"""为每个馆抓取 og:image 预览图"""
import json, os, re, urllib.request
from concurrent.futures import ThreadPoolExecutor
BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

def get_thumb(m):
    u = m["vr_url"]
    if m.get("status") == "needs_proxy":
        return (m["name_zh"], None, "skip-proxy")
    try:
        req = urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=12) as r:
            doc = r.read(500000).decode("utf-8", "ignore")
            final = r.geturl()
        mtag = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', doc, re.I) \
            or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', doc, re.I) \
            or re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', doc, re.I)
        if mtag:
            img = mtag.group(1)
            from urllib.parse import urljoin
            return (m["name_zh"], urljoin(final, img), "ok")
        return (m["name_zh"], None, "no-og")
    except Exception as e:
        return (m["name_zh"], None, str(e)[:30])

allm = []
for f in ["museums.json", "auto.json"]:
    d = json.load(open(os.path.join(BASE, f), encoding="utf-8"))
    allm += d["museums"] if f == "museums.json" else d
print("抓预览图", len(allm), "馆...", flush=True)
with ThreadPoolExecutor(max_workers=6) as ex:
    res = dict((name, (url, why)) for name, url, why in ex.map(get_thumb, allm))
ok = 0
for f in ["museums.json", "auto.json"]:
    p = os.path.join(BASE, f)
    d = json.load(open(p, encoding="utf-8"))
    lst = d["museums"] if f == "museums.json" else d
    for m in lst:
        url, why = res.get(m["name_zh"], (None, "?"))
        if url: m["thumb"] = url; ok += 1
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"拿到 {ok}/{len(allm)} 张预览图")
for n,(u,w) in res.items():
    if not u: print("  无图:", n, w)
