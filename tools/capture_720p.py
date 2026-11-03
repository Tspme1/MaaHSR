#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC 端一键从 Android 真机的 MaaFwApp (1280x720 虚拟屏) 抓取标准 720P 截图工具。

工作原理：
1. 自动通过 `adb shell dumpsys display` 查找名为 MaaFw / 分辨率为 1280x720 的 VirtualDisplay 的 displayId（或 uniqueId）。
2. 调用 `adb exec-out screencap -d <display_id> -p` 直接从该虚拟屏抓取无损 1280x720 PNG 图像。
3. 保存至 `assets/resource/image/captures/<name>_<timestamp>.png`，可直接用于裁剪模板与标注 ROI！

用法：
    python tools/capture_720p.py main_world
    python tools/capture_720p.py phone_menu
    python tools/capture_720p.py guide_daily
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = PROJECT_ROOT / "assets" / "resource" / "image" / "captures"


def find_adb() -> str:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    sdk_adb = Path(local_app_data) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
    if sdk_adb.exists():
        return str(sdk_adb)
    return "adb"


def get_virtual_display_id(adb: str) -> str | None:
    """从 dumpsys display 或 SurfaceFlinger 中查找 1280x720 虚拟屏的 displayId / uniqueId"""
    res = subprocess.run(
        [adb, "shell", "dumpsys", "display"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if res.returncode != 0:
        print(f"[ERROR] adb shell dumpsys display 失败:\n{res.stderr}")
        sys.exit(1)

    text = res.stdout
    # 优先从 DisplayDeviceInfo 或 LogicalDisplay 查找 1280 x 720 的虚拟屏 (VIRTUAL)
    # Android 11+ screencap -d 支持 displayId (如 2, 3...) 或 uniqueId (处理 virtual:... )
    # 先解析 LogicalDisplay: mDisplayId=2 ... 1280 x 720
    logical_blocks = re.split(r"(?=Display Id=\d+|mDisplayId=\d+)", text)
    candidates = []
    for block in logical_blocks:
        m_id = re.search(r"(?:Display Id|mDisplayId)=(\d+)", block)
        if not m_id:
            continue
        disp_id = m_id.group(1)
        if disp_id == "0":
            continue  # 跳过主物理屏幕 0
        if "1280" in block and "720" in block:
            candidates.append(disp_id)

    if candidates:
        return candidates[-1]

    # 备选：检查 dumpsys SurfaceFlinger --display-id
    res_sf = subprocess.run(
        [adb, "shell", "dumpsys", "SurfaceFlinger", "--display-id"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    for line in res_sf.stdout.splitlines():
        m = re.search(r"Display (\d+)\s+\(.*Virtual.*", line, re.IGNORECASE)
        if m:
            return m.group(1)

    return None


def capture_screen(adb: str, display_id: str | None, out_path: Path) -> bool:
    cmd = [adb, "exec-out", "screencap", "-p"]
    if display_id is not None:
        cmd = [adb, "exec-out", "screencap", "-d", str(display_id), "-p"]

    print(f"[INFO] 正在执行: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0 or len(res.stdout) < 100 or not res.stdout.startswith(b"\x89PNG"):
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(res.stdout)
    return True


def main():
    parser = argparse.ArgumentParser(description="从真机 1280x720 虚拟屏一键抓取标准 720P PNG 截图")
    parser.add_argument("name", nargs="?", default="screen", help="截图场景名称（如 login, main_world, phone_menu, guide_daily）")
    parser.add_argument("--display-id", "-d", help="手动指定虚拟屏 displayId")
    args = parser.parse_args()

    adb = find_adb()
    disp_id = args.display_id or get_virtual_display_id(adb)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = DEFAULT_OUT_DIR / f"{args.name}_{timestamp}.png"

    if disp_id:
        print(f"[FOUND] 检测到 1280x720 虚拟屏 Display ID: {disp_id}")
        if capture_screen(adb, disp_id, out_file):
            print(f"[SUCCESS] 已保存虚拟屏 720P 截图至: {out_file}")
            return
        print(f"[WARN] 使用 Display ID {disp_id} 截图失败，尝试检查 MaaFwApp 调试目录...")
    else:
        print("[WARN] 未检测到活动的 1280x720 虚拟屏（请确认手机上 MaaHSR 已点击『开始』并正在运行虚拟屏任务）。")
        print("[INFO] 正在尝试抓取默认屏幕作为回退...")
        if capture_screen(adb, None, out_file):
            print(f"[FALLBACK] 已保存主屏幕截图至: {out_file}（注意：这是主屏幕而非 720P 虚拟屏）")
            return

    sys.exit(1)


if __name__ == "__main__":
    main()
