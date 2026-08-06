#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""博物馆世界地图 - 轻量后端（无第三方依赖）
服务静态文件 + 数据API + 必应搜索发现VR链接 + 用户添加博物馆
"""
import json, os, re, html, time, base64, urllib.parse, urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

BASE = os.path.dirname(os.path.abspath(__file__))
PORT = 8765
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

VR_KEYS = ["virtual", "tour", "360", "vr", "pano", "artsandculture", "street view", "online tour",
           "全景", "虚拟", "漫游", "数字", "线上", "云游", "云展"]
JUNK_HOSTS = ("baike.", "zhihu.", "douban.", "zhidao.", "mfa.gov", "iciba.", "dict.", "hanyuguoxue",
              "chagushici", "39017", "eudic", "cambridge.org", "wikiwand", "sogou.com/m",
              "tmall.", "taobao.", "jd.com", "jd.hk", "amazon.", "ebay.", "tmall.hk")

def load_json(name, default):
    p = os.path.join(BASE, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def all_museums():
    base = load_json("museums.json", {}).get("museums", [])
    custom = load_json("custom.json", [])
    auto = load_json("auto.json", [])
    return base + custom + auto

def local_search(q):
    q = q.strip().lower()
    if not q:
        return []
    out = []
    for m in all_museums():
        hay = " ".join(str(m.get(k, "")) for k in
                       ("name_zh", "name_en", "city", "country", "type", "notes")).lower()
        if q in hay:
            out.append(m)
    return out

def bing_decode(url):
    """解开 bing.com/ck/a 重定向链接"""
    if "bing.com/ck/a" in url:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        u = qs.get("u", [""])[0]
        if u.startswith("a1"):
            try:
                pad = "=" * (-len(u[2:]) % 4)
                return base64.urlsafe_b64decode(u[2:] + pad).decode("utf-8", "ignore")
            except Exception:
                return url
    return url

def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

def bing_search(query, count=8):
    """单次必应搜索，返回原始结果列表"""
    url = "https://cn.bing.com/search?q=" + urllib.parse.quote(query) + f"&count={count}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=10) as r:
        page = r.read().decode("utf-8", "ignore")
    results = []
    for block in re.findall(r'<li class="b_algo".*?</li>', page, re.S):
        m = re.search(r'<h2[^>]*><a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not m:
            continue
        link = bing_decode(html.unescape(m.group(1)))
        title = strip_tags(m.group(2))
        pm = re.search(r'<p[^>]*>(.*?)</p>', block, re.S)
        snippet = strip_tags(pm.group(1)) if pm else ""
        host = urllib.parse.urlparse(link).netloc
        results.append({"title": title, "url": link, "snippet": snippet[:160], "host": host})
    return results

def name_core(name):
    """提取馆名核心词用于相关性过滤"""
    c = re.sub(r'(博物馆|博物院|美术馆|纪念馆|陈列馆|图书馆|museum|gallery|of art|the )', '', name.lower()).strip()
    return c if len(c) >= 2 else name.lower()

def relevance(name, r):
    """结果与馆名的相关度评分，0=垃圾"""
    text = (r["title"] + " " + r["snippet"] + " " + r["url"]).lower()
    core = name_core(name)
    score = 0
    if name.lower() in text:
        score += 3
    elif len(core) >= 2 and core in text:
        score += 2
    elif any(w in text for w in ("museum", "博物", "museum", "galler", "louvre", "palace", "故宫")):
        score += 1
    if any(k in (r["title"] + " " + r["url"] + " " + r["snippet"]).lower() for k in VR_KEYS):
        score += 2
    return score

def scan_site_vr(home_url):
    """抓取官网首页，嗅探站内VR入口链接"""
    out = []
    try:
        req = urllib.request.Request(home_url, headers=UA)
        with urllib.request.urlopen(req, timeout=8) as r:
            page = r.read(400000).decode("utf-8", "ignore")
    except Exception:
        return out
    base = home_url
    for href, text in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', page, re.S)[:600]:
        label = strip_tags(text)
        combo = (href + " " + label).lower()
        if not any(k in combo for k in VR_KEYS):
            continue
        if href.startswith("javascript") or href == "#":
            continue
        full = urllib.parse.urljoin(base, html.unescape(href))
        out.append({"title": label or full, "url": full,
                    "snippet": "官网站内发现的 VR/全景入口", "host": urllib.parse.urlparse(full).netloc,
                    "from_site": True})
        if len(out) >= 3:
            break
    return out

def discover(name):
    """多查询 + 相关性过滤 + 官网VR嗅探"""
    seen, pool = set(), []
    queries = [name, name + " 全景", name + " virtual tour"]
    for q in queries:
        try:
            for r in bing_search(q):
                key = r["url"].rstrip("/").split("#")[0]
                if key in seen:
                    continue
                seen.add(key)
                r["score"] = relevance(name, r)
                r["is_vr"] = any(k in (r["title"] + " " + r["url"] + " " + r["snippet"]).lower()
                                 for k in VR_KEYS)
                pool.append(r)
        except Exception:
            pass
        time.sleep(0.6)
    # 过滤完全无关的，垃圾源降权
    good = [r for r in pool if r["score"] > 0]
    for r in good:
        if any(j in r["host"] for j in JUNK_HOSTS):
            r["score"] -= 2
    good.sort(key=lambda r: (not r["is_vr"], -r["score"]))
    good = good[:8]
    # 对前2个非垃圾官网做站内VR嗅探，结果置顶
    site_hits, scanned = [], 0
    for r in good:
        if scanned >= 2:
            break
        if any(j in r["host"] for j in JUNK_HOSTS) or not r["host"]:
            continue
        scanned += 1
        for s in scan_site_vr(r["url"]):
            s["is_vr"] = True
            site_hits.append(s)
    return site_hits + good

# ================= 翻译引擎（MyMemory，自动检测语言） =================
_tcache = load_json("translate_cache.json", {})

def save_tcache():
    try:
        with open(os.path.join(BASE, "translate_cache.json"), "w", encoding="utf-8") as f:
            json.dump(_tcache, f, ensure_ascii=False)
    except Exception:
        pass

def _mymemory(q, pair):
    url = "https://api.mymemory.translated.net/get?" + urllib.parse.urlencode({"q": q, "langpair": pair})
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 429:  # 限流则等待重试一次
            time.sleep(3)
            with urllib.request.urlopen(req, timeout=15) as r:
                d = json.loads(r.read().decode())
        else:
            raise
    rd = d.get("responseData", {})
    return rd.get("translatedText"), rd.get("detectedLanguage")

def guess_source(t):
    for ch in t:
        o = ord(ch)
        if 0x4e00 <= o <= 0x9fff: return "zh-CN"
        if 0x3040 <= o <= 0x30ff: return "ja"
        if 0xac00 <= o <= 0xd7af: return "ko"
        if 0x0400 <= o <= 0x04ff: return "ru"
        if 0x0600 <= o <= 0x06ff: return "ar"
    return "en"

def translate_text(text, target="zh-CN"):
    text = text.strip()
    if not text:
        return text
    key = target + "|" + text[:400]
    if key in _tcache:
        return _tcache[key]
    src = guess_source(text)
    if src.startswith("zh") and target.startswith("zh"):
        return text
    result = None
    try:
        result, _ = _mymemory(text[:450], f"{src}|{target}")
        if result and result.strip().lower() == text.strip().lower():
            result = None
    except Exception:
        result = None
    if not result:
        try:
            _, det = _mymemory(text[:450], "Autodetect|en")
            if det and not det.lower().startswith(("zh",)):
                result, _ = _mymemory(text[:450], f"{det}|{target}")
        except Exception:
            pass
    if not result:
        result = text
    if result != text:  # 失败（原文退回）不写入缓存，避免污染
        _tcache[key] = result
        if len(_tcache) > 3000:
            for k in list(_tcache)[:800]:
                _tcache.pop(k, None)
        save_tcache()
    return result

# ================= 内嵌检测 =================
def frame_check(url):
    """检查目标站点是否允许被 iframe 嵌入"""
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=10) as r:
            xfo = (r.headers.get("X-Frame-Options") or "").upper()
            csp = (r.headers.get("Content-Security-Policy") or "").lower()
            final = r.geturl()
        if "DENY" in xfo or "SAMEORIGIN" in xfo:
            return {"frameable": False, "reason": "X-Frame-Options", "final_url": final}
        m = re.search(r"frame-ancestors\s+([^;]+)", csp)
        if m and ("'none'" in m.group(1) or "'self'" in m.group(1)):
            return {"frameable": False, "reason": "CSP frame-ancestors", "final_url": final}
        return {"frameable": True, "final_url": final}
    except Exception as e:
        return {"frameable": None, "reason": str(e)[:80]}

# ================= 网页代理 + 整页翻译 =================
_proxy_cache = {}

def translate_html_nodes(doc, max_nodes=60, max_chars=12000):
    from concurrent.futures import ThreadPoolExecutor
    stash = []
    def stash_cb(m):
        stash.append(m.group(0))
        return "\x00%d\x00" % (len(stash) - 1)
    doc = re.sub(r"<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->", stash_cb, doc, flags=re.S | re.I)
    count = [0]; chars = [0]
    todos = {}
    def pick(m):
        t = m.group(1)
        s = t.strip()
        if count[0] >= max_nodes or chars[0] >= max_chars or len(s) < 3 or len(s) > 300:
            return m.group(0)
        if not re.search(r"[A-Za-zÀ-ɏЀ-ӿ぀-ヿ가-힯]", s):
            return m.group(0)
        count[0] += 1; chars[0] += len(s)
        todos.setdefault(s, t)
        return m.group(0)
    doc = re.sub(r">([^<>]+)<", pick, doc)
    if todos:
        uniq = list(todos.keys())
        with ThreadPoolExecutor(max_workers=3) as ex:
            results = list(ex.map(lambda s: translate_text(s), uniq))
        trans = dict(zip(uniq, results))
        def sub(m):
            t = m.group(1); s = t.strip()
            if s in trans and trans[s] != s:
                return ">" + t.replace(s, html.escape(trans[s])) + "<"
            return m.group(0)
        doc = re.sub(r">([^<>]+)<", sub, doc)
    doc = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], doc)
    return doc

def proxy_fetch(url, do_translate):
    ck = (url, do_translate)
    if ck in _proxy_cache:
        return _proxy_cache[ck]
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=18) as r:
        ctype = r.headers.get("Content-Type", "text/html")
        raw = r.read(2_500_000)
        final = r.geturl()
    if "text/html" not in ctype:
        out = (raw, ctype, final)
        _proxy_cache[ck] = out
        return out
    enc = "utf-8"
    m = re.search(r"charset=([\w-]+)", ctype)
    if m:
        enc = m.group(1)
    doc = raw.decode(enc, "ignore")
    doc = re.sub(r"<meta[^>]+http-equiv=[\"']?Content-Security-Policy[^>]*>", "", doc, flags=re.I)
    doc = re.sub(r"<meta[^>]+http-equiv=[\"']?X-Frame-Options[^>]*>", "", doc, flags=re.I)
    def rw(m):
        attr, q, v = m.group(1), m.group(2), m.group(3)
        if v.startswith(("javascript:", "#", "data:", "mailto:", "tel:")):
            return m.group(0)
        return '%s=%s%s%s' % (attr, q, urllib.parse.urljoin(final, html.unescape(v)), q)
    doc = re.sub(r'(src|href|action)\s*=\s*(["\'])([^"\']+)\2', rw, doc)
    base_tag = '<base href="%s">' % final
    if re.search(r"<head[^>]*>", doc, re.I):
        doc = re.sub(r"(<head[^>]*>)", r"\1" + base_tag, doc, count=1, flags=re.I)
    else:
        doc = base_tag + doc
    if do_translate:
        doc = translate_html_nodes(doc)
    out = (doc.encode("utf-8"), "text/html; charset=utf-8", final)
    _proxy_cache[ck] = out
    if len(_proxy_cache) > 40:
        _proxy_cache.pop(next(iter(_proxy_cache)))
    return out


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # 静音日志
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        if u.path == "/api/museums":
            self._json({"museums": all_museums()})
        elif u.path == "/api/search":
            q = qs.get("q", [""])[0]
            self._json({"q": q, "results": local_search(q)})
        elif u.path == "/api/discover":
            q = qs.get("q", [""])[0].strip()
            if not q:
                return self._json({"error": "missing q"}, 400)
            try:
                res = discover(q)
                self._json({"q": q, "results": res})
            except Exception as e:
                self._json({"error": str(e), "results": []}, 502)
        elif u.path == "/api/geocode":
            q = qs.get("q", [""])[0]
            self._json(self.geocode(q))
        elif u.path == "/api/framecheck":
            url = qs.get("url", [""])[0]
            if not url:
                return self._json({"error": "missing url"}, 400)
            self._json(frame_check(url))
        elif u.path == "/api/translate":
            text = qs.get("text", [""])[0]
            to = qs.get("to", ["zh-CN"])[0]
            if not text:
                return self._json({"error": "missing text"}, 400)
            try:
                self._json({"src": text, "text": translate_text(text, to)})
            except Exception as e:
                self._json({"error": str(e), "text": text}, 502)
        elif u.path == "/proxy":
            url = qs.get("url", [""])[0]
            do_tr = qs.get("t", ["0"])[0] == "1"
            if not url.startswith("http"):
                return self._json({"error": "bad url"}, 400)
            try:
                raw, ctype, final = proxy_fetch(url, do_tr)
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except Exception as e:
                body = ("<meta charset='utf-8'><body style='font-family:serif;background:#faf4e6;padding:40px'>"
                        "<h3>代理加载失败</h3><p>%s</p><p><a href='%s'>直接前往本站 →</a></p>" % (html.escape(str(e)[:200]), html.escape(url))).encode("utf-8")
                self.send_response(502)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        else:
            super().do_GET()

    def geocode(self, q):
        try:
            url = "https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" + urllib.parse.quote(q)
            req = urllib.request.Request(url, headers={"User-Agent": "museum-world-map"})
            with urllib.request.urlopen(req, timeout=4) as r:
                arr = json.loads(r.read().decode())
            if arr:
                return {"lat": float(arr[0]["lat"]), "lon": float(arr[0]["lon"])}
        except Exception:
            pass
        return {"lat": None, "lon": None}

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/api/add":
            n = int(self.headers.get("Content-Length", 0))
            try:
                d = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception:
                return self._json({"error": "bad json"}, 400)
            if not d.get("name_zh") or not d.get("vr_url"):
                return self._json({"error": "name_zh & vr_url required"}, 400)
            if d.get("lat") is None or d.get("lon") is None:
                return self._json({"error": "lat/lon required"}, 400)
            item = {
                "id": "custom-%d" % int(time.time()),
                "name_zh": d.get("name_zh", ""), "name_en": d.get("name_en", ""),
                "city": d.get("city", ""), "country": d.get("country", ""),
                "lat": float(d["lat"]), "lon": float(d["lon"]),
                "vr_url": d["vr_url"], "type": d.get("type", "网上发现"),
                "status": "custom", "notes": d.get("notes", ""),
            }
            p = os.path.join(BASE, "custom.json")
            cur = load_json("custom.json", [])
            cur.append(item)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(cur, f, ensure_ascii=False, indent=2)
            self._json({"ok": True, "item": item})
        else:
            self._json({"error": "not found"}, 404)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

if __name__ == "__main__":
    os.chdir(BASE)
    print(f"Serving on http://localhost:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
