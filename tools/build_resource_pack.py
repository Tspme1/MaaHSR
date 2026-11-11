#!/usr/bin/env python3
"""
构建 MaaHSR 轻量级资源热更新包 (MaaHSR-resource-<version>.zip)
参考 MAA 的「APP 本体 + 资源包分体更新」架构：
- 仅打包 interface.json、locales/、resource/pipeline/、resource/image/、resource/default_pipeline.json、resource_bilibili/
- 自动排除体积庞大的 resource/model/ocr/ (18MB OCR 模型随 APP 本体内置，热更新时自动保留)
- 生成的压缩包仅几十 KB，既可上传至 GitHub Release 供 APP 在线秒级热更，也可推送到手机本地热更。
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
DIST_DIR = ROOT_DIR / "dist"
RELEASE_DIR = ROOT_DIR / "release"


def build_resource_pack(version: str = None, include_ocr: bool = False) -> Path:
    interface_path = ASSETS_DIR / "interface.json"
    if not interface_path.is_file():
        raise FileNotFoundError(f"未找到 {interface_path}")

    meta = json.loads(interface_path.read_text(encoding="utf-8"))
    if version:
        meta["version"] = version
        meta["title"] = f"MaaHSR {version}"
        interface_path.write_text(json.dumps(meta, ensure_ascii=False, indent=4), encoding="utf-8")
        print(f"[+] 已同步 interface.json 版本号为: {version}")
    else:
        version = meta.get("version", "v0.0.2")

    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    out_zip = RELEASE_DIR / f"MaaHSR-resource-{version}.zip"

    count = 0
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for file_path in sorted(ASSETS_DIR.rglob("*")):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(ASSETS_DIR).as_posix()
            if not include_ocr and rel.startswith("resource/model/"):
                continue
            if rel.startswith("resource/image/captures/"):
                continue
            zf.write(file_path, arcname=rel)
            count += 1

    import shutil
    dist_zip = DIST_DIR / f"MaaHSR-resource-{version}.zip"
    shutil.copy2(out_zip, dist_zip)

    sha256_hex = hashlib.sha256(out_zip.read_bytes()).hexdigest()
    size_kb = out_zip.stat().st_size / 1024.0
    print(f"[OK] 资源热更新包构建完成: {out_zip}")
    print(f"     同时同步镜像至: {dist_zip}")
    print(f"     包含文件数: {count} (已排除 18MB OCR 模型: {not include_ocr})")
    print(f"     包体大小  : {size_kb:.1f} KB")
    print(f"     SHA-256   : sha256:{sha256_hex}")
    return out_zip


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="构建 MaaHSR 轻量资源热更新包")
    parser.add_argument("--version", type=str, default=None, help="指定资源包版本号（例如 v0.3.0）")
    parser.add_argument("--include-ocr", action="store_true", help="是否包含 OCR 模型目录")
    args = parser.parse_args()
    build_resource_pack(version=args.version, include_ocr=args.include_ocr)
