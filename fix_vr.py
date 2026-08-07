#!/usr/bin/env python3
"""修复非VR链接：CN馆嗅探站内VR；欧美馆换GAC partner页（必应验证）"""
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server

BASE = os.path.dirname(os.path.abspath(__file__))
VR_URL = re.compile(r'(pano|/vr|_vr|360|720|streetview|v360|virtualroaming|eyespy|virtual|tour|全景|漫游|虚拟|数字|vr)', re.I)

# 国内/可达站点：嗅探
SNIFF = {
 "敦煌莫高窟": "https://www.e-dunhuang.com/",
 "南京博物院": "https://www.njmuseum.com/",
 "湖南博物院": "https://de.hnmuseum.com/collection/",
 "苏州博物馆": "https://www.szmuseum.com/",
 "香港故宫文化博物馆": "https://www.hkpm.org.hk/sc",
 "陕西历史博物馆": "https://www.sxhm.com/",
 "秦始皇帝陵博物院": "https://bmy.com.cn/",
 "广岛和平纪念资料馆": "https://hpmmuseum.jp/",
 "成都博物馆": "https://www.cdmuseum.com/",
 "上海博物馆": "https://www.shanghaimuseum.net/",
 "荷兰国立博物馆": "https://www.rijksmuseum.nl/en",
}
# 欧美馆：找GAC partner页
GAC = {
 "盖蒂中心": "Getty Museum",
 "维也纳艺术史博物馆": "Kunsthistorisches Museum Vienna",
 "橘园美术馆": "Musee de l'Orangerie",
 "罗丹美术馆": "Musee Rodin",
 "莫瑞泰斯皇家美术馆": "Mauritshuis",
 "维多利亚国家美术馆": "National Gallery of Victoria",
 "泰特现代美术馆": "Tate Modern",
 "美国国家美术馆": "National Gallery of Art Washington",
 "安大略皇家博物馆": "Royal Ontario Museum",
 "伦敦科学博物馆": "Science Museum London",
 "美国国家历史博物馆": "National Museum of American History",
 "卢浮宫阿布扎比": "Louvre Abu Dhabi",
 "帝国战争博物馆": "Imperial War Museums",
 "佩加蒙博物馆": "Pergamonmuseum",
}

def sniff(name, home):
    try:
        cands = server.scan_site_vr(home)
    except Exception:
        cands = []
    for c in cands:
        if VR_URL.search(c["url"]) and ("google" not in c["url"]):
            return c["url"], "sniff"
    # 必应补充
    try:
        for r in server.bing_search(name + " 全景 虚拟展厅"):
            if r["host"] and not any(j in r["host"] for j in server.JUNK_HOSTS) and VR_URL.search(r["url"]):
                return r["url"], "bing:" + r["host"]
    except Exception:
        pass
    return None, None

def find_gac(en):
    try:
        for r in server.bing_search(en + " artsandculture.google.com partner"):
            m = re.search(r'https://artsandculture\.google\.com/partner/[\w\-%.]+', r["url"])
            if m: return m.group(0)
        # 第二次尝试
        for r in server.bing_search(en + " google arts culture virtual tour"):
            m = re.search(r'https://artsandculture\.google\.com/partner/[\w\-%.]+', r["url"])
            if m: return m.group(0)
    except Exception:
        pass
    return None

fixes = {}
print("== 国内馆嗅探 ==", flush=True)
for name, home in SNIFF.items():
    url, how = sniff(name, home)
    print(("✅" if url else "❌", name, "->", (url or "未找到")[:70], how or ""), flush=True)
    if url: fixes[name] = (url, None)
    time.sleep(0.8)
print("== 欧美馆GAC ==", flush=True)
for name, en in GAC.items():
    url = find_gac(en)
    print(("✅" if url else "❌", name, "->", (url or "未找到")[:75]), flush=True)
    if url: fixes[name] = (url, "needs_proxy")
    time.sleep(0.8)

# 应用修复
n = 0
for f in ["museums.json", "custom.json", "auto.json"]:
    p = os.path.join(BASE, f)
    d = json.load(open(p, encoding="utf-8"))
    lst = d["museums"] if f == "museums.json" else d
    for m in lst:
        if m["name_zh"] in fixes:
            url, st = fixes[m["name_zh"]]
            m["vr_url"] = url
            m["frameable"] = None
            if st: m["status"] = st
            m["type"] = "🥽 VR 全景" if not st else "🌐 街景漫游（需代理）"
            n += 1
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("已修复", n, "条")
json.dump(fixes, open(os.path.join(BASE,"fix_vr_result.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
