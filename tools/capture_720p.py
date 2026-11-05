#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC 端一键从 Android 真机的 MaaHSR (1280x720 虚拟屏) 拉取/抓取标准 720P 截图工具。

支持两种无缝取图方式：
方式 A（推荐，100% 原始帧缓冲无损图）：
  在手机 MaaHSR 界面点击底部『⋮ 快捷操作』 -> 『📷 截图』，
  然后在电脑运行 `python tools/capture_720p.py --sync` 即可将手机截取的所有 720P 截图一键拉取到电脑！

方式 B（PC 端直接实时抓图）：
  运行 `python tools/capture_720p.py <场景名>`，脚本自动查找 1280x720 虚拟屏或最新缓存帧并拉取到电脑。
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = PROJECT_ROOT / "screenshots_raw"
APP_PKG = "com.aliothmoon.maafw.maahsr"
REMOTE_MANUAL_DIR = f"/sdcard/Android/data/{APP_PKG}/files/log/manual"
REMOTE_FOCUS_DIR = f"/sdcard/Android/data/{APP_PKG}/files/log/focus"


def find_adb() -> str:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    sdk_adb = Path(local_app_data) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
    if sdk_adb.exists():
        return str(sdk_adb)
    return "adb"


def sync_manual_screenshots(adb: str) -> int:
    """从手机 /sdcard/Android/data/com.aliothmoon.maafw.maahsr/files/log/manual 拉取全部截图"""
    DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        [adb, "shell", f"ls -1 {REMOTE_MANUAL_DIR} 2>/dev/null"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    files = [line.strip() for line in res.stdout.splitlines() if line.strip().endswith(".png")]
    count = 0
    for fname in files:
        local_path = DEFAULT_OUT_DIR / fname
        if not local_path.exists():
            subprocess.run([adb, "pull", f"{REMOTE_MANUAL_DIR}/{fname}", str(local_path)], check=False)
            if local_path.exists():
                print(f"[PULLED] {local_path}")
                count += 1
    return count


def pull_latest_from_dir(adb: str, remote_dir: str, out_path: Path) -> bool:
    res = subprocess.run(
        [adb, "shell", f"ls -1t {remote_dir} 2>/dev/null"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    files = [line.strip() for line in res.stdout.splitlines() if line.strip().endswith(".png")]
    if not files:
        return False
    latest = files[0]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([adb, "pull", f"{remote_dir}/{latest}", str(out_path)], check=False)
    return out_path.exists() and out_path.stat().st_size > 100


def get_virtual_display_id(adb: str) -> str | None:
    res = subprocess.run(
        [adb, "shell", "dumpsys", "display"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if res.returncode != 0:
        return None

    logical_blocks = re.split(r"(?=Display Id=\d+|mDisplayId=\d+)", res.stdout)
    candidates = []
    for block in logical_blocks:
        m_id = re.search(r"(?:Display Id|mDisplayId)=(\d+)", block)
        if not m_id:
            continue
        disp_id = m_id.group(1)
        if disp_id == "0":
            continue
        if "1280" in block and "720" in block:
            candidates.append(disp_id)
    return candidates[-1] if candidates else None


def capture_via_screencap(adb: str, display_id: str, out_path: Path) -> bool:
    cmd = [adb, "exec-out", "screencap", "-d", str(display_id), "-p"]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0 or len(res.stdout) < 100 or not res.stdout.startswith(b"\x89PNG"):
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(res.stdout)
    return True


def main():
    parser = argparse.ArgumentParser(description="从真机 MaaHSR 1280x720 虚拟屏拉取/抓取标准 720P 截图")
    parser.add_argument("name", nargs="?", default="screen", help="截图场景名称（如 login, main_world, phone_menu, guide_daily）")
    parser.add_argument("--sync", "-s", action="store_true", help="同步手机端点击『快捷操作 -> 截图』保存的所有 720P 截图")
    args = parser.parse_args()

    adb = find_adb()

    if args.sync:
        pulled = sync_manual_screenshots(adb)
        print(f"[DONE] 新增同步 {pulled} 张 720P 虚拟屏截图至 {DEFAULT_OUT_DIR}")
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = DEFAULT_OUT_DIR / f"{args.name}_{timestamp}.png"

    # 1. 先同步手机端手动点的截图
    pulled = sync_manual_screenshots(adb)
    if pulled > 0:
        print(f"[INFO] 已自动同步 {pulled} 张手机端手动截取的 720P 截图。")

    # 2. 尝试通过 VirtualDisplay ID 实时 screencap
    disp_id = get_virtual_display_id(adb)
    if disp_id and capture_via_screencap(adb, disp_id, out_file):
        print(f"[SUCCESS] 已通过虚拟屏 (ID={disp_id}) 抓取 720P 截图: {out_file}")
        return

    # 3. 尝试从 MaaFwApp 的 manual 或 focus 帧缓存拉取最新一帧
    if pull_latest_from_dir(adb, REMOTE_MANUAL_DIR, out_file):
        print(f"[SUCCESS] 已拉取 MaaHSR 最新手动虚拟屏截图至: {out_file}")
        return
    if pull_latest_from_dir(adb, REMOTE_FOCUS_DIR, out_file):
        print(f"[SUCCESS] 已拉取 MaaHSR 最新运行缓存帧至: {out_file}")
        return

    print("[HINT] 暂未抓取到虚拟屏画面。请在手机 MaaHSR 中点击『开始』启动虚拟屏后，点击底部『⋮ 快捷操作 -> 📷 截图』，再运行本脚本！")


if __name__ == "__main__":
    main()
