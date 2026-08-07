#!/usr/bin/env python3
"""深链审查：确保每个馆的 vr_url 直达 VR 界面而非首页"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server

BASE = os.path.dirname(os.path.abspath(__file__))
VR_PATH = re.compile(r'(pano|virtual|/vr|_vr|360|streetview|tour|visites-en-ligne|online-tours|vt3|hypervision|全景|漫游|虚拟|数字展厅|v360|virtualroaming)', re.I)

def is_direct(url):
    return bool(VR_PATH.search(url))

def best_sniff(url):
    """在页面上找最强VR入口，优先同域名"""
    host = re.sub(r'^www\.', '', re.search(r'https?://([^/]+)', url).group(1)) if re.match(r'https?://', url) else ''
    cands = server.scan_site_vr(url)
    if not cands: return None
    def score(c):
        s = 0
        cu = c['url']
        if host and host in cu: s += 3
        if re.search(r'(pano|360|/vr|_vr|streetview|全景)', cu, re.I): s += 3
        if re.search(r'(virtual|tour|virtualroaming|v360|漫游|虚拟|数字)', cu, re.I): s += 2
        return s
    cands.sort(key=lambda c: -score(c))
    return cands[0]['url'] if score(cands[0]) >= 2 else None

for fname in ["museums.json", "custom.json", "auto.json"]:
    p = os.path.join(BASE, fname)
    d = json.load(open(p, encoding='utf-8'))
    lst = d["museums"] if fname == "museums.json" else d
    for m in lst:
        u = m['vr_url']
        if is_direct(u):
            print('直达✓', m['name_zh'], '|', u[:65]); continue
        if 'artsandculture.google.com' in u:
            print('GAC·保留', m['name_zh']); continue
        try:
            better = best_sniff(u)
        except Exception as e:
            better = None
        if better and is_direct(better):
            print('深挖→', m['name_zh'], u[:45], '=>', better[:65])
            m['vr_url'] = better
            m['notes'] = (m.get('notes','')[:30] + ' [VR直达]').strip()
            m['frameable'] = None  # 需重新检测
        else:
            print('保留首页', m['name_zh'], '|', u[:55])
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('DONE')
