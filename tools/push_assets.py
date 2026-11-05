#!/usr/bin/env python3
"""
MaaHSR 资源热更新一键推送工具 (0.5 秒免重装 APK 更新 Pipeline 与模板截图)
用法:
  python tools/push_assets.py
推送后在手机 MaaHSR 点击「快捷选项 -> 重新加载项目」或「设置 -> 项目资源 -> 热更新本地资源包」即可立即生效！
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
REMOTE_BASE = "/sdcard/Android/data/com.aliothmoon.maafw.maahsr/files"
REMOTE_PI = f"{REMOTE_BASE}/pi"


def find_adb() -> str:
    adb = shutil.which("adb")
    if adb:
        return adb
    sdk_adb = Path(os.environ.get("LOCALAPPDATA", "")) / "Android/Sdk/platform-tools/adb.exe"
    if sdk_adb.is_file():
        return str(sdk_adb)
    raise FileNotFoundError("未找到 adb，请确认 Android SDK platform-tools 已安装")


def run_adb(adb: str, serial: str | None, *args: str) -> subprocess.CompletedProcess:
    cmd = [adb]
    if serial:
        cmd.extend(["-s", serial])
    cmd.extend(args)
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def push_assets(serial: str | None = None) -> None:
    adb = find_adb()
    # 同时构建一份 resource_update.zip 放入手机 files/ 目录，方便点击「热更新本地资源包」
    from build_resource_pack import build_resource_pack
    zip_path = build_resource_pack(include_ocr=False)

    run_adb(adb, serial, "shell", f"mkdir -p {REMOTE_PI}/resource/pipeline {REMOTE_PI}/resource/image {REMOTE_PI}/locales")
    run_adb(adb, serial, "push", str(zip_path), f"{REMOTE_BASE}/resource_update.zip")

    items = [
        ("interface.json", f"{REMOTE_PI}/interface.json"),
        ("locales", f"{REMOTE_PI}/"),
        ("resource/default_pipeline.json", f"{REMOTE_PI}/resource/default_pipeline.json"),
        ("resource/pipeline", f"{REMOTE_PI}/resource/"),
        ("resource/image", f"{REMOTE_PI}/resource/"),
        ("resource_bilibili", f"{REMOTE_PI}/"),
    ]
    for rel_src, remote_dst in items:
        local_src = ASSETS_DIR / rel_src
        if local_src.exists():
            run_adb(adb, serial, "push", str(local_src), remote_dst)
            print(f"  -> 已同步: {rel_src}")

    print("\n[OK] 资源热更新已推送至手机！")
    print("     在手机 MaaHSR 中点击「快捷选项 -> 重新加载项目」或「设置 -> 热更新本地资源包」即可立即生效。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="一键热更新推送 MaaHSR 资源到手机")
    parser.add_argument("-s", "--serial", default=None, help="指定 ADB 设备序列号")
    args = parser.parse_args()
    try:
        push_assets(args.serial)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
