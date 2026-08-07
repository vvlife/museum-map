#!/usr/bin/env python3
"""修正 deepen 误伤 + 国博去重"""
import json, os
BASE = os.path.dirname(os.path.abspath(__file__))
REVERT = {
 "泰特现代美术馆": "https://www.tate.org.uk/visit/tate-modern",
 "维也纳艺术史博物馆": "https://www.khm.at/en",
 "橘园美术馆": "https://www.musee-orangerie.fr/en",
 "毕尔巴鄂古根海姆美术馆": "https://www.guggenheim-bilbao.eus/en",
 "莫瑞泰斯皇家美术馆": "https://www.mauritshuis.nl/en/",
 "广岛和平纪念资料馆": "https://hpmmuseum.jp/",
 "成都博物馆": "https://www.cdmuseum.com/",
 "维多利亚国家美术馆": "https://www.ngv.vic.gov.au/",
 "蒂森-博内米萨博物馆": "https://www.museothyssen.org/en",
 "中国国家博物馆": "https://m.chnmuseum.cn/portals/0/web/vr/",  # base版也换成VR列表
}
for fname in ["museums.json", "auto.json"]:
    p = os.path.join(BASE, fname)
    d = json.load(open(p, encoding="utf-8"))
    lst = d["museums"] if fname == "museums.json" else d
    out = []
    for m in lst:
        if fname == "auto.json" and m["name_zh"] == "中国国家博物馆":
            print("去重删除 auto 国博"); continue
        if m["name_zh"] in REVERT:
            if m["vr_url"] != REVERT[m["name_zh"]]:
                print("修正:", m["name_zh"], "->", REVERT[m["name_zh"]][:55])
                m["vr_url"] = REVERT[m["name_zh"]]
                m["frameable"] = None
        out.append(m)
    if fname == "museums.json": d["museums"] = out; json.dump(d, open(p,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    else: json.dump(out, open(p,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
total = 0
for f in ["museums.json","custom.json","auto.json"]:
    d = json.load(open(os.path.join(BASE,f),encoding="utf-8"))
    total += len(d["museums"] if f=="museums.json" else d)
print("总馆藏:", total)
