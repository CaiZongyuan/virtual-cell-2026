# -*- coding: utf-8 -*-
"""Render a .drawio to PNG by driving headless Chrome over the DevTools
protocol.

Why CDP instead of `chrome --screenshot file://...`:

  in this environment Chrome is only able to render `data:` URIs.  Both
  `file://` and `http://127.0.0.1:...` come back with an empty PNG (Chrome
  exits 0 and writes nothing).  Overserving the sandbox does not help.  a
  `data:` URL would work, but render.html plus the 4 MB draw.io viewer blows
  past the 32767-character Windows command line.

  So: launch Chrome with `--remote-debugging-port` (a bind, not a connect)
  and push the page in over CDP with Page.setDocumentContent.  The viewer JS
  travels as a base64 `data:` src, which is absolute and therefore resolves
  even though the document has no base URL.  No filesystem read, no network.

Usage: cdp_shot.py <in.drawio> <viewer.js> <out.png> <w> <h> <scale> [port]
"""
import base64
import json
import sys
import time
import urllib.request

from websocket import create_connection

SRC, VIEWER, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, SCALE = int(sys.argv[4]), int(sys.argv[5]), float(sys.argv[6])
PORT = int(sys.argv[7]) if len(sys.argv) > 7 else 9222


def build_html():
    with open(SRC, encoding="utf-8") as f:
        xml = f.read()
    with open(VIEWER, encoding="utf-8") as f:
        js = f.read()
    js_b64 = base64.b64encode(js.encode("utf-8")).decode("ascii")
    cfg = {"nav": False, "resize": False, "border": 0, "zoom": 1,
           "toolbar": None, "xml": xml}
    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>state-arch</title>
<style>
  html,body{margin:0;padding:0;background:#ffffff;}
  #wrap{width:%dpx;height:%dpx;background:#ffffff;}
</style></head>
<body>
<div id="wrap" class="mxgraph"></div>
<script>
document.getElementById('wrap').setAttribute('data-mxgraph', JSON.stringify(%s));
</script>
<script src="data:text/javascript;base64,%s"></script>
</body></html>
""" % (W, H, json.dumps(cfg, ensure_ascii=False), js_b64)


def http_json(path, timeout=5):
    with urllib.request.urlopen("http://127.0.0.1:%d%s" % (PORT, path),
                                timeout=timeout) as r:
        return json.load(r)


ws = None
deadline = time.time() + 45
while time.time() < deadline:
    try:
        pages = [t for t in http_json("/json")
                 if t.get("type") == "page"
                 and t.get("webSocketDebuggerUrl")]
        if pages:
            ws = create_connection(pages[0]["webSocketDebuggerUrl"], timeout=180)
            break
    except Exception:
        pass
    time.sleep(0.5)

if ws is None:
    sys.exit("could not attach to chrome on port %d" % PORT)

_mid = [0]


def cmd(method, params=None):
    _mid[0] += 1
    mine = _mid[0]
    ws.send(json.dumps({"id": mine, "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == mine:
            if "error" in msg:
                raise RuntimeError("%s -> %s" % (method, msg["error"]))
            return msg.get("result", {})


cmd("Page.enable")
cmd("Emulation.setDeviceMetricsOverride",
    {"width": W, "height": H, "deviceScaleFactor": SCALE, "mobile": False})

tree = cmd("Page.getFrameTree")
frame_id = tree["frameTree"]["frame"]["id"]
cmd("Page.setDocumentContent", {"frameId": frame_id, "html": build_html()})

# the viewer is synchronous-ish, but give it a real budget and poll for the
# produced <svg> so we never screenshot a half-built graph.
ok = False
deadline = time.time() + 90
while time.time() < deadline:
    try:
        r = cmd("Runtime.evaluate",
                {"expression": "document.querySelectorAll('svg').length",
                 "returnByValue": True})
        if (r.get("result", {}).get("value") or 0) > 0:
            ok = True
            break
    except Exception:
        pass
    time.sleep(0.5)

if not ok:
    sys.exit("viewer produced no <svg>")

time.sleep(1.5)  # let font metrics settle before rasterising

res = cmd("Page.captureScreenshot",
          {"format": "png", "captureBeyondViewport": True,
           "fromSurface": True})
data = base64.b64decode(res["data"])
with open(OUT, "wb") as f:
    f.write(data)
print("wrote %s (%d bytes) at %dx%d scale %s"
      % (OUT, len(data), W, H, SCALE))
ws.close()
