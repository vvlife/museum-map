#!/usr/bin/env python3
"""补收录：上轮未找到的17馆，中英双语查询"""
import json, os, time, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server

BASE = os.path.dirname(os.path.abspath(__file__))
MIS = [
 ("陕西历史博物馆","Shaanxi History Museum",34.2226,108.9533,"history"),
 ("湖南博物院","Hunan Museum",28.2157,112.9869,"general"),
 ("苏州博物馆","Suzhou Museum",31.3245,120.6289,"art"),
 ("香港故宫文化博物馆","Hong Kong Palace Museum",22.3040,114.1596,"general"),
 ("中国国家博物馆","National Museum of China",39.9051,116.4015,"general"),
 ("美国国家历史博物馆","Smithsonian National Museum of American History",38.8913,-77.0300,"history"),
 ("菲尔德自然史博物馆","Field Museum Chicago",41.8663,-87.6170,"nature"),
 ("卢浮宫阿布扎比","Louvre Abu Dhabi",24.5336,54.3989,"art"),
 ("新加坡国家博物馆","National Museum of Singapore",1.2966,103.8485,"general"),
 ("维多利亚国家美术馆","National Gallery of Victoria",-37.8226,144.9689,"art"),
 ("安大略皇家博物馆","Royal Ontario Museum",43.6677,-79.3948,"general"),
 ("蒂森-博内米萨博物馆","Thyssen-Bornemisza Museum",40.4161,-3.6950,"art"),
 ("古根海姆毕尔巴鄂","Guggenheim Museum Bilbao",43.2687,-2.9340,"art"),
 ("橘园美术馆","Musee de l'Orangerie virtual tour",48.8638,2.3222,"art"),
 ("罗丹美术馆","Musee Rodin Paris",48.8556,2.3158,"art"),
 ("帝国战争博物馆","Imperial War Museum London",51.4958,-0.1087,"history"),
 ("广岛和平纪念资料馆","Hiroshima Peace Memorial Museum",34.3928,132.4522,"history"),
]

def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)

def find(zh, en):
    seen, pool = set(), []
    for q in [en+" virtual tour", en+" 360 online", zh+" 虚拟展厅", zh+" 全景"]:
        try:
            for r in server.bing_search(q):
                key = r["url"].rstrip("/").split("#")[0]
                if key in seen: continue
                seen.add(key)
                r["score"] = max(server.relevance(zh, r), server.relevance(en, r))
                r["is_vr"] = any(k in (r["title"]+" "+r["url"]+" "+r["snippet"]).lower() for k in server.VR_KEYS)
                pool.append(r)
        except Exception as e:
            log("  query err:", str(e)[:50])
        time.sleep(0.5)
    good = [r for r in pool if r["score"] > 0 and not any(j in r["host"] for j in server.JUNK_HOSTS)]
    good.sort(key=lambda r: (not r["is_vr"], -r["score"]))
    return good[:1]

def main():
    p = os.path.join(BASE, "auto.json")
    auto = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []
    have = {m["name_zh"] for m in auto}
    added, miss = 0, []
    for zh, en, lat, lon, cat in MIS:
        if zh in have: continue
        cands = find(zh, en)
        if cands:
            c = cands[0]
            auto.append({"id": "auto-" + str(int(time.time()*1000)), "name_zh": zh, "name_en": en,
                "city": "", "country": "", "lat": lat, "lon": lon, "vr_url": c["url"],
                "type": "🌐 补收录", "status": "auto", "category": cat,
                "notes": c["title"][:60], "needs_review": True})
            added += 1
            log(f"✅ {zh} -> {c['host']} | {c['url'][:70]}")
            json.dump(auto, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        else:
            miss.append(zh)
            log(f"❌ 未找到: {zh}")
        time.sleep(1.2)
    log(f"完成: 新增 {added}, 未找到 {len(miss)} -> {miss}")
main()
