#!/usr/bin/env python3
r"""Read-only status of the A1 mini over LAN MQTT: one "pushall" request, then print the state, any
error or HMS alert, and what the AMS holds. It sends nothing else. Standard library only, so it runs on
the arm Pi as it is; the printer's IP, serial and access code come in on stdin, never in argv:

    { printf '%s\n%s\n%s\n' "$A1_MINI_IP" "$A1_MINI_SERIAL" "$A1_MINI_ACCESS_CODE"; cat a1mini_status.py; } |
      ssh "$ARM_PI_USERNAME@$ARM_PI_HOSTNAME" 'python3 -c "import sys; IP=sys.stdin.readline().strip();
      SERIAL=sys.stdin.readline().strip(); CODE=sys.stdin.readline().strip(); exec(sys.stdin.read())"'
"""
import json, socket, ssl, struct, time
def s(b): return struct.pack(">H", len(b)) + b
def pkt(t, body):
    n, out = len(body), b""
    while True:
        d, n = n % 128, n // 128
        out += bytes([d | (0x80 if n else 0)])
        if not n: break
    return bytes([t]) + out + body
def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        c = sock.recv(n - len(buf))
        if not c: raise EOFError("closed")
        buf += c
    return buf
def read_pkt(sock):
    t = recv_exact(sock, 1)[0]; mult, n = 1, 0
    while True:
        d = recv_exact(sock, 1)[0]; n += (d & 127) * mult; mult *= 128
        if not d & 128: break
    return t, recv_exact(sock, n)
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
raw = socket.create_connection((IP, 8883), timeout=10)
sock = ctx.wrap_socket(raw)
sock.sendall(pkt(0x10, s(b"MQTT") + bytes([4, 0xC2]) + struct.pack(">H", 60) + s(b"ci-status-%d" % int(time.time())) + s(b"bblp") + s(CODE.encode())))
t, body = read_pkt(sock)
print("connack rc", body[1] if t >> 4 == 2 else ("unexpected", t))
if t >> 4 == 2 and body[1] == 0:
    sock.sendall(pkt(0x82, struct.pack(">H", 1) + s(("device/%s/report" % SERIAL).encode()) + b"\x00"))
    sock.sendall(pkt(0x30, s(("device/%s/request" % SERIAL).encode()) + json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}).encode()))
    deadline = time.time() + 20
    while time.time() < deadline:
        t, body = read_pkt(sock)
        if t >> 4 != 3: continue
        tl = struct.unpack(">H", body[:2])[0]; payload = body[2 + tl:]
        try: msg = json.loads(payload)
        except Exception: continue
        p = msg.get("print", {})
        if "gcode_state" not in p: continue
        ams = p.get("ams", {})
        trays = []
        for u in ams.get("ams", []):
            for tr in u.get("tray", []):
                trays.append({"slot": "A%d" % (int(tr.get("id", 0)) + 1), "type": tr.get("tray_type"), "name": tr.get("tray_sub_brands"),
                              "colour": tr.get("tray_color"), "remain_pct": tr.get("remain"), "idx": tr.get("tray_info_idx")})
        out = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "gcode_state": p.get("gcode_state"),
               "job": p.get("subtask_name"), "percent": p.get("mc_percent"), "remaining_min": p.get("mc_remaining_time"),
               "layer": [p.get("layer_num"), p.get("total_layer_num")], "print_error": p.get("print_error"),
               "hms": p.get("hms"), "nozzle_c": [p.get("nozzle_temper"), p.get("nozzle_target_temper")],
               "bed_c": [p.get("bed_temper"), p.get("bed_target_temper")], "nozzle_diameter": p.get("nozzle_diameter"),
               "tray_now": ams.get("tray_now"), "ams_trays": trays,
               "external_spool": {k: p.get("vt_tray", {}).get(k) for k in ("tray_type", "tray_color")}}
        print(json.dumps(out, indent=1))
        break
sock.sendall(b"\xe0\x00"); sock.close()
