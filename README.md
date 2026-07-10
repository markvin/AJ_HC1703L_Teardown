# Augentix AJ HC1703L PTZ IPCam Teardown
PTZ IPCam based on SOC Augentix HC1703L teardown

This is a cheap Pan-Tilt IP Camera (sensor SC1346, 1288 (H) x 728 (V), supposedly 1080p) available on Aliexpress, Gearbest and Temu for €5~15. I bought five of them for less than €20 in an attempt to hack them as their low price is due to being locked to paid cloud services.
With limited documentation available on the Augentix SOC, a practical starting point was to attach a 3.3V UART on the [two + one pads](https://github.com/Jalecom/Augentix-HC1703L-PTZ-IPCam-Teardown/blob/main/Pictures/IMG_8248.jpeg) close to the HC1703 where 57'600bps signal is present.
The camera's behaviour appears very similar to the Goke GK7102 Cloud IP Cameras, and many of the hack are effective on the HC1703 as well. See [ant-thomas zsgx1hacks](https://github.com/ant-thomas/zsgx1hacks)

## Debug Scripts and Files

By default, the startup script `/tmp/start.sh` runs a bunch of [commands](https://github.com/Jalecom/Augentix-HC1703L-PTZ-IPCam-Teardown/blob/main/tmp/start.sh) to check and configure the device. Among them, at line 337, it looks for a `debug_cmd.sh` file on the SD card and runs it if present:

```
336 echo "find debug cmd file, wait for cmd running..."
337 /mnt/debug_cmd.sh
``` 

## Files running from SD Card

So, to run your debug scripts, create a file named `debug_cmd.sh` on an SD card. You will then be able to execute your bash commands from it.
Note that the SD card is mounted in `/mnt` and the camera looks for `/mnt/debug_cmd.sh` while `start.sh` is running, before the WiFi drivers are loaded and before the proprietary closed source `p2pcam` binary is executed.
After that, `p2pcam` on some SoC remount the SD card in a different position, e.g. /mnt/mmc01/0/ and anything running from the SD card could prevent the correct working of some p2pcam, giving trouble in movie saving on the SD card itself.

## Security

The security of these devices is terrible.
* DO NOT expose these cameras to the internet.
* Logs in `/tmp/augentix.log`, `/tmp/icam365.log` and `/tmp/libwebrtc.log`.
* By default the camera wants to use some app [iCam365 on Google Play](https://play.google.com/store/apps/details?id=com.tange365.icam365) or [iCam365 on AppStore](https://apps.apple.com/us/app/icam365/id1444978112)
* As soon as my camera is connected to a network it (mainly p2pcam) try to contact:
	- 120.79.14.221 (heartbeat to alisoft, every 60s)
	- ep.tange365.com
	- api.icloseli.com
	- host.tange365.com
	- relay.icloseli.com
	- p2p-002.host.tange365.com
	- p2p-003.host.tange365.com </BR>
	Check the behavior of your one with [a sniffer!](https://github.com/Jalecom/AJ_HC1703L_Teardown/tree/main/sniffer)

**Credentials stored in plaintext on flash:**

The file `/home/devParam.dat` (permanent flash, survives power cycles) stores the WiFi
SSID and password in plaintext at fixed offsets (+0x100 and +0x12c respectively).
Anyone with shell access to the camera can read your WiFi password with a simple `hexdump`.

**Root password hardcoded in the binary:**

The `p2pcam` binary writes `/etc/passwd` on every boot with a hardcoded root password
(`cxlinux`). The password cannot be changed persistently — `p2pcam` overwrites the file
on every reboot. The hash uses DES crypt with salt `"yi"` (confirmed from binary).

**RTSP has no authentication by default:**

The `no_rtsp_auth` field in `defalut.config` defaults to `1`, meaning the RTSP stream
on port 554 requires no username or password. Anyone on the same network can view the
camera feed without credentials.

## Hack Features

* BusyBox v1.36.1 (2025-10-26 10:33:05 CET) - It’s been compiled with most functions included. Not all of them are currently installed, but they can still be called directly. See: `busybox --help`
* BusyBox FTP Server
* dropbear SSH Server: root can login ssh without password
* WebUI PTZ - (http://192.168.200.1:8080/cgi-bin/webui)
* Improved terminal experience


## Installation

Current version works from microSD card and do not require installation.

* Download [the last  hack](https://github.com/Jalecom/AJ_HC1703L_Teardown/blob/main/HC1703L_Hack_v0.4.zip)
* Copy contents of folder ```sdcard``` to the main directory of a vfat/fat32 formatted microSD card
* To connect the camera to your WiFi edit and insert your SSID and PWD in the ```config.txt```
* Insert microSD card into camera and reboot the device
* If no/wrong WiFi credential are given, the camera act as AP at address ```192.168.200.1```
* Enjoy


## ToDo

* ~~TO DO - Wi-Fi configuration without cloud account~~
* ~~TO DO - Blocking cloud hosts~~
* ~~TO DO - Fix on webui ip retrive error~~, ~~LED IR on/off button~~
* ~~TO DO - Try to run in RAM only without affecting the SD~~
* ~~TO DO - If the space is enough, add a permanent version to run even without an SD~~
* ~~TO DO - Read the ip assigned to the camera after the welcome message~~
* TO DO - Will be possible retrive a single current picture from the camera via webui ?


### 2026-01-06
* The camera announces the assigned IP address aloud if [readip.sh](https://github.com/Jalecom/AJ_HC1703L_Teardown/blob/main/SDCARD_v0.4/hack/readip.sh) and [numbers.wav](https://github.com/Jalecom/AJ_HC1703L_Teardown/blob/main/SDCARD_v0.4/numbers.wav) are present. At the end of the boot process, `wifi.sh` runs `/mnt/hack/readip.sh` if it exists. The `readip.sh` script can also be run manually with a numeric argument, in which case the address is spoken immediately, without the 5-second delay. To play the audio file it is used the p2pcam feature on port 8001: `httpclt get "http://127.0.0.1:8001/playaudio?file=/tmp/ip.wav"`

### 2025-12-31 [HC1703L_Hack_v0.4.zip](https://github.com/Jalecom/AJ_HC1703L_Teardown/blob/main/HC1703L_Hack_v0.4.zip)
* Added a Temporary version of the Hack stored in the RAM of the camera. The SD is only required to start.
* Added a Permanent mini version stored in `/bak/hack` - It use busybox telnetd instead dropbear due to space: the minihack is only 300KB and the SD card can be removed.
* Added a simple sniffer to check who the camera is calling.   
* Direct call to ptz_test from webui (pan & tilt movement, thanks to TwoTeeToRoomTwo)
* Open `config.txt` and insert your wifi credentials.


### 2025-08-23 [HC1703L_Hack_v0.3.zip](https://github.com/Jalecom/AJ_HC1703L_Teardown/blob/main/HC1703L_Hack_v0.3.zip)
* Fixed `webui` IR LEDs buttons (error on GPIO port, thanks to Electro-nic)   
* Fixed `webui` oblique direction buttons (thanks to Pawol)
* Added `index.html` redirecting to `cgi-bin/webui` (Pawol)
* Added hidden buttons to check some `p2pcam` function (via ip port 8001) and added White LEDs buttons (via GPIO 12)
* Found some interesting command in ```auto_test.sh``` integrated in the webui. E.g.:</BR> 
  ```cgi_cmd() { httpclt get 'http://127.0.0.1:8001/'$1 }```</BR>
  ```cgi_cmd 'playaudio?file=/tmp/VOICE/alarm.wav' &```</BR>
  ```cgi_cmd 'whitelight?mode=on'```</BR>   
  ```...```</BR>
  

### 2025-05-18 [HC1703L_Hack_v0.2.zip](https://github.com/Jalecom/AJ_HC1703L_Teardown/blob/main/HC1703L_Hack_v0.2.zip)
* `wifi.sh` can connect to your AccessPoint without cloud account, i.e. without the need to expose the camera to the internet or to use the vendor app. Edit the last line of `debug_cmd.sh` with your credentials or call manually the script with SSID PWD from SSH 
* Removed the annoying voice WaitWifiConfig.wav
* `wdk.sh` is a simple Whatch Dog Kicker, requested if you need to kill `p2pcam` and `start.sh`, this is not (yet) used by the hack.
* Added some lines to hosts file to prevent communication with ```host.tange365.com``` et cetera...
* Fixed webui ip retrive error


## Additional info

### End of Startup process

After the [boot process](https://github.com/Jalecom/AJ_HC1703L_Teardown/blob/main/AugentixFWboot_noSDcard.log), the camera retain the `/home` folder even after a powerdown, until the reset button is manually pressed.\
the `/bak` folder is mounted as ReadOnly and retain all the files requested to startup including `start.sh` and `p2pcam.sqfs`.\
the `/tmp` folder is created at every boot and the `start.sh` is copied from `/bak`; the one in `/tmp` is the one executed during the startup process. `/mnt`, `/var`, log and ini files are here.\
the `start.sh` load some drivers, check if a `firmware.bin` or a `debug_cmd.sh` is on the SD card and upgrade or run it, then init the sensor, ptz, voice, wifi, call `rsyscall.hc1703` and finally mount `/bak/p2pcam.sqfs` to run the p2pcam (closed source bineary), wich control all the higher function of the camera and try to connect with the cloud.\
the `debug_cmd.sh` open a web server for PTZ camera control on IP port 8080; add a SSH and a FTP server; overwrite temporary `hosts`, `profile`, `group`, `passwd`, and `shadow` file; connect with your credential to your WiFi and update via NTP the clock.


### Trigger / flag files

Files whose presence activates mechanisms in the firmware. None need to contain data unless noted.

**SD card root (`/mnt/` — checked by `start.sh` before WiFi loads)**

| File | Effect |
|------|--------|
| `debug_cmd.sh` | Executed as root shell script before `p2pcam` starts |
| `firmware.bin` | Firmware upgrade from SD. If `OTA` is also present, camera does not reboot to factory mode after flashing |
| `OTA` | Modifier for `firmware.bin` upgrade — OTA mode, no factory reboot |
| `FSRW` | Triggers `factory_tool.sh` (provisioning) + starts `tees` logging daemon + leaves `/bak` mounted read-write during `p2pcam` |
| `rmid` | Same `factory_tool.sh` trigger as `FSRW`; within that script, deletes `/bak/eye.conf` |

**SD card — processed by `factory_tool.sh` (requires `FSRW` or `rmid` to be present)**

| File pattern | Effect |
|-------------|--------|
| `eyeconf/*.conf` | Installed as `/bak/eye.conf` — only if `/bak/eye.conf` does not already exist |
| `rmid` | Deletes `/bak/eye.conf` |
| `*-hwcfg.ini` | Copied to `/bak/hwcfg.ini` |
| `*-hardinfo.bin` | Copied to `/bak/hardinfo.bin` (GPIO map, board type, sensor) |
| `*-ptz.cfg` | Copied to `/bak/ptz.cfg` |
| `*-custom_init.sh` | Copied to `/bak/custom_init.sh` |
| `*-VOICE.tgz` | Copied to `/bak/VOICE.tgz` (voice prompts) |

**SD card root (`/mnt/mmc01/` — checked by `p2pcam` via `init_sd_card`, binary analysis confirmed)**

> Note: `init_sd_card` mounts the SD temporarily at `/mnt/mmc01` (not `/mnt/mmc01/0/`), reads these files, then unmounts. The normal runtime path is `/mnt/mmc01/0/`.

| File | Effect |
|------|--------|
| `HARDTEST` | Factory QA mode: starts `telnetd`, resets RTC to year 2000, sets ONVIF/P2P flags |
| `FSRW` | Sets `g_fsrw_flag` — same flag as the `start.sh` check |
| `DUMPLOG` | Enables p2pcam's internal P2P debug log. Creates **`/mnt/mmc01/0/<serial>_debug.log`** during p2pcam startup, **only when eye.conf is valid** (32 bytes). With an empty eye.conf the log is redirected to `/tmp/ipc_debug.log` (RAM) and no file appears on the SD. Written during normal boot — does not require p2pcam to exit. **Contains sensitive data (MAC, UUID).** Verified by live test. |
| `cls.conf` | Parsed by `checkDebugWifiConfig()` — debug WiFi/static IP configuration |
| `accesskey.key` | Copied to `/tmp/accesskey.key` — purpose unknown |
| `SPEED_PASS` | **Result marker, not a trigger.** `init_sd_card` only ever removes it (when no SD is detected, the SD is empty, or neither `/home/eye.conf` nor `/bak/eye.conf` exists). Placing it on the SD manually has no observable effect on `init_sd_card`. |

**`/home/` — permanent flash, checked at every boot by `start.sh`**

| File | Effect |
|------|--------|
| `firmware.bin` | Firmware upgrade from flash (same as SD version) |
| `eye.conf` | Moved to `/bak/eye.conf` (replaces whatever was there) |
| `hardinfo.bin` | Moved to `/bak/hardinfo.bin` |
| `hwcfg.ini` | Moved to `/bak/hwcfg.ini` |
| `ptz.cfg` | Moved to `/bak/ptz.cfg` |
| `image.ini` | Moved to `/bak/image.ini` |
| `VOICE.tgz` | Moved to `/bak/VOICE.tgz` |
| `SD_CHECK` | Forces SD health check on next boot (removed automatically after passing). Also created by `init_sd_card` itself if the SD mount fails — so it retries on the next boot. |
| `SD_NOMOUNT` | **Crash guard** managed by `init_sd_card` itself: created at the start of each SD init, removed on success. If present at boot, it means the previous SD init crashed (power loss, etc.) → SD is treated as suspect, mount is blocked, `/tmp/sd_no_mount` is created, and p2pcam reboots. Do not place manually. |
| `TF_RWERROR_TIME` | SD write-error timestamp tracking — removed by `init_sd_card` only when no SD is detected, the SD is empty, or neither `/home/eye.conf` nor `/bak/eye.conf` exists. Persists across normal boots. |
| `TF_RWERROR_FLAG` | SD write-error flag — removed by `init_sd_card` under the same conditions as `TF_RWERROR_TIME`. |
| `rmid` | Processed by `factory_tool.sh`: deletes `/bak/eye.conf` |
| `START_FLAG` | Read at startup by `status_ctrl_thread` to control LED2 state. Cleaned up by factory reset if present without `STOP_FLAG`. Exact lifecycle unknown. |
| `STOP_FLAG` | Read alongside `START_FLAG` at startup: both present → LED2 on. Exact lifecycle unknown. |
| `OFFLINE_REBOOT` | Contains an integer count read by `getDevRebootTimes()`. Tracks how many times the device has rebooted in an offline state. |

**`/bak/eye.conf` — the key state flag**

| State | Effect |
|-------|--------|
| 32 bytes (valid) | `p2pcam` takes P2P cloud path — port 554 closed |
| 0 bytes or absent | `p2pcam` takes SONG TOOL path — port 554 opens |

### Diagnostic files

**`/tmp/` — RAM, lost on reboot**

| File | Written by | Contents |
|------|-----------|----------|
| `augentix.log` | kernel syslogd | Kernel messages, USB/WiFi driver events, network events |
| `closelicamera.log` | Closeli SDK | SDK runtime log: stream state, cloud connection, relay server pings. Ring buffer, max 1000 lines (`CLOSELICAMERA_LOGMAXLINE=1000`) |
| `sd_no_mount` | `init_sd_card` | Created when `/home/SD_NOMOUNT` exists; signals that SD mount was blocked |
| `accesskey.key` | `init_sd_card` | Copied from `/mnt/mmc01/accesskey.key` if present on SD at boot |

**`/tmp/` — trigger files checked at runtime (place before `p2pcam` starts)**

| File | Checked by | Effect |
|------|-----------|--------|
| `forceday` | `icrCtrlThd` thread / `isImageNeedForceToDay()` | Forces ISP to daytime mode every 60 seconds. Without this file the function only applies daytime mode once per hour between 04:00 and 16:59. |

**`/home/` — permanent flash, survives reboots and power cycles**

| File | Written by | Contents |
|------|-----------|----------|
| `reboot.time` | `start.sh` (on p2pcam exit) | Unix timestamp of the last time p2pcam stopped: `[data]\ntime = <unix_ts>` |
| `config.cfg` | Closeli SDK | Cloud credentials JSON: account email, device IDs, cloud token, secret key, relay server IPs. **Contains sensitive data — delete or protect if sharing.** |
| `config.cfg.bak` | Closeli SDK | Backup copy of `config.cfg` |
| `config.xml` | Closeli SDK | Camera settings: timezone, WiFi SSID, resolution, motion sensitivity, night vision, schedules, SDK version. |
| `dst.cfg` | Closeli SDK | DST rules JSON for the configured timezone. |
| `dev.env` | Closeli SDK | Environment flag (`dev_env=pro`). |
| `work.log` | Closeli SDK | Connection history: WiFi connections, API calls, timestamps. Uses MAC address as device identifier. |
| `idx.log` | Closeli SDK | Entry count for `work.log`. |
| `silent_reboot` | `p2pcam` | Created immediately before a watchdog or connectivity-triggered reboot (video/audio stall, 4G failure, no valid IP after retries). Marks that the previous session ended uncleanly. |

**SD card — output files written by `p2pcam`**

| File | Written by | Contents |
|------|-----------|----------|
| `ipc.log.0` | `tees` daemon | Full diagnostic dump: Closeli SDK log, system state snapshots (`ps`, `ifconfig`, `df`, `netstat`, `free`), and p2pcam stdout ("Dump of log" section). Created when `FSRW` is present; written when p2pcam exits (start.sh sends `SIGUSR1` to tees). The `.0` suffix comes from tees log rotation: `-o ipc.log` creates `ipc.log.0` for the first dump, `ipc.log.1` for the next, up to 20 files. **May contain sensitive data (cloud credentials logged by the Closeli SDK).** |
| `<serial>_debug.log` | `p2pcam` (DUMPLOG flag) | p2pcam startup debug log. Only created when eye.conf is valid (32 bytes) — the P2P subsystem must initialise for the file to be written. Filename is the 32-character P2P serial. Contents: ONVIF WS-Discovery Hello (UUID, IP), Closeli SDK version, `set_device_info` (module ID, firmware version, serial, MAC), init callbacks (resolution, rotation, audio, antiflicker), ISP mode. Written early in the boot — complete before the camera is fully operational. **Contains MAC address and UUID.** Delete from SD after use. Verified by live test. |
| `/mnt/mmc01/0/GPSLOG/` | `p2pcam` | Created automatically by p2pcam when GPS logging is active. p2pcam creates the directory if it does not exist, then creates date subdirectories (`YYYY-MM-DD/`) and writes GPS log files named `%02dH%02dM%02dS.log` (e.g. `14H30M05S.log`). Only written when RTC time is valid. |
| `/mnt/mmc01/0/g4log.txt` | `p2pcam` | p2pcam event log. Each entry is prefixed with a `YYYY/MM/DD HH:MM:SS` timestamp. **Only written when `DUMPLOG` is present on the SD at runtime.** |
| `/mnt/mmc01/0/g4errlog.txt` | `p2pcam` | p2pcam error log. Same format as `g4log.txt`. **Only written when `DUMPLOG` is present on the SD at runtime.** |

### RTSP Connection

* rtsp://admin:@192.168.200.1:554 (2304x1296 w/o audio)
* rtsp://admin:@192.168.200.1:554/0/av0 (with audio)
* rtsp://admin:@192.168.200.1:554/0/av1 (low quality 640x368)
* rtsp://admin:@192.168.200.1:8001
* rtsp://admin:@192.168.200.1:8001/0/av0 (with audio)
* rtsp://admin:@192.168.200.1:8001/0/av1 (low quality)

### How port 554 opens — binary analysis

Port 554 and cloud P2P coexist because of two independent mechanisms in `p2pcam`.

**Why port 554 opens (static — always true on stock firmware):**

`load_hardware_config` reads `/bak/defalut.config` at every boot.
Stock firmware ships with `support_onvif=1` in that file.
This sets an internal flag (`g_onvif_enabled`, address `0x5cc0b0`).

`is_rtsp_enabled()` (address `0x2802c`) returns 1 when:
1. `g_onvif_enabled != 0` — ONVIF enabled (always true on stock cameras)
2. `g_dev_config[0x3c4] == 0` — camera has never registered with the AJCloud/Closeli cloud

When both conditions hold, `ctp_server_init` binds TCP port 554.

**Why SONG TOOL path is taken (the eye.conf trick):**

`p2pcam` has two startup paths — P2P (cloud) and SONG TOOL (local).
It takes the P2P path only if eye.conf decodes correctly with the key `"iloveyou"`.
`load_eye_conf` tries `/home/eye.conf` first, then falls back to `/bak/eye.conf`.
The hack leaves `/bak/eye.conf` as a 0-byte file: decode fails → SONG TOOL path taken.
SONG TOOL starts `ctp_server_init`, which is where `is_rtsp_enabled()` is called.

**Why cloud still works:**

P2P cloud credentials are loaded after the path decision — a separate step reads the
device serial and credentials independently of the eye.conf decode result.
Both port 554 and cloud are active simultaneously.

**Summary of the boot sequence:**
```
load_hardware_config  →  support_onvif=1  →  g_onvif_enabled=1
load_eye_conf         →  /bak/eye.conf empty  →  decode fails  →  g_eyeconf_loaded=0
start_p2p_or_songtool →  g_eyeconf_loaded=0  →  SONG TOOL path
ctp_server_init       →  is_rtsp_enabled() returns 1  →  port 554 bound
                      →  P2P cloud connects independently
```

**How an empty eye.conf keeps port 554 open permanently:**

`p2pcam` decides at startup whether to take the P2P (cloud) path or the SONG TOOL (local)
path. The decision depends on whether eye.conf can be decoded successfully (`load_eye_conf`
tries `/home/eye.conf` first, then `/bak/eye.conf`).
`eye.conf` is encrypted with a custom LSB-first DES variant using the key `"iloveyou"`.
An empty file always fails to decode → `p2pcam` always takes the SONG TOOL path →
`ctp_server_init` runs → `is_rtsp_enabled()` returns 1 → port 554 is bound.

The trigger is simply: `touch /home/eye.conf`

`start.sh` then does `mv -f /home/eye.conf /bak/eye.conf`, so `/bak/eye.conf` becomes
and stays 0 bytes across all subsequent boots — `/bak/` is permanent flash.
`p2pcam` finds the empty `/bak/eye.conf` on every boot and the SONG TOOL path is always taken.
Confirmed by binary analysis: `p2pcam` never deletes or modifies `eye.conf` itself.

**Enabling RTSP on a stock camera (port 554 not yet open):**

If the camera has a valid `eye.conf` and port 554 is closed, a single command activates it:

> **Warning — backup eye.conf first.** `touch /home/eye.conf` creates an empty file that
> `start.sh` will move to `/bak/eye.conf` on the next boot, permanently overwriting the
> original 32-byte file. Once overwritten, the P2P serial stored in it is unrecoverable
> from the device. Save it before proceeding:
> ```sh
> python3 tools/gen_eyeconf.py decode /bak/eye.conf
> # note the serial somewhere safe before continuing
> ```

```sh
touch /home/eye.conf && reboot
```
After the reboot `start.sh` moves the empty file to `/bak/eye.conf` and port 554 opens
on every subsequent boot without any further intervention.

**Using cloud P2P and RTSP at the same time:**

Both work simultaneously. To keep the cloud app working while also opening port 554:
1. Register the camera in the vendor app first (AJCloud / Closeli / iCam365)
2. Once the camera appears in the app, run `touch /home/eye.conf && reboot`
3. Port 554 opens and the cloud connection keeps working

This works because the cloud registration token is stored separately in flash and is not
affected by the state of `eye.conf`. `eye.conf` only controls which startup path `p2pcam`
takes, not whether the cloud credentials are valid.

**Recovering a lost eye.conf:**

If `eye.conf` has been emptied and you want to restore P2P-only mode, you need to
regenerate the 32-byte encrypted file from the device's P2P serial number.

> **Warning:** once `eye.conf` is emptied the serial is gone from the device — it is
> not stored in any log file, config file, or physical label. Save it first.

The serial is a 32-character alphanumeric string unique to each unit.
Where to find it:

- **Decode eye.conf via SSH** — while it still has the original 32 bytes:
  ```sh
  python3 tools/gen_eyeconf.py decode /bak/eye.conf
  ```
- **SD card boot log (no SSH needed)** — place a file named `FSRW` at the root of the
  SD card and boot the camera. The firmware starts a logging daemon (`tees`) that
  captures `p2pcam` stdout to `ipc.log.0` on the SD card. The serial appears there as
  `GET EYE SER: <serial>` — but only if `eye.conf` still has the original 32 bytes;
  with an empty `eye.conf` the serial line is absent; instead the log contains `eye id size = 0` followed by `err id`.
  > **Warning:** `FSRW` also triggers `factory_tool.sh`, a factory provisioning script
  > that can overwrite `/bak/hardinfo.bin`, `/bak/ptz.cfg` and `/bak/hwcfg.ini` if
  > files with matching names are present on the SD card. Keep the SD card clean — only
  > the `FSRW` file. Also, `ipc.log.0` contains sensitive data (cloud tokens, config)
  > logged by the Closeli SDK; delete it from the SD after use.
- **Vendor app** — if the camera was previously registered, open YCC365 Plus (or
  AJCloud/Closeli), go to **Device details → Serial number**. This shows the full
  32-character P2P serial even after `eye.conf` has been emptied.

> **Note:** the QR code on the HC1703L label encodes the MAC address, not the P2P
> serial. There is no other copy of the serial on the device.

**Recovering eye.conf once you have the serial:**
```sh
# Generate the 32-byte eye.conf from your serial
python3 tools/gen_eyeconf.py encode <YOUR_SERIAL> -o eye.conf

# Install via SSH (start.sh moves /home/eye.conf to /bak/eye.conf on next boot)
cat eye.conf | ssh root@<CAMERA_IP> 'cat > /home/eye.conf'
```
Restoring a valid eye.conf disables port 554 and returns the camera to P2P-only mode.


## Device Details

### Software Versions
```
$ uname -a
Linux localhost 3.18.31 #13 Wed Feb 28 01:51:17 UTC 2024 armv7l GNU/Linux

$ busybox # this is the one in the camera firmware, the hack use BusyBox v1.36.1
BusyBox v1.33.0 (2023-02-08 19:01:00 CST) multi-call binary.

Currently defined functions:
        [, [[, arch, arp, arping, ash, awk, cat, chmod, chown, clear, cp, date, dd, devmem, df, dmesg, dnsdomainname,
        echo, env, false, find, flash_eraseall, flashcp, free, getty, grep, halt, head, hostname, i2ctransfer, id,
        ifconfig, ifdown, ifup, init, insmod, kill, killall, klogd, linux32, linux64, linuxrc, ln, logger, login,
        logread, ls, lsmod, lsof, md5sum, mdev, mkdir, mkdosfs, mknod, more, mount, mv, netstat, nologin, nuke, passwd,
        ping, ping6, pipe_progress, poweroff, printenv, ps, pwd, reboot, resume, rm, rmmod, route, run-init, sed, seq,
        setpriv, sh, sleep, sort, start-stop-daemon, stty, sync, sysctl, syslogd, tail, tar, telnetd, top, touch, tr,
        true, ts, tty, udhcpc, udhcpd, uevent, umount, uname, unlzma, uptime, usleep, vi, which, xargs
```

### Hardware info
```
$ cat /bak/hardinfo.bin
<?xml version="1.0" encoding="UTF-8"?>
<DeviceInfo version="1.0">
<DeviceClass>0</DeviceClass>
<OemCode>0</OemCode>
<BoardType>2900</BoardType>
<FirmwareIdent>aj_ipc_hc2_001</FirmwareIdent>
<Manufacturer>AJ</Manufacturer>
<Model>HC1703L</Model>
<WifiChip>RTL8188</WifiChip>
<SensorPosition>1</SensorPosition>
<SupportPtz>1</SupportPtz>
<PtzMcu>0</PtzMcu>
<GPIO>
<BoardReset>6_0x00000000_0_0</BoardReset>
<SpeakerCtrl>64_0x00000000_0_0</SpeakerCtrl>
<IrFeedback>0</IrFeedback>
<BlueLed>-1</BlueLed>
<RedLed>-1</RedLed>
<IrCtrl>77_0x00000000_0_1</IrCtrl>
<IrCut1B>80_0x00000000_0_1</IrCut1B>
<IrCut2B>79_0x00000000_0_1</IrCut2B>
<ALarmLight>10_0x00000000_0_1</ALarmLight>
<WhiteLight>12_0x00000000_0_1</WhiteLight>
<CallKey>17_0x00000000_0_0</CallKey>
<SmokeAlarm>17_0x00000000_0_0</SmokeAlarm>
<WifiCtrl>-1</WifiCtrl>
</GPIO>
```

### Open ports
```
$ nmap -p- 192.168.200.1
Nmap scan report for 192.168.200.1
Host is up (0.063s latency).
Not shown: 65524 closed ports
PORT      STATE    SERVICE
21/tcp    open     ftp			# open by hack
22/tcp    open     ssh			# open by hack
53/tcp    open     domain
80/tcp    open     http
554/tcp   open     rtsp
6670/tcp  open     irc
8001/tcp  open     vcom-tunnel
8080/tcp  open     http-proxy	# open by hack
9000/tcp  filtered cslistener
9010/tcp  filtered sdr
20202/tcp open     ipdtp-port

Nmap done: 1 IP address (1 host up) scanned in 66.17 seconds
```

### Processor
```
$ cat /proc/cpuinfo
processor       : 0
model name      : ARMv7 Processor rev 5 (v7l)
BogoMIPS        : 20160.00
Features        : half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 lpae evtstrm
CPU implementer : 0x41
CPU architecture: 7
CPU variant     : 0x0
CPU part        : 0xc07
CPU revision    : 5

Hardware        : Augentix HC1703_1723_1753_1783s family
Revision        : 0000
Serial          : 0000000000000000
$ 
```

### Memory
```
$ cat /proc/meminfo
MemTotal:          61968 kB
MemFree:            9464 kB
MemAvailable:      18188 kB
Buffers:            2324 kB
Cached:             9908 kB
SwapCached:            0 kB
Active:             8840 kB
Inactive:           8064 kB
Active(anon):       4852 kB
Inactive(anon):     1064 kB
Active(file):       3988 kB
Inactive(file):     7000 kB
Unevictable:          24 kB
Mlocked:              24 kB
SwapTotal:             0 kB
SwapFree:              0 kB
Dirty:                 0 kB
Writeback:             0 kB
AnonPages:          4720 kB
Mapped:             6432 kB
Shmem:              1244 kB
Slab:               4428 kB
SReclaimable:        428 kB
SUnreclaim:         4000 kB
KernelStack:         800 kB
PageTables:          272 kB
NFS_Unstable:          0 kB
Bounce:                0 kB
WritebackTmp:          0 kB
CommitLimit:       30984 kB
Committed_AS:      22336 kB
VmallocTotal:     958464 kB
VmallocUsed:        9272 kB
VmallocChunk:     499700 kB
```

### /etc/passwd
(user/pass -> ```root/cxlinux```)
```
$ cat /etc/passwd
root:yi.LoBvyUCv0k:0:0:root:/root/:/bin/sh
```
The algorithm used to encode the password is DES (Data Encryption Standard), a symmetric encryption algorithm commonly used in old Unix/Linux systems to protect passwords, wich is now cosidered obsolete as can be cracked within few hours. This type of hash generated with DES crypt can store only up to 8 characters of a password, however the algorithm uses a 2-character salt (which in this case is "yi"), and the rest of the 11-character hash is the encrypted part derived from the password "cxlinux" itself.


