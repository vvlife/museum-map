#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量扩充馆藏：对知名博物馆跑发现管线，自动收集官方VR链接"""
import json, os, sys, time, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from server import discover, JUNK_HOSTS  # noqa

# (name_zh, 附加英文查询词, lat, lon, category)
CANDIDATES = [
    ("芝加哥艺术博物馆", "Art Institute of Chicago", 41.8796, -87.6237, "art"),
    ("盖蒂中心", "Getty Center", 34.0780, -118.4741, "art"),
    ("美国国家美术馆", "National Gallery of Art Washington", 38.8913, -77.0199, "art"),
    ("泰特现代美术馆", "Tate Modern", 51.5076, -0.0994, "art"),
    ("维多利亚与阿尔伯特博物馆", "V&A Museum", 51.4966, -0.1722, "art"),
    ("维也纳艺术史博物馆", "Kunsthistorisches Museum", 48.2038, 16.3614, "art"),
    ("橘园美术馆", "Musee de l'Orangerie", 48.8638, 2.3222, "art"),
    ("蓬皮杜中心", "Centre Pompidou", 48.8606, 2.3522, "art"),
    ("比利时皇家美术博物馆", "Royal Museums Fine Arts Belgium", 50.8419, 4.3577, "art"),
    ("新南威尔士美术馆", "Art Gallery of New South Wales", -33.8688, 151.2173, "art"),
    ("蒂森博物馆", "Museo Thyssen-Bornemisza", 40.4161, -3.6950, "art"),
    ("毕尔巴鄂古根海姆美术馆", "Guggenheim Bilbao", 43.2687, -2.9340, "art"),
    ("罗丹美术馆", "Musee Rodin Paris", 48.8556, 2.3158, "art"),
    ("莫瑞泰斯皇家美术馆", "Mauritshuis", 52.0805, 4.3143, "art"),
    ("维多利亚国家美术馆", "NGV Melbourne", -37.8226, 144.9689, "art"),
    ("卢浮宫阿布扎比分馆", "Louvre Abu Dhabi", 24.5336, 54.3989, "art"),
    ("上海博物馆", "Shanghai Museum", 31.2303, 121.4737, "general"),
    ("南京博物院", "Nanjing Museum", 32.0415, 118.8192, "general"),
    ("河南博物院", "Henan Museum", 34.7897, 113.6675, "general"),
    ("湖南博物院", "Hunan Museum", 28.2157, 112.9869, "general"),
    ("苏州博物馆", "Suzhou Museum", 31.3245, 120.6289, "art"),
    ("香港故宫文化博物馆", "Hong Kong Palace Museum", 22.3040, 114.1596, "general"),
    ("台北故宫博物院", "National Palace Museum Taipei", 25.1024, 121.5485, "general"),
    ("新加坡国家博物馆", "National Museum of Singapore", 1.2966, 103.8485, "general"),
    ("安大略皇家博物馆", "Royal Ontario Museum", 43.6677, -79.3948, "general"),
    ("东京国立科学博物馆", "National Museum of Nature and Science Tokyo", 35.7164, 139.7765, "science"),
    ("美国自然历史博物馆", "American Museum of Natural History", 40.7813, -73.9740, "nature"),
    ("菲尔德自然史博物馆", "Field Museum Chicago", 41.8663, -87.6170, "nature"),
    ("巴黎自然历史博物馆", "Museum national Histoire naturelle", 48.8422, 2.3562, "nature"),
    ("上海自然博物馆", "Shanghai Natural History Museum", 31.2369, 121.4669, "nature"),
    ("伦敦科学博物馆", "Science Museum London", 51.4978, -0.1745, "science"),
    ("德意志博物馆", "Deutsches Museum", 48.1298, 11.5834, "science"),
    ("史密森尼航空航天博物馆", "Smithsonian Air and Space Museum", 38.8882, -77.0199, "science"),
    ("中国科学技术馆", "China Science and Technology Museum", 40.0042, 116.3886, "science"),
    ("陕西历史博物馆", "Shaanxi History Museum", 34.2226, 108.9533, "history"),
    ("秦始皇帝陵博物院", "Terracotta Army Museum", 34.3847, 109.2785, "heritage"),
    ("三星堆博物馆", "Sanxingdui Museum", 30.9933, 104.2000, "heritage"),
    ("墨西哥国立人类学博物馆", "Museo Nacional de Antropologia", 19.4260, -99.1863, "history"),
    ("埃及文明国家博物馆", "NMEC Cairo", 30.0085, 31.2485, "history"),
    ("美国国家历史博物馆", "Smithsonian National Museum of American History", 38.8913, -77.0300, "history"),
    ("帝国战争博物馆", "Imperial War Museum London", 51.4958, -0.1087, "history"),
    ("广岛和平纪念资料馆", "Hiroshima Peace Memorial Museum", 34.3928, 132.4522, "history"),
    ("成都博物馆", "Chengdu Museum", 30.6600, 104.0633, "general"),
    ("浙江省博物馆", "Zhejiang Museum", 30.2500, 120.1500, "general"),
]

def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)

def pick_best(results):
    """从发现结果中挑最像官方VR入口的一条"""
    if not results:
        return None
    def rank(r):
        s = 0
        if r.get("from_site"): s += 4
        if r.get("is_vr"): s += 3
        if not any(j in r.get("host", "") for j in JUNK_HOSTS): s += 2
        if any(k in r.get("host", "") for k in ("museum", "muse", "gov", "org", "edu", "artsandculture")): s += 1
        s += min(r.get("score", 0), 4)
        return s
    best = max(results, key=rank)
    return best if rank(best) >= 6 else None

def main():
    existing = {m["name_zh"] for m in json.load(open("museums.json", encoding="utf-8"))["museums"]}
    auto_path = "auto.json"
    auto = json.load(open(auto_path, encoding="utf-8")) if os.path.exists(auto_path) else []
    done = {m["name_zh"] for m in auto}
    ok, fail = 0, 0
    for name_zh, name_en, lat, lon, cat in CANDIDATES:
        if name_zh in existing or name_zh in done:
            log(f"跳过(已存在): {name_zh}")
            continue
        try:
            res = discover(name_zh)
            best = pick_best(res)
            if best:
                item = {
                    "id": "auto-%d-%d" % (int(time.time()), ok),
                    "name_zh": name_zh, "name_en": name_en,
                    "city": "", "country": "",
                    "lat": lat, "lon": lon, "category": cat,
                    "vr_url": best["url"],
                    "type": "🌐 自动发现" + ("(官网嗅探)" if best.get("from_site") else ""),
                    "status": "auto", "notes": best.get("title", "")[:80],
                    "needs_review": True,
                }
                auto.append(item)
                json.dump(auto, open(auto_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                ok += 1
                log(f"✅ {name_zh} -> {best['host']} | {best['url'][:70]}")
            else:
                fail += 1
                log(f"❌ 未找到可靠VR链接: {name_zh}")
        except Exception as e:
            fail += 1
            log(f"⚠️ {name_zh} 出错: {e}")
            traceback.print_exc()
        time.sleep(2)
    log(f"完成! 新增 {ok} 馆, 未找到 {fail} 馆")

if __name__ == "__main__":
    main()
