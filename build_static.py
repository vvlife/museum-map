import json, os, shutil, re
BASE = os.path.dirname(os.path.abspath(__file__))
docs = os.path.join(BASE, "docs")
shutil.rmtree(docs, ignore_errors=True)
os.makedirs(os.path.join(docs, "static"))
for f in ["leaflet.js", "leaflet.css", "three.min.js", "globe.gl.min.js", "countries.geo.json"]:
    shutil.copy2(os.path.join(BASE, "static", f), os.path.join(docs, "static", f))
museums = json.load(open(os.path.join(BASE, "museums.json"), encoding="utf-8"))["museums"]
for extra in ("custom.json", "auto.json"):
    p = os.path.join(BASE, extra)
    if os.path.exists(p):
        museums += json.load(open(p, encoding="utf-8"))
html = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
embed = "<script>window.MUSEUMS_EMBED = %s;</script>\n<script>" % json.dumps(museums, ensure_ascii=False)
html = html.replace("<script>\nwindow.__errs", embed + "\nwindow.__errs", 1)
open(os.path.join(docs, "index.html"), "w", encoding="utf-8").write(html)
json.dump(museums, open(os.path.join(docs, "museums.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("docs/ built:", len(museums), "museums,", os.path.getsize(os.path.join(docs, "index.html")), "bytes html")
