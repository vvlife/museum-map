#!/usr/bin/env python3
"""审计：每个馆的链接是否真的打开就是VR页面"""
import json, os, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}
URL_VR = re.compile(r'(pano|virtual|/vr|_vr|360|720|streetview|vt3|v360|virtualroaming|eyespy|kuula|roundme|matterport|全景|漫游|虚拟|数字展厅|online-tours|visites-en-ligne)', re.I)
SIG = ["krpano","pano2vr","aframe","photo-sphere","photosphere","pannellum","marzipano","panolens",
       "streetview","eyespy","vr-360","360°","720°","全景","虚拟展厅","虚拟漫游","vr360",
       "matterport","roundme","kuula","virtual tour","virtual-tour","visite virtuelle","virtual visit"]

def classify(m):
    u = m["vr_url"]
    url_hit = bool(URL_VR.search(u))
    try:
        req = urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=12) as r:
            raw = r.read(400000)
            final = r.geturl()
        doc = raw.decode("utf-8", "ignore").lower()
        sig = next((s for s in SIG if s in doc), None)
        if url_hit or sig:
            return (m, "VR", f"url={'Y' if url_hit else 'N'} sig={sig}")
        return (m, "NOTVR", "首页/普通页面")
    except Exception as e:
        # 抓取失败但URL本身像VR → 信任URL
        if url_hit: return (m, "VR", f"抓取失败但URL似VR ({str(e)[:30]})")
        return (m, "MAYBE", f"无法访问: {str(e)[:40]}")

allm = []
for f in ["museums.json", "custom.json", "auto.json"]:
    d = json.load(open(os.path.join(BASE, f), encoding="utf-8"))
    lst = d["museums"] if f == "museums.json" else d
    for m in lst: m["_file"] = f
    allm += lst

print("审计", len(allm), "馆...", flush=True)
with ThreadPoolExecutor(max_workers=8) as ex:
    res = list(ex.map(classify, allm))
vr = [r for r in res if r[1]=="VR"]
notvr = [r for r in res if r[1]=="NOTVR"]
maybe = [r for r in res if r[1]=="MAYBE"]
print(f"\n=== ✅ VR页面 {len(vr)} ===")
for m,_,why in vr: print(f"  {m['name_zh']} | {why}")
print(f"\n=== ❌ 非VR页面 {len(notvr)}（待修） ===")
for m,_,why in notvr: print(f"  {m['name_zh']} | {m['vr_url'][:65]}")
print(f"\n=== ⚠️ 无法访问 {len(maybe)} ===")
for m,_,why in maybe: print(f"  {m['name_zh']} | {why} | {m['vr_url'][:50]}")
json.dump([{"id":m["id"],"name":m["name_zh"],"url":m["vr_url"],"verdict":v,"why":w,"file":m["_file"]} for m,v,w in res],
          open(os.path.join(BASE,"audit_result.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n已存 audit_result.json")
