# -*- coding: utf-8 -*-
"""Render an HTML/CSS teaching figure to PNG by driving headless Chrome over CDP.

Same reason as scripts/drawio-cdp-shot.py: in this sandbox Chrome only renders
`data:` URIs, so `file://` and `http://127.0.0.1:...` exit 0 and write nothing.
We don't need the drawio viewer here, so this variant has no 4 MB blob to inline
and would fit under the command-line limit -- but it goes over CDP anyway so both
figure pipelines behave identically.

The source HTML carries several <section class="figure" data-figure="..."> blocks
and relies on a `?figure=<name>` query parameter to pick one. A data: URI has no
query string, so we inject the selection by rewriting the block visibility
directly instead of relying on the page's own switcher.

Usage: html-cdp-shot.py <in.html> <figure> <out.png> <w> <h> <scale>
"""
import base64
import json
import sys
import time
import urllib.request

from websocket import create_connection

SRC, FIGURE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, SCALE = int(sys.argv[4]), int(sys.argv[5]), float(sys.argv[6])
PORT = int(sys.argv[7]) if len(sys.argv) > 7 else 9222


def build_html():
    with open(SRC, encoding="utf-8") as f:
        html = f.read()
    # The page selects its figure from `?figure=<name>`. A data: URI carries no
    # query string, so patch URLSearchParams *before* the page's own script runs
    # and let the original switcher do its normal job. Reusing the page's own
    # code path (rather than re-implementing visibility rules here) means the
    # screenshot is produced by exactly the same CSS the browser preview uses.
    # This assumes a fresh target/realm per render -- see the note at the driver.
    inject = """
<script>
(function () {
  var want = %s;
  var Native = window.URLSearchParams;
  function Patched(init) {
    var inst = new Native(init);
    var nativeGet = inst.get.bind(inst);
    inst.get = function (k) {
      return (k === 'figure') ? want : nativeGet(k);
    };
    return inst;
  }
  Patched.prototype = Native.prototype;
  // Keep the static surface intact; only `new URLSearchParams(...).get` differs.
  window.URLSearchParams = Patched;
})();
</script>
""" % json.dumps(FIGURE)
    return html.replace("<body>", inject + "<body>", 1)


def http_json(path, timeout=5):
    with urllib.request.urlopen("http://127.0.0.1:%d%s" % (PORT, path),
                                timeout=timeout) as r:
        return json.load(r)


def cdp_http(path, method="PUT", timeout=10):
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (PORT, path),
                                 method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8")
    return json.loads(body) if body.strip() else {}


# Open a FRESH target for every render. `Page.setDocumentContent` reuses the
# page's JS realm, so a URLSearchParams patch from a previous figure would still
# be installed when the next one loads -- the second run then wraps the wrapper
# and `?figure=` silently stops resolving. A new target gives a clean realm.
try:
    target = cdp_http("/json/new?about:blank", method="PUT")
    ws_url = target["webSocketDebuggerUrl"]
    close_target = target.get("id")
except Exception as exc:
    sys.exit("could not create a chrome target on port %d: %s" % (PORT, exc))

ws = create_connection(ws_url, timeout=180)

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


def evaluate(expr):
    r = cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    return r.get("result", {}).get("value")


cmd("Page.enable")
cmd("Emulation.setDeviceMetricsOverride",
    {"width": W, "height": H, "deviceScaleFactor": SCALE, "mobile": False})

tree = cmd("Page.getFrameTree")
frame_id = tree["frameTree"]["frame"]["id"]
cmd("Page.setDocumentContent", {"frameId": frame_id, "html": build_html()})

# Poll for the selected section to actually be laid out before rasterising.
# The page marks it with .active, so that is the honest readiness signal.
ok = False
deadline = time.time() + 45
while time.time() < deadline:
    try:
        active = evaluate(
            "document.querySelectorAll('.figure.active').length")
        h = evaluate("var e=document.querySelector('.figure.active');"
                     "e ? Math.round(e.getBoundingClientRect().height) : 0")
        if (active or 0) == 1 and (h or 0) > 100:
            ok = True
            break
    except Exception:
        pass
    time.sleep(0.5)

if not ok:
    sys.exit("figure %r never became active (check the page's `allowed` set)"
             % FIGURE)

time.sleep(1.2)  # let font metrics settle before rasterising

res = cmd("Page.captureScreenshot",
          {"format": "png", "captureBeyondViewport": True,
           "fromSurface": True})
data = base64.b64decode(res["data"])
with open(OUT, "wb") as f:
    f.write(data)
print("wrote %s (%d bytes) at %dx%d scale %s figure=%s"
      % (OUT, len(data), W, H, SCALE, FIGURE))
ws.close()
if close_target:
    try:
        cdp_http("/json/close/%s" % close_target, method="GET")
    except Exception:
        pass
