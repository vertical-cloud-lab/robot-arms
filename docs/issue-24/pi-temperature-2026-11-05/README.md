# Table Pi temperatures while streaming (2026-11-05)

Asked in [PR #40](https://github.com/vertical-cloud-lab/robot-arms/pull/40): how hot the table Pis
run, whether that is safe long term, and whether face blurring is what heats them. All three Pis
were sampled at the same time, once a second, from 18:53:52 to 18:54:22 UTC, while all four
streams ran.

![SoC temperature and CPU use of the three table Pis, 18:53:52 UTC](pi_thermals.png)

| | eufi (back cam) | mpzy (front cam) | 76zj (gripper cams) |
| --- | --- | --- | --- |
| SoC | 54.5–56.8 °C, mean 55.6 | 56.8–59.5 °C, mean 58.1 | 58.4–61.2 °C, mean 59.8 |
| PMIC | 58.0 °C | 59.8 °C | 60.6 °C |
| ARM clock | 2400 MHz (the maximum) throughout | 2400 MHz throughout | 2400 MHz throughout |
| `get_throttled` | `0x0` since boot (2026-10-30 02:12 UTC) | `0x0` since boot (2026-11-03 01:04 UTC) | `0x0` since boot (2026-11-05 18:51 UTC) |
| Fan (Active Cooler) | 30–50 % PWM, 3360–5490 rpm | 30 %, about 3180 rpm | 50 %, about 5270 rpm |
| 5 V input (PMIC) | 5.09–5.18 V | 5.08–5.10 V | 5.06–5.15 V |
| Face blurring (`device.py`), cores | 1.84 | 1.77 | 3.56 (1.78 per stream) |
| Streaming: capture (`rpicam-vid`) + encode and send (`ffmpeg`), cores | 0.02 + 0.13 = 0.15 | 0.01 + 0.10 = 0.11 | 0.04 + 0.22 = 0.26 |
| Everything else, cores | 0.06 | 0.02 | 0.04 |
| Frames sent per second (last 2-minute log line) | 4.8 | 5.0 | 3.3 (wide), 2.9 (HQ) |
| Stream unit's average CPU since it started | 1.87 cores over 19.7 h | 1.87 cores over 19.75 h | (started 3 min before) |

`get_throttled` `0x0` means no throttling, frequency cap or under-voltage at any time since boot.
Each Pi's blurring runs on two threads per stream, and each stream is capped at 2 cores
(`CPUQuota=200%`), so blurring uses all it is allowed. Over the 16 hours before, the streams'
2-minute log lines show 4.9–5.0 frames a second all night on mpzy, and on eufi too except from
05:42 to 06:37 UTC, when its `ffmpeg` kept losing the connection to YouTube.

**76zj rebooted just before this.** It dropped off Tailscale at 18:41:18 UTC and booted again at
18:51:05 UTC; nothing in this run restarted it. Its journal only covers the current boot, so it
doesn't say why. Both gripper streams then started new broadcasts (`2sLWW-N15BE` wide,
`jRS2IjKwXCw` HQ), since they had been down for more than 10 minutes. Its fan had already
stepped to 50 % and the SoC was at the same 60 °C that
[#61's notes](https://github.com/vertical-cloud-lab/robot-arms/blob/d5ba8f7/livestream/README.md#gripper-cameras-two-streams-on-76zj)
measured on it the night before. An earlier sample of eufi and mpzy alone, at 18:43:03 UTC
(commit `dc92172`), gave 56.2–59.5 °C and 55.1–57.3 °C with the same CPU split.

**Limits from Raspberry Pi's [documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#frequency-management-and-thermal-control):**
the Arm cores are throttled progressively from 80 °C, and the Arm cores and GPU at 85 °C. The Pi 5
fan turns on at 50 °C (30 %) and steps up at 60 °C (50 %), 67.5 °C (70 %) and 75 °C (100 %), with
5 °C of hysteresis on the way down. The kernel's trip points on all three Pis match those, and
its critical trip (shutdown) is 110 °C.

**Files.** `eufi.json`, `mpzy.json` and `76zj.json` are what
[`pi_thermal_sample.py`](../../../scripts/pi_thermal_sample.py) printed on each Pi: the 31 samples,
CPU time per process and per thread of the stream units, systemd's CPU total per unit, the streams'
2-minute `fps out` log lines for the 16 hours before (76zj's journal only covers its current boot),
and kernel messages about voltage or temperature since boot (only the thermal governor registering
at boot, on mpzy and 76zj). [`pi_thermal_plot.py`](../../../scripts/pi_thermal_plot.py) made
`summary.json` and the figure. To repeat it, read-only and with no restart, run the three at once
so they share a window:

```bash
ssh "$ARM_PI_USERNAME@$ARM_PI_HOSTNAME" 'python3 - --seconds 30' < scripts/pi_thermal_sample.py > eufi.json &
ssh "$CAM2_PI_USERNAME@$CAM2_PI_HOSTNAME" 'python3 - --seconds 30' < scripts/pi_thermal_sample.py > mpzy.json &
ssh "$CAM_PI_USERNAME@$CAM_PI_HOSTNAME" 'python3 - --seconds 30' < scripts/pi_thermal_sample.py > 76zj.json &
wait
python scripts/pi_thermal_plot.py .
```

The sampler needs no sudo, never opens a camera and prints no hostname or command line.
