#!/usr/bin/env python3
"""Minimal Chrome DevTools Protocol client (stdlib only) for testing the site.
usage: python3 site_cdp_test.py URL OUTPREFIX W H WAIT_S [steps.json]  (serve the site with python3 -m http.server first)
steps: list of {"js": "...", "wait": s, "shot": "name", "clip_selector": "#bom", "theme": "dark"}
Prints console messages and exceptions; writes OUTPREFIX-<name>.png."""
import base64, json, os, socket, struct, subprocess, sys, tempfile, time, urllib.request

url, out, W, H, WAIT = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
steps = json.load(open(sys.argv[6])) if len(sys.argv) > 6 else []
port = 9333 + os.getpid() % 500
prof = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(out)))
chrome = subprocess.Popen(["google-chrome", "--headless=new", "--no-sandbox", "--enable-unsafe-swiftshader", "--use-angle=swiftshader",
                           f"--remote-debugging-port={port}", f"--user-data-dir={prof}", "--hide-scrollbars",
                           f"--window-size={W},{H}", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(100):
    try:
        tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
        ws = [t for t in tabs if t["type"] == "page"][0]["webSocketDebuggerUrl"]
        break
    except Exception:
        time.sleep(0.2)
host, path = ws[len("ws://"):].split("/", 1)
s = socket.create_connection((host.split(":")[0], int(host.split(":")[1])))
key = base64.b64encode(os.urandom(16)).decode()
s.send(f"GET /{path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n".encode())
hdr = b""
while b"\r\n\r\n" not in hdr:
    hdr += s.recv(1)
buf = b""


def recv_exact(n):
    global buf
    while len(buf) < n:
        d = s.recv(1 << 20)
        if not d:
            raise EOFError
        buf += d
    r, buf = buf[:n], buf[n:]
    return r


def recv_msg():
    data = b""
    while True:
        b0, b1 = recv_exact(2)
        ln = b1 & 0x7F
        if ln == 126:
            ln = struct.unpack(">H", recv_exact(2))[0]
        elif ln == 127:
            ln = struct.unpack(">Q", recv_exact(8))[0]
        data += recv_exact(ln)
        if b0 & 0x80:
            return json.loads(data)


def send(obj):
    p = json.dumps(obj).encode()
    mask = os.urandom(4)
    h = bytes([0x81])
    if len(p) < 126:
        h += bytes([0x80 | len(p)])
    elif len(p) < 65536:
        h += bytes([0x80 | 126]) + struct.pack(">H", len(p))
    else:
        h += bytes([0x80 | 127]) + struct.pack(">Q", len(p))
    s.send(h + mask + bytes(c ^ mask[i % 4] for i, c in enumerate(p)))


mid = 0
logs = []


def handle(m):
    meth = m.get("method", "")
    if meth == "Runtime.consoleAPICalled":
        a = m["params"]["args"]
        logs.append(f"console.{m['params']['type']}: " + " ".join(str(x.get("value", x.get("description", ""))) for x in a)[:400])
    elif meth == "Runtime.exceptionThrown":
        d = m["params"]["exceptionDetails"]
        logs.append("EXCEPTION: " + (d.get("exception", {}).get("description") or d.get("text", ""))[:600])
    elif meth == "Log.entryAdded":
        e = m["params"]["entry"]
        logs.append(f"log.{e['level']}: {e['text'][:300]} {e.get('url', '')[-60:]}")


def call(method, params=None, timeout=120):
    global mid
    mid += 1
    send({"id": mid, "method": method, "params": params or {}})
    t0 = time.time()
    while time.time() - t0 < timeout:
        m = recv_msg()
        if m.get("id") == mid:
            return m.get("result", m.get("error"))
        handle(m)
    raise TimeoutError(method)


def pump(sec):
    s.settimeout(0.2)
    t0 = time.time()
    while time.time() - t0 < sec:
        try:
            handle(recv_msg())
        except socket.timeout:
            pass
    s.settimeout(None)


def ev(js):
    r = call("Runtime.evaluate", {"expression": js, "awaitPromise": True, "returnByValue": True})
    return r.get("result", {}).get("value") if isinstance(r, dict) else r


def shot(name, selector=None):
    params = {"format": "png", "captureBeyondViewport": bool(selector)}
    if selector:
        rect = ev(f"(()=>{{const e=document.querySelector({json.dumps(selector)});e.scrollIntoView();const r=e.getBoundingClientRect();return [r.left+scrollX,r.top+scrollY,r.width,Math.min(r.height,2400)]}})()")
        params["clip"] = {"x": rect[0], "y": rect[1], "width": rect[2], "height": rect[3], "scale": 1}
    r = call("Page.captureScreenshot", params)
    fn = f"{out}-{name}.png"
    open(fn, "wb").write(base64.b64decode(r["data"]))
    print("wrote", fn)


call("Runtime.enable"); call("Log.enable"); call("Page.enable")
call("Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": W < 600})
call("Page.navigate", {"url": url})
pump(WAIT)
if not steps:
    shot("view")
for st in steps:
    if "theme" in st:
        call("Emulation.setEmulatedMedia", {"features": [{"name": "prefers-color-scheme", "value": st["theme"]}]})
    if "mouse" in st:
        x, y = st["mouse"]
        call("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y, "button": "none", "pointerType": "mouse"})
    if "js" in st:
        print("js:", str(ev(st["js"]))[:600])
    pump(st.get("wait", 0.5))
    if "shot" in st:
        shot(st["shot"], st.get("clip_selector"))
pump(0.5)
print("\n".join(logs) or "(no console messages)")
chrome.kill()
subprocess.run(["rm", "-rf", prof])
