#!/usr/bin/env python3
import json, os
BASE = os.path.dirname(os.path.abspath(__file__))
G = "https://artsandculture.google.com/partner/"
FIX = {
 # 回滚误修 + 定案
 "广岛和平纪念资料馆": ("https://hpmmuseum.jp/", None, None),
 "成都博物馆": ("https://www.cdmuseum.com/", None, None),
 "香港故宫文化博物馆": ("https://www.hkpm.org.hk/sc", None, None),
 "荷兰国立博物馆": (G+"rijksmuseum", "needs_proxy", "🌐 街景漫游（需代理）"),
 # 敦煌直达洞窟全景
 "敦煌莫高窟": ("https://www.e-dunhuang.com/cave/10.0001/0001.0001.0061", None, "🥽 VR 全景"),
 # 欧美馆 GAC 街景直达
 "盖蒂中心": (G+"the-j-paul-getty-museum", "needs_proxy", "🌐 街景漫游（需代理）"),
 "维也纳艺术史博物馆": (G+"kunsthistorisches-museum-vienna", "needs_proxy", "🌐 街景漫游（需代理）"),
 "橘园美术馆": (G+"musee-de-lorangerie", "needs_proxy", "🌐 街景漫游（需代理）"),
 "罗丹美术馆": (G+"musee-rodin", "needs_proxy", "🌐 街景漫游（需代理）"),
 "莫瑞泰斯皇家美术馆": (G+"mauritshuis", "needs_proxy", "🌐 街景漫游（需代理）"),
 "维多利亚国家美术馆": (G+"national-gallery-of-victoria", "needs_proxy", "🌐 街景漫游（需代理）"),
 "泰特现代美术馆": (G+"tate-modern", "needs_proxy", "🌐 街景漫游（需代理）"),
 "美国国家美术馆": (G+"national-gallery-of-art", "needs_proxy", "🌐 街景漫游（需代理）"),
 "安大略皇家博物馆": (G+"royal-ontario-museum", "needs_proxy", "🌐 街景漫游（需代理）"),
 "伦敦科学博物馆": (G+"science-museum", "needs_proxy", "🌐 街景漫游（需代理）"),
 "美国国家历史博物馆": (G+"national-museum-of-american-history", "needs_proxy", "🌐 街景漫游（需代理）"),
 "卢浮宫阿布扎比": (G+"louvre-abu-dhabi", "needs_proxy", "🌐 街景漫游（需代理）"),
 "帝国战争博物馆": (G+"imperial-war-museums", "needs_proxy", "🌐 街景漫游（需代理）"),
 "佩加蒙博物馆": (G+"pergamonmuseum", "needs_proxy", "🌐 街景漫游（需代理）"),
}
n=0
for f in ["museums.json","custom.json","auto.json"]:
    p = os.path.join(BASE,f)
    d = json.load(open(p,encoding="utf-8"))
    lst = d["museums"] if f=="museums.json" else d
    for m in lst:
        if m["name_zh"] in FIX:
            url, st, tp = FIX[m["name_zh"]]
            if m["vr_url"] != url:
                print("修:", m["name_zh"], "->", url[:65])
            m["vr_url"] = url
            m["frameable"] = None
            if st: m["status"] = st
            if tp: m["type"] = tp
            n+=1
    json.dump(d, open(p,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("定案", n, "条")
