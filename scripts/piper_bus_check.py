#!/usr/bin/env python3
"""Is the PiPER on? Check can0 on the arm Pi without enabling or moving anything.

Run it on the Pi, or from a session over SSH without copying anything there:

    ssh "$ARM_PI_USERNAME@$ARM_PI_HOSTNAME" 'python3 - --query' < scripts/piper_bus_check.py

Standard library only. It prints can0's state and counters, listens for --listen-s and, with
--query, sends one firmware-version query (0x4AF, data 01 00 .., the frame piper_sdk's
ConnectPort sends) and listens again. It never enables the motors, commands motion, writes a
setting or touches the interface.

A silent bus does not mean the arm is off: on 2026-10-14 it was powered but sent nothing until
asked (#25). What the answers mean:
- feedback frames (0x2A1-0x2A8, 0x251-0x256, 0x261-0x266): on and talking.
- only 0x151 and 0x155-0x159: the arm is set as a leader ("teaching input") arm, which sends
  control frames for a follower and no feedback.
- nothing until queried, then an acknowledged query and a reply on 0x4AF: the controller is
  powered but not running normally. Power-cycle the arm.
- an unacknowledged query: no powered node on this adapter's wires. The adapter keeps
  retrying the frame until something acknowledges it, so restart can0 afterwards.
"""
import argparse
import collections
import re
import socket
import struct
import subprocess
import time

FEEDBACK = set(range(0x2A1, 0x2A9)) | set(range(0x251, 0x257)) | set(range(0x261, 0x267))
LEADER = {0x151, 0x155, 0x156, 0x157, 0x159}
FIRMWARE = 0x4AF
FRAME = "=IB3x8s"  # struct can_frame


def can_stats(can):
    def counter(name):
        return int(open(f"/sys/class/net/{can}/statistics/{name}").read())
    out = subprocess.run(["ip", "-details", "link", "show", can],
                         capture_output=True, text=True).stdout
    state = re.search(r"can state (\S+)", out)
    return {"oper": open(f"/sys/class/net/{can}/operstate").read().strip(),
            "state": state.group(1) if state else "?",
            "rx": counter("rx_packets"), "tx": counter("tx_packets")}


def listen(sock, seconds):
    """Count frames per CAN ID for `seconds`; also collect the 0x4AF reply bytes."""
    ids, firmware = collections.Counter(), bytearray()
    end = time.time() + seconds
    while (left := end - time.time()) > 0:
        sock.settimeout(left)
        try:
            can_id, dlc, data = struct.unpack(FRAME, sock.recv(16))
        except socket.timeout:
            break
        can_id &= socket.CAN_EFF_MASK
        ids[can_id] += 1
        if can_id == FIRMWARE:
            firmware += data[:dlc]
    return ids, firmware


def show(ids, seconds=None):
    if not ids:
        print("  no frames")
    for can_id, n in sorted(ids.items()):
        print(f"  0x{can_id:03X}: {n} frames" + (f" ({n / seconds:.0f} Hz)" if seconds else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--can", default="can0")
    ap.add_argument("--listen-s", type=float, default=3.0)
    ap.add_argument("--query", action="store_true",
                    help="send one firmware-version query (0x4AF) and listen for the reply")
    args = ap.parse_args()

    st = can_stats(args.can)
    print(f"{args.can}: {st['oper']}, {st['state']}, {st['rx']} rx / {st['tx']} tx frames so far")
    if st["state"] != "ERROR-ACTIVE":
        print("  not ERROR-ACTIVE: restart can0 (down, bitrate 1000000, up) before trusting this")

    sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
    sock.bind((args.can,))
    print(f"listening {args.listen_s:g} s:")
    ids, _ = listen(sock, args.listen_s)
    show(ids, args.listen_s)

    if any(i in FEEDBACK for i in ids):
        verdict = "on and streaming feedback"
    elif any(i in LEADER for i in ids):
        verdict = "on, but set as a leader (teaching input) arm, so it gives no feedback"
    elif not args.query:
        verdict = "silent; rerun with --query, since a powered arm can be silent too"
    else:
        tx_before = can_stats(args.can)["tx"]
        sock.send(struct.pack(FRAME, FIRMWARE, 8, bytes([0x01] + [0] * 7)))
        ids, firmware = listen(sock, 1.0)
        acked = can_stats(args.can)["tx"] > tx_before
        print(f"after the 0x4AF query ({'acknowledged' if acked else 'NOT acknowledged'}):")
        show(ids)
        text = firmware.replace(b"\0", b" ").decode("ascii", "replace")
        if "S-V" in text:
            print("  firmware:", text[text.index("S-V"):][:8])
        if firmware:
            verdict = ("powered and answering queries but not streaming feedback: "
                       "power-cycle the arm")
        elif acked:
            verdict = "something acknowledged the query but did not answer it"
        else:
            verdict = ("no node acknowledged the query: the arm is unpowered or not wired to "
                       "this adapter; restart can0 so the adapter stops retrying the query")
    print("verdict:", verdict)


if __name__ == "__main__":
    main()
