#!/usr/bin/env python3
"""人工策展：清洗 auto.json 垃圾链接 + 去重 + 补齐缺失馆"""
import json, os, time
BASE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(BASE, "auto.json")
auto = json.load(open(p, encoding="utf-8"))

# 名称 -> 修正后的官方链接
FIX = {
 "芝加哥艺术博物馆": "https://www.artic.edu/visit",
 "盖蒂中心": "https://www.getty.edu/visit/",
 "维也纳艺术史博物馆": "https://www.khm.at/en/",
 "橘园美术馆": "https://www.musee-orangerie.fr/en",
 "毕尔巴鄂古根海姆美术馆": "https://www.guggenheim-bilbao.eus/en",
 "罗丹美术馆": "https://www.musee-rodin.fr/en",
 "莫瑞泰斯皇家美术馆": "https://www.mauritshuis.nl/en/",
 "卢浮宫阿布扎比": "https://www.louvreabudhabi.ae/",
 "安大略皇家博物馆": "https://www.rom.on.ca/en",
 "伦敦科学博物馆": "https://www.sciencemuseum.org.uk/",
 "德意志博物馆": "https://www.deutsches-museum.de/en",
 "中国科学技术馆": "https://www.cstm.org.cn/",
 "陕西历史博物馆": "https://www.sxhm.com/",
 "广岛和平纪念资料馆": "https://hpmmuseum.jp/",
 "成都博物馆": "https://www.cdmuseum.com/",
 "浙江省博物馆": "https://www.zhejiangmuseum.com/",
 "美国国家历史博物馆": "https://americanhistory.si.edu/",
}
DELETE = {"卢浮宫阿布扎比分馆"}  # 重复且指向礼品店
ADD = [
 ("菲尔德自然史博物馆","Field Museum","https://www.fieldmuseum.org/",41.8663,-87.6170,"nature","芝加哥"),
 ("维多利亚国家美术馆","National Gallery of Victoria","https://www.ngv.vic.gov.au/",-37.8226,144.9689,"art","墨尔本"),
 ("蒂森-博内米萨博物馆","Thyssen-Bornemisza Museum","https://www.museothyssen.org/en",40.4161,-3.6950,"art","马德里"),
 ("帝国战争博物馆","Imperial War Museum","https://www.iwm.org.uk/",51.4958,-0.1087,"history","伦敦"),
]

out, seen = [], set()
for m in auto:
    n = m["name_zh"]
    if n in DELETE or n in seen:
        print("删除:", n, m["vr_url"][:50]); continue
    seen.add(n)
    if n in FIX:
        print("修正:", n, m["vr_url"][:45], "->", FIX[n])
        m["vr_url"] = FIX[n]
        m["notes"] = "人工复核官方入口"
        m["status"] = "verified"; m["needs_review"] = False
        m["type"] = "🏛 官方网站"
    out.append(m)

have = {m["name_zh"] for m in out}
base = json.load(open(os.path.join(BASE,"museums.json"),encoding="utf-8"))["museums"]
have |= {m["name_zh"] for m in base}
for zh,en,url,lat,lon,cat,city in ADD:
    if zh in have: continue
    out.append({"id":"curated-"+str(int(time.time()*1000)+len(out)),"name_zh":zh,"name_en":en,
        "city":city,"country":"","lat":lat,"lon":lon,"vr_url":url,"type":"🏛 官方网站",
        "status":"verified","category":cat,"notes":"人工补录官方入口","needs_review":False})
    print("补录:", zh)
json.dump(out, open(p,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("auto.json 最终:", len(out), "馆")
