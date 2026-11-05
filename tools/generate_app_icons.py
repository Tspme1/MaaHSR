#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from collections import deque
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

SOURCE_IMAGE = Path(r"C:\Users\tangshupeng\.gemini\antigravity\brain\aa09cb8d-01cd-4d2a-81b9-c83553344dc3\.user_uploaded\media_1793715542023_0b897f68.jpg")
ROOT_DIR = Path(r"d:\anti_work\MaaHSR")
RES_DIR = ROOT_DIR / "Android" / "MaaFwApp" / "app" / "src" / "main" / "res"
LOCALES_ICON = ROOT_DIR / "assets" / "locales" / "icon.png"

def remove_black_background(img_path):
    print(f"[*] 加载源图: {img_path}")
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size
    arr = np.array(img)
    rgb = arr[:, :, :3]

    # 判定纯黑/近黑背景 (R < 25 and G < 25 and B < 25)
    is_black = (rgb[:, :, 0] < 25) & (rgb[:, :, 1] < 25) & (rgb[:, :, 2] < 25)

    # 从 4 边缘的近黑像素开始 BFS 泛洪填充
    visited = np.zeros((h, w), dtype=bool)
    queue = deque()

    def add_seed(y, x):
        if 0 <= y < h and 0 <= x < w and is_black[y, x] and not visited[y, x]:
            visited[y, x] = True
            queue.append((y, x))

    for x in range(w):
        add_seed(0, x)
        add_seed(h - 1, x)
    for y in range(h):
        add_seed(y, 0)
        add_seed(y, w - 1)

    # 顶部挂绳内部封闭黑色小三角种子点 (对应 512x512 的 (280, 60)，在 1024x1024 下为 (90, 580) 等)
    for sy, sx in [(90, 580), (100, 560), (60, 280), (120, 560)]:
        add_seed(sy, sx)

    while queue:
        y, x = queue.popleft()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx] and is_black[ny, nx]:
                visited[ny, nx] = True
                queue.append((ny, nx))

    # 前景掩码与抗锯齿柔边
    fg_mask = (~visited).astype(np.uint8) * 255
    mask_img = Image.fromarray(fg_mask, mode="L")
    mask_smooth = mask_img.filter(ImageFilter.GaussianBlur(radius=0.8))

    arr[:, :, 3] = np.array(mask_smooth)
    clean_img = Image.fromarray(arr, mode="RGBA")
    print(f"  + 背景抠除完成，非透明像素比例: {np.count_nonzero(~visited) / (w * h) * 100:.2f}%")
    return clean_img

def apply_safe_margin(img, scale_ratio=0.82):
    """
    将非透明区域裁剪并缩放到画布宽高的 scale_ratio (默认 82%)，四周留出约 9% 的透明安全边距居中放置。
    """
    bbox = img.getbbox()
    if not bbox:
        return img
    cropped = img.crop(bbox)
    cw, ch = cropped.size
    w, h = img.size

    target_w = int(round(w * scale_ratio))
    target_h = int(round(h * scale_ratio))

    ratio = min(target_w / cw, target_h / ch)
    nw = int(round(cw * ratio))
    nh = int(round(ch * ratio))
    resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    offset_x = (w - nw) // 2
    offset_y = (h - nh) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)
    print(f"  + 已应用安全边距: 主体尺寸 {cw}x{ch} -> 缩放至 {nw}x{nh} (画布 {w}x{h}, 占比 {scale_ratio*100:.1f}%)")
    return canvas

def make_round_icon(img):
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, w - 1, h - 1), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.5))

    out = img.copy()
    curr_a = np.array(out.split()[3]).astype(float)
    circ_a = np.array(mask).astype(float)
    comb = np.clip(curr_a * circ_a / 255.0, 0, 255).astype(np.uint8)
    out.putalpha(Image.fromarray(comb))
    return out

def main():
    raw_img = remove_black_background(SOURCE_IMAGE)
    base_img = apply_safe_margin(raw_img, scale_ratio=0.82)

    # 1. 保存 512x512 RGBA PNG 到 assets/locales/icon.png
    LOCALES_ICON.parent.mkdir(parents=True, exist_ok=True)
    icon_512 = base_img.resize((512, 512), Image.Resampling.LANCZOS)
    icon_512.save(LOCALES_ICON, format="PNG")
    print(f"[OK] 已保存 512x512 应用图标: {LOCALES_ICON}")

    # 同步 ic_maahsr_launcher_v52.png
    v52_launcher = RES_DIR / "mipmap-xxxhdpi" / "ic_maahsr_launcher_v52.png"
    v52_launcher.parent.mkdir(parents=True, exist_ok=True)
    icon_512.save(v52_launcher, format="PNG")
    print(f"[OK] 已保存 512x512 图标: {v52_launcher}")

    profile_launcher = ROOT_DIR / "Android" / "MaaFwApp" / "app" / "build" / "generated" / "profileRes" / "mipmap-xxxhdpi" / "ic_profile_launcher.png"
    profile_launcher.parent.mkdir(parents=True, exist_ok=True)
    icon_512.save(profile_launcher, format="PNG")
    print(f"[OK] 已同步覆盖 profileRes 图标: {profile_launcher}")

    # 2. 覆盖 res/mipmap-* 下的 webp
    densities = {
        "mipmap-mdpi": (48, 108),
        "mipmap-hdpi": (72, 162),
        "mipmap-xhdpi": (96, 216),
        "mipmap-xxhdpi": (144, 324),
        "mipmap-xxxhdpi": (192, 432),
    }

    for folder, (std_size, fg_size) in densities.items():
        folder_path = RES_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        # ic_launcher.webp (82% 居中，9% 透明安全边距)
        launcher = base_img.resize((std_size, std_size), Image.Resampling.LANCZOS)
        launcher.save(folder_path / "ic_launcher.webp", format="WEBP")

        # ic_launcher_round.webp
        launcher_round = make_round_icon(launcher)
        launcher_round.save(folder_path / "ic_launcher_round.webp", format="WEBP")

        # ic_launcher_foreground.webp (同样保持 82% 居中)
        launcher_fg = base_img.resize((fg_size, fg_size), Image.Resampling.LANCZOS)
        launcher_fg.save(folder_path / "ic_launcher_foreground.webp", format="WEBP")

        print(f"  + 更新 {folder}: launcher={std_size}x{std_size}, fg={fg_size}x{fg_size}")

    # 3. 保存 96x96 RGBA PNG 到 drawable-xxhdpi 与 drawable
    avatar_96 = base_img.resize((96, 96), Image.Resampling.LANCZOS)
    for draw_folder in ["drawable-xxhdpi", "drawable"]:
        p = RES_DIR / draw_folder / "ic_notification_avatar.png"
        p.parent.mkdir(parents=True, exist_ok=True)
        avatar_96.save(p, format="PNG")
        print(f"[OK] 已保存通知头像: {p}")

if __name__ == "__main__":
    main()
