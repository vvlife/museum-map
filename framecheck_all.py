#!/usr/bin/env python3
"""批量检测所有馆的可嵌入性，结果写入各数据文件 frameable 字段"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server

BASE = os.path.dirname(os.path.abspath(__file__))

def check(m):
    r = server.frame_check(m["vr_url"])
    return m["vr_url"], r.get("frameable")  # True / False / None

files = ["museums.json", "custom.json", "auto.json"]
allm = []
data = {}
for f in files:
    p = os.path.join(BASE, f)
    d = json.load(open(p, encoding="utf-8"))
    lst = d["museums"] if f == "museums.json" else d
    data[f] = (p, d, lst)
    allm += lst

print("检测", len(allm), "馆...")
with ThreadPoolExecutor(max_workers=6) as ex:
    results = dict(ex.map(check, allm))
for f, (p, d, lst) in data.items():
    n = 0
    for m in lst:
        fb = results.get(m["vr_url"])
        if fb is not None:
            m["frameable"] = fb; n += 1
        else:
            m["frameable"] = None
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f, "->", n, "条已标记")
yes = sum(1 for v in results.values() if v is True)
no = sum(1 for v in results.values() if v is False)
unk = sum(1 for v in results.values() if v is None)
print(f"可内嵌 {yes} / 防嵌入 {no} / 未知 {unk}")
