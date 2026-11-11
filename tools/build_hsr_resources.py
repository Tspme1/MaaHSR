#!/usr/bin/env python3
"""
tools/build_hsr_resources.py
自动化生成 MaaHSR 720P 模版切图、日常任务流水线 JSON 以及界面配置。
"""
import json
import os
from pathlib import Path
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "screenshots_raw"
ASSETS_DIR = ROOT_DIR / "assets"
IMAGE_DIR = ASSETS_DIR / "resource" / "image"
PIPELINE_DIR = ASSETS_DIR / "resource" / "pipeline"
LOCALES_DIR = ASSETS_DIR / "locales"

# 1. 模版切图清单 (left, top, right, bottom)
CROPS = [
    ("login_enter.png", "manual_20261103_213127_168.png", (580, 646, 700, 684)),
    ("hud_phone.png", "manual_20261103_213153_191.png", (16, 40, 44, 80)),
    ("hud_guide.png", "manual_20261103_213153_191.png", (988, 22, 1024, 66)),
    ("hud_honor.png", "manual_20261103_213153_191.png", (854, 22, 898, 66)),
    ("phone_close.png", "manual_20261110_211931_037.png", (1216, 22, 1256, 62)),
    ("phone_mail.png", "manual_20261110_211931_037.png", (1215, 210, 1257, 248)),
    ("phone_mail_warm.png", "manual_20261103_213205_023.png", (1215, 210, 1257, 248)),
    ("phone_mail_green.png", "2026.11.10-20.58.14.586_MailOpenPhone.png", (1215, 210, 1257, 248)),
    ("phone_assignments.png", "manual_20261110_211931_037.png", (1082, 272, 1166, 352)),
    ("phone_honor.png", "manual_20261103_213205_023.png", (870, 486, 950, 566)),
    ("phone_guide.png", "manual_20261110_211931_037.png", (762, 596, 834, 674)),
    ("guide_tab_daily.png", "manual_20261103_213226_694.png", (150, 86, 226, 138)),
    ("guide_tab_survival.png", "manual_20261103_213431_834.png", (244, 86, 320, 138)),
    ("assignment_claim.png", "manual_20261103_213247_386.png", (864, 612, 1158, 660)),
    ("mail_claim_all.png", "manual_20261103_213258_728.png", (272, 636, 458, 678)),
    ("honor_tab_reward.png", "manual_20261103_213312_131.png", (18, 92, 74, 152)),
    ("honor_tab_quest.png", "manual_20261103_213318_812.png", (18, 178, 74, 238)),
    ("calyx_challenge.png", "manual_20261103_213459_949.png", (816, 640, 1244, 684)),
    ("team_start_challenge.png", "manual_20261103_213512_106.png", (940, 640, 1212, 684)),
    ("battle_exit.png", "manual_20261103_213633_788.png", (282, 612, 590, 656)),
    ("battle_again.png", "manual_20261103_213633_788.png", (690, 612, 998, 656)),
    ("ornament_start_challenge.png", "manual_20261103_222651_770.png", (876, 636, 1244, 684)),
    ("support_btn_green.png", "manual_20261103_222651_770.png", (520, 570, 644, 604)),
    ("survival_cavern_tab.png", "manual_20261103_222749_789.png", (118, 430, 422, 514)),
    ("survival_stagnant_tab.png", "manual_20261103_222749_789.png", (118, 330, 422, 414)),
    ("support_confirm.png", "manual_20261103_231522_072.png", (944, 640, 1226, 688)),
    ("count_plus.png", "manual_20261103_213459_949.png", (1186, 566, 1240, 600)),
    ("quick_battle_btn.png", "manual_20261103_213459_949.png", (615, 636, 772, 688)),
    ("honor_reward_claim_all.png", "manual_20261104_204804_141.png", (788, 646, 954, 692)),
    ("stage_close_dark.png", "manual_20261104_214625_891.png", (1216, 22, 1256, 62)),
    ("quick_battle_close.png", "manual_20261104_222436_065.png", (316, 566, 615, 613)),
    ("quick_refill_off.png", "manual_20261105_191606_949.png", (1192, 507, 1241, 531)),
]


def crop_templates():
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[*] 开始从 {RAW_DIR} 裁剪模版到 {IMAGE_DIR}...")
    for out_name, src_name, box in CROPS:
        src_path = RAW_DIR / src_name
        if not src_path.is_file():
            print(f"[!] 警告：原图不存在 {src_path}")
            continue
        with Image.open(src_path) as img:
            cropped = img.crop(box)
            out_path = IMAGE_DIR / out_name
            cropped.save(out_path, format="PNG")
            print(f"  + 裁剪完成: {out_name} {box} (尺寸: {cropped.size})")
    print("[OK] 所有模版切图完成！\n")


def build_masked_white_icons():
    import numpy as np

    print(f"[*] 开始生成纯白/半透图标 green_mask 模板...")
    TARGETS = [
        ("phone_mail.png", "phone_mail_mask.png"),
        ("hud_phone.png", "hud_phone_mask.png"),
        ("hud_guide.png", "hud_guide_mask.png"),
        ("hud_honor.png", "hud_honor_mask.png"),
        ("phone_close.png", "phone_close_mask.png"),
        ("stage_close_dark.png", "stage_close_dark_mask.png"),
    ]

    try:
        from scipy.ndimage import maximum_filter
        has_scipy = True
    except ImportError:
        has_scipy = False

    def dilate_stroke_2px(stroke_mask):
        if has_scipy:
            return maximum_filter(maximum_filter(stroke_mask, size=3), size=3)
        padded = np.pad(stroke_mask, 1, mode="edge")
        res1 = np.zeros_like(stroke_mask)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                res1 |= padded[1 + dy : 1 + dy + stroke_mask.shape[0], 1 + dx : 1 + dx + stroke_mask.shape[1]]
        padded2 = np.pad(res1, 1, mode="edge")
        res2 = np.zeros_like(stroke_mask)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                res2 |= padded2[1 + dy : 1 + dy + stroke_mask.shape[0], 1 + dx : 1 + dx + stroke_mask.shape[1]]
        return res2

    for base_name, mask_name in TARGETS:
        src_path = IMAGE_DIR / base_name
        if not src_path.is_file():
            print(f"[!] 警告：源图标不存在 {src_path}")
            continue
        with Image.open(src_path) as img:
            arr = np.array(img.convert("RGB"))

        R = arr[:, :, 0]
        G = arr[:, :, 1]
        B = arr[:, :, 2]
        L = 0.299 * R + 0.587 * G + 0.114 * B
        stroke = L >= 175
        near_stroke = dilate_stroke_2px(stroke)
        border = near_stroke & (~stroke)

        out = np.zeros_like(arr)
        out[:, :] = [0, 255, 0]  # MaaFramework green_mask (pure green ignored)
        v = np.clip(L, 200, 255).astype(np.uint8)
        out[stroke] = np.column_stack([v[stroke], v[stroke], v[stroke]])
        out[border] = [55, 55, 55]

        out_path = IMAGE_DIR / mask_name
        Image.fromarray(out).save(out_path, format="PNG")
        print(f"  + 遮罩生成完成: {mask_name} (高亮笔画: {int(np.sum(stroke))}, 边缘反差轮廓: {int(np.sum(border))})")
    print("[OK] 所有纯白/半透遮罩模板生成完成！\n")


def build_pipelines():
    PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[*] 开始生成流水线 JSON 文件到 {PIPELINE_DIR}...")

    # Startup.json
    startup_pipeline = {
        "StartUp": {
            "desc": "启动崩坏：星穹铁道并进入大世界",
            "action": "StartApp",
            "package": "com.miHoYo.hkrpg",
            "post_delay": 3000,
            "next": [
                "CheckMainWorld",
                "LoginClickEnter",
                "ClaimMonthlyCardPopup",
                "StartupWaitLoading"
            ]
        },
        "LoginClickEnter": {
            "desc": "登录页点击进入游戏",
            "recognition": "OCR",
            "expected": [
                "点击进入",
                "开始游戏",
                "进入游戏"
            ],
            "roi": [
                450,
                520,
                380,
                180
            ],
            "action": "Click",
            "target": [
                640,
                660
            ],
            "post_delay": 3000,
            "next": [
                "CheckMainWorld",
                "ClaimMonthlyCardPopup",
                "LoginClickEnter",
                "StartupWaitLoading"
            ]
        },
        "ClaimMonthlyCardPopup": {
            "desc": "识别并领取列车补给凭证（月卡）",
            "recognition": "OCR",
            "expected": [
                "列车补给凭证",
                "今日补给"
            ],
            "roi": [
                400,
                100,
                480,
                500
            ],
            "action": "Click",
            "target": [
                640,
                640
            ],
            "post_delay": 2000,
            "next": [
                "DismissMonthlyCardReward",
                "CheckMainWorld"
            ]
        },
        "DismissMonthlyCardReward": {
            "desc": "关闭月卡领取获得物品浮层",
            "recognition": "OCR",
            "expected": [
                "点击空白处关闭",
                "获得物品"
            ],
            "roi": [
                400,
                100,
                480,
                580
            ],
            "action": "Click",
            "target": [
                640,
                660
            ],
            "post_delay": 1500,
            "next": [
                "CheckMainWorld",
                "StartupWaitLoading"
            ]
        },
        "StartupWaitLoading": {
            "desc": "等待加载中转",
            "recognition": "DirectHit",
            "action": "DoNothing",
            "post_delay": 2000,
            "next": [
                "CheckMainWorld",
                "LoginClickEnter",
                "ClaimMonthlyCardPopup",
                "CloseTopRightModal",
                "StartupWaitLoading"
            ],
            "timeout": 180000
        },
        "CheckMainWorld": {
            "desc": "识别左上角手机图标确认位于大世界",
            "recognition": "TemplateMatch",
            "template": [
                "hud_phone_mask.png",
                "hud_phone.png"
            ],
            "green_mask": True,
            "roi": [
                5,
                25,
                65,
                70
            ],
            "threshold": 0.65,
            "action": "DoNothing",
            "pre_delay": 0,
            "post_delay": 0,
            "focus": {
                "Node.Recognition.Succeeded": "已进入崩坏：星穹铁道大世界主界面"
            }
        },
        "OpenPhoneMenu": {
            "desc": "打开左上角手机主菜单",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "InPhoneMenuCheck",
                "ClickPhoneIcon"
            ]
        },
        "InPhoneMenuCheck": {
            "desc": "检查是否已在手机菜单",
            "recognition": "OCR",
            "expected": [
                "委托",
                "指南",
                "无名勋礼"
            ],
            "roi": [
                730,
                250,
                460,
                450
            ],
            "action": "DoNothing",
            "pre_delay": 0,
            "post_delay": 0
        },
        "ClickPhoneIcon": {
            "desc": "点击左上角手机图标",
            "recognition": "TemplateMatch",
            "template": [
                "hud_phone_mask.png",
                "hud_phone.png"
            ],
            "green_mask": True,
            "roi": [
                5,
                25,
                65,
                70
            ],
            "threshold": 0.65,
            "action": "Click",
            "target": [
                30,
                60
            ],
            "post_delay": 700
        },
        "CloseTopRightModal": {
            "desc": "点击右上角关闭按钮",
            "recognition": "TemplateMatch",
            "template": [
                "phone_close_mask.png",
                "stage_close_dark_mask.png",
                "phone_close.png",
                "stage_close_dark.png"
            ],
            "green_mask": True,
            "roi": [
                1190,
                5,
                85,
                80
            ],
            "threshold": 0.65,
            "action": "Click",
            "target": [
                1235,
                42
            ],
            "post_delay": 600
        },
        "ReturnToMainWorld": {
            "desc": "退回大世界主界面",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "CheckMainWorld",
                "CloseTopRightModal"
            ]
        }
    }
    (PIPELINE_DIR / "Startup.json").write_text(json.dumps(startup_pipeline, ensure_ascii=False, indent=4), encoding="utf-8")
    print("  + 已生成 Startup.json")

    # Assignments.json
    assignments_pipeline = {
        "Assignments": {
            "desc": "每日委托一键领取与再次派遣",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "AssignmentAlreadyOpen",
                "AssignmentFromPhone",
                "AssignmentOpenPhone",
                "AssignmentReturnAndRetry"
            ]
        },
        "AssignmentOpenPhone": {
            "desc": "在大世界点击左上角手机打开菜单",
            "recognition": "TemplateMatch",
            "template": [
                "hud_phone_mask.png",
                "hud_phone.png"
            ],
            "green_mask": True,
            "roi": [
                5,
                25,
                65,
                70
            ],
            "threshold": 0.65,
            "action": "Click",
            "target": [
                30,
                60
            ],
            "post_delay": 800,
            "next": [
                "AssignmentFromPhone"
            ]
        },
        "AssignmentFromPhone": {
            "desc": "从手机菜单点击【委托】磁贴",
            "recognition": "OCR",
            "expected": [
                "委托"
            ],
            "roi": [
                1050,
                250,
                140,
                120
            ],
            "action": "Click",
            "target": [
                1123,
                310
            ],
            "post_delay": 900,
            "next": [
                "AssignmentAlreadyOpen"
            ]
        },
        "AssignmentAlreadyOpen": {
            "desc": "确认已在委托界面",
            "recognition": "OCR",
            "expected": [
                "委托",
                "进行中的委托",
                "委托奖励"
            ],
            "roi": [
                20,
                10,
                900,
                650
            ],
            "action": "DoNothing",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "AssignmentClickClaimYellow",
                "AssignmentClickOneKeyClaim",
                "AssignmentDoneClose"
            ]
        },
        "AssignmentClickClaimYellow": {
            "desc": "点击右下角金色【领取奖励】按钮",
            "recognition": "TemplateMatch",
            "template": "assignment_claim.png",
            "roi": [
                840,
                590,
                340,
                90
            ],
            "threshold": 0.75,
            "action": "Click",
            "target": [
                1011,
                636
            ],
            "post_delay": 900,
            "focus": {
                "Node.Recognition.Succeeded": "已点击委托【领取奖励】"
            },
            "next": [
                "AssignmentDismissReward",
                "AssignmentDoneClose"
            ]
        },
        "AssignmentClickOneKeyClaim": {
            "desc": "识别并点击一键领取",
            "recognition": "OCR",
            "expected": [
                "一键领取",
                "领取奖励"
            ],
            "roi": [
                350,
                580,
                830,
                110
            ],
            "action": "Click",
            "post_delay": 900,
            "next": [
                "AssignmentRedispatch",
                "AssignmentDismissReward",
                "AssignmentDoneClose"
            ]
        },
        "AssignmentRedispatch": {
            "desc": "点击再次派遣",
            "recognition": "OCR",
            "expected": [
                "再次派遣"
            ],
            "roi": [
                400,
                580,
                600,
                110
            ],
            "action": "Click",
            "post_delay": 900,
            "next": [
                "AssignmentDismissReward",
                "AssignmentDoneClose"
            ]
        },
        "AssignmentDismissReward": {
            "desc": "关闭委托奖励弹窗",
            "recognition": "OCR",
            "expected": [
                "点击空白处关闭",
                "获得物品"
            ],
            "roi": [
                400,
                100,
                480,
                600
            ],
            "action": "Click",
            "target": [
                640,
                680
            ],
            "post_delay": 600,
            "next": [
                "AssignmentDoneClose"
            ]
        },
        "AssignmentDoneClose": {
            "desc": "关闭委托界面退回手机菜单",
            "action": "Click",
            "target": [
                1235,
                42
            ],
            "post_delay": 600,
            "next": [
                "AssignmentExitPhone",
                "CheckMainWorld"
            ]
        },
        "AssignmentExitPhone": {
            "desc": "关闭手机菜单退回大世界",
            "recognition": "TemplateMatch",
            "template": [
                "phone_close_mask.png",
                "stage_close_dark_mask.png",
                "phone_close.png",
                "stage_close_dark.png"
            ],
            "green_mask": True,
            "roi": [
                1190,
                5,
                85,
                80
            ],
            "threshold": 0.65,
            "action": "Click",
            "target": [
                1235,
                42
            ],
            "post_delay": 600,
            "next": [
                "CheckMainWorld"
            ]
        },
        "AssignmentReturnAndRetry": {
            "desc": "异常时退回重试",
            "action": "Click",
            "target": [
                1235,
                42
            ],
            "post_delay": 600,
            "next": [
                "AssignmentOpenPhone",
                "AssignmentFromPhone"
            ]
        }
    }
    (PIPELINE_DIR / "Assignments.json").write_text(json.dumps(assignments_pipeline, ensure_ascii=False, indent=4), encoding="utf-8")
    print("  + 已生成 Assignments.json")

    # Mail.json
    mail_pipeline = {
        "Mail": {
            "desc": "邮件一键全部领取",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "MailAlreadyOpen",
                "MailFromPhone",
                "MailFromPhoneByAnchor",
                "MailOpenPhone",
                "MailReturnAndRetry"
            ]
        },
        "MailOpenPhone": {
            "desc": "在大世界点击左上角手机打开菜单",
            "recognition": "TemplateMatch",
            "template": [
                "hud_phone_mask.png",
                "hud_phone.png"
            ],
            "green_mask": True,
            "roi": [
                5,
                25,
                65,
                70
            ],
            "threshold": 0.65,
            "action": "Click",
            "target": [
                30,
                60
            ],
            "post_delay": 800,
            "next": [
                "MailFromPhone",
                "MailFromPhoneByAnchor"
            ]
        },
        "MailFromPhone": {
            "desc": "从手机右侧栏点击邮件图标",
            "recognition": "TemplateMatch",
            "template": [
                "phone_mail_mask.png",
                "phone_mail.png",
                "phone_mail_warm.png",
                "phone_mail_green.png"
            ],
            "green_mask": True,
            "roi": [
                1195,
                190,
                80,
                80
            ],
            "threshold": 0.65,
            "action": "Click",
            "target": [
                1236,
                230
            ],
            "post_delay": 900,
            "next": [
                "MailAlreadyOpen"
            ]
        },
        "MailFromPhoneByAnchor": {
            "desc": "当背景变化导致邮箱图标模板未命中时，通过识别手机菜单文字锚点直接点击右侧固定邮箱坐标",
            "recognition": "OCR",
            "expected": [
                "委托",
                "指南",
                "合成",
                "成就",
                "角色",
                "跃迁",
                "商店",
                "好友"
            ],
            "roi": [
                580,
                250,
                620,
                450
            ],
            "action": "Click",
            "target": [
                1236,
                230
            ],
            "post_delay": 900,
            "next": [
                "MailAlreadyOpen"
            ]
        },
        "MailAlreadyOpen": {
            "desc": "确认已在邮箱界面",
            "recognition": "OCR",
            "expected": [
                "邮箱",
                "全部领取",
                "删除已读"
            ],
            "roi": [
                20,
                10,
                500,
                690
            ],
            "action": "DoNothing",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "MailClickClaimAll",
                "MailDoneClose"
            ]
        },
        "MailClickClaimAll": {
            "desc": "点击全部领取",
            "recognition": "OCR",
            "expected": [
                "全部领取"
            ],
            "roi": [
                250,
                620,
                230,
                75
            ],
            "action": "Click",
            "target": [
                365,
                657
            ],
            "post_delay": 900,
            "focus": {
                "Node.Recognition.Succeeded": "已点击邮件【全部领取】"
            },
            "next": [
                "MailDismissReward",
                "MailDoneClose"
            ]
        },
        "MailDismissReward": {
            "desc": "关闭邮件领取获得物品浮层",
            "recognition": "OCR",
            "expected": [
                "点击空白处关闭",
                "获得物品"
            ],
            "roi": [
                400,
                100,
                480,
                600
            ],
            "action": "Click",
            "target": [
                640,
                680
            ],
            "post_delay": 600,
            "next": [
                "MailDoneClose"
            ]
        },
        "MailDoneClose": {
            "desc": "关闭邮箱界面",
            "action": "Click",
            "target": [
                1235,
                42
            ],
            "post_delay": 600,
            "next": [
                "MailExitPhone",
                "CheckMainWorld"
            ]
        },
        "MailExitPhone": {
            "desc": "关闭手机菜单退回大世界",
            "recognition": "TemplateMatch",
            "template": [
                "phone_close_mask.png",
                "stage_close_dark_mask.png",
                "phone_close.png",
                "stage_close_dark.png"
            ],
            "green_mask": True,
            "roi": [
                1190,
                5,
                85,
                80
            ],
            "threshold": 0.65,
            "action": "Click",
            "target": [
                1235,
                42
            ],
            "post_delay": 600,
            "next": [
                "CheckMainWorld"
            ]
        },
        "MailReturnAndRetry": {
            "desc": "异常时退回重试",
            "action": "Click",
            "target": [
                1235,
                42
            ],
            "post_delay": 600,
            "next": [
                "MailOpenPhone",
                "MailFromPhone",
                "MailFromPhoneByAnchor"
            ]
        }
    }
    (PIPELINE_DIR / "Mail.json").write_text(json.dumps(mail_pipeline, ensure_ascii=False, indent=4), encoding="utf-8")
    print("  + 已生成 Mail.json")

    # DailyTraining.json
    daily_pipeline = {
        "DailyTraining": {
            "desc": "每日实训活跃度奖励领取",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "DailySwitchTab",
                "DailyAlreadyOpen",
                "DailyOpenFromHud",
                "DailyOpenPhone",
                "DailyFromPhone"
            ]
        },
        "DailyOpenFromHud": {
            "desc": "在大世界点击右上角指南图标",
            "recognition": "TemplateMatch",
            "template": [
                "hud_guide_mask.png",
                "hud_guide.png"
            ],
            "green_mask": True,
            "roi": [
                970,
                10,
                80,
                75
            ],
            "threshold": 0.65,
            "action": "Click",
            "target": [
                1010,
                44
            ],
            "post_delay": 800,
            "next": [
                "DailySwitchTab",
                "DailyAlreadyOpen"
            ]
        },
        "DailyOpenPhone": {
            "desc": "在大世界点击左上角手机图标",
            "recognition": "TemplateMatch",
            "template": [
                "hud_phone_mask.png",
                "hud_phone.png"
            ],
            "green_mask": True,
            "roi": [
                5,
                25,
                65,
                70
            ],
            "threshold": 0.65,
            "action": "Click",
            "target": [
                30,
                60
            ],
            "post_delay": 800,
            "next": [
                "DailyFromPhone"
            ]
        },
        "DailyFromPhone": {
            "desc": "从手机菜单点击指南磁贴",
            "recognition": "OCR",
            "expected": [
                "指南"
            ],
            "roi": [
                740,
                575,
                130,
                115
            ],
            "action": "Click",
            "target": [
                802,
                633
            ],
            "post_delay": 800,
            "next": [
                "DailySwitchTab",
                "DailyAlreadyOpen"
            ]
        },
        "DailySwitchTab": {
            "desc": "打开指南后始终先点击第一个标签页（每日实训），防止因实训完成默认停留在第二页",
            "recognition": "OCR",
            "expected": [
                "星际和平指南",
                "每日实训",
                "生存索引",
                "逐光捡金",
                "旷宇纷争",
                "战术训练"
            ],
            "roi": [
                20,
                10,
                600,
                150
            ],
            "action": "Click",
            "target": [
                188,
                112
            ],
            "post_delay": 700,
            "next": [
                "DailyAlreadyOpen"
            ]
        },
        "DailyAlreadyOpen": {
            "desc": "确认已在每日实训界面",
            "recognition": "OCR",
            "expected": [
                "每日实训"
            ],
            "roi": [
                20,
                10,
                250,
                70
            ],
            "action": "DoNothing",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "DailyCheckAlreadyFull",
                "DailyClaimTaskCard",
                "DailyClaimProgressNodes"
            ]
        },
        "DailyCheckAlreadyFull": {
            "desc": "检查本日活跃度是否已满",
            "recognition": "OCR",
            "expected": [
                "本日活跃度已满"
            ],
            "roi": [
                100,
                520,
                1080,
                120
            ],
            "action": "DoNothing",
            "pre_delay": 0,
            "post_delay": 0,
            "focus": {
                "Node.Recognition.Succeeded": "今日每日实训活跃度已满（500/500），无需重复领取"
            },
            "next": [
                "DailyDoneClose"
            ]
        },
        "DailyClaimTaskCard": {
            "desc": "点击单项任务卡片领取",
            "recognition": "OCR",
            "expected": [
                "领取"
            ],
            "roi": [
                100,
                520,
                1080,
                120
            ],
            "action": "Click",
            "post_delay": 600,
            "next": [
                "DailyClaimTaskCard",
                "DailyClaimProgressNodes"
            ]
        },
        "DailyClaimProgressNodes": {
            "desc": "点击顶部活跃度进度条宝箱（点满500档）",
            "action": "Click",
            "target": [
                1135,
                187
            ],
            "post_delay": 600,
            "next": [
                "DailyDismissReward",
                "DailyDoneClose"
            ]
        },
        "DailyDismissReward": {
            "desc": "关闭活跃度奖励弹窗",
            "recognition": "OCR",
            "expected": [
                "点击空白处关闭",
                "获得物品"
            ],
            "roi": [
                400,
                100,
                480,
                600
            ],
            "action": "Click",
            "target": [
                640,
                680
            ],
            "post_delay": 600,
            "next": [
                "DailyDoneClose"
            ]
        },
        "DailyDoneClose": {
            "desc": "关闭指南界面",
            "action": "Click",
            "target": [
                1235,
                42
            ],
            "post_delay": 600,
            "next": [
                "DailyExitPhone",
                "CheckMainWorld"
            ]
        },
        "DailyExitPhone": {
            "desc": "若在手机菜单则关闭退出",
            "recognition": "TemplateMatch",
            "template": [
                "phone_close_mask.png",
                "stage_close_dark_mask.png",
                "phone_close.png",
                "stage_close_dark.png"
            ],
            "green_mask": True,
            "roi": [
                1190,
                5,
                85,
                80
            ],
            "threshold": 0.65,
            "action": "Click",
            "target": [
                1235,
                42
            ],
            "post_delay": 600,
            "next": [
                "CheckMainWorld"
            ]
        }
    }
    (PIPELINE_DIR / "DailyTraining.json").write_text(json.dumps(daily_pipeline, ensure_ascii=False, indent=4), encoding="utf-8")
    print("  + 已生成 DailyTraining.json")

    # NamelessHonor.json
    honor_pipeline = {
        "NamelessHonor": {
            "desc": "无名勋礼一键领取任务经验与等级奖励",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "HonorAlreadyOpen",
                "HonorOpenFromHud",
                "HonorOpenPhone",
                "HonorFromPhone",
                "HonorClosePhoneAndClickHud"
            ]
        },
        "HonorOpenFromHud": {
            "desc": "在大世界点击右上角无名勋礼图标",
            "recognition": "TemplateMatch",
            "template": [
                "hud_honor_mask.png",
                "hud_honor.png"
            ],
            "green_mask": True,
            "roi": [
                840,
                10,
                75,
                75
            ],
            "threshold": 0.65,
            "action": "Click",
            "target": [
                876,
                44
            ],
            "post_delay": 900,
            "next": [
                "HonorAlreadyOpen"
            ]
        },
        "HonorOpenPhone": {
            "desc": "在大世界点击左上角手机图标",
            "recognition": "TemplateMatch",
            "template": [
                "hud_phone_mask.png",
                "hud_phone.png"
            ],
            "green_mask": True,
            "roi": [
                5,
                25,
                65,
                70
            ],
            "threshold": 0.65,
            "action": "Click",
            "target": [
                30,
                60
            ],
            "post_delay": 800,
            "next": [
                "HonorFromPhone",
                "HonorClosePhoneAndClickHud"
            ]
        },
        "HonorFromPhone": {
            "desc": "从手机菜单点击无名勋礼磁贴",
            "recognition": "OCR",
            "expected": [
                "无名勋礼"
            ],
            "roi": [
                850,
                470,
                120,
                115
            ],
            "action": "Click",
            "target": [
                910,
                525
            ],
            "post_delay": 900,
            "next": [
                "HonorAlreadyOpen"
            ]
        },
        "HonorClosePhoneAndClickHud": {
            "desc": "若手机菜单中未出现无名勋礼磁贴，关闭手机菜单并退回大世界点击右上角HUD图标",
            "recognition": "OCR",
            "expected": [
                "委托",
                "指南",
                "跃迁",
                "角色"
            ],
            "roi": [
                580,
                250,
                620,
                450
            ],
            "action": "Click",
            "target": [
                1235,
                42
            ],
            "post_delay": 800,
            "next": [
                "HonorOpenFromHud",
                "HonorClickHudDirect"
            ]
        },
        "HonorClickHudDirect": {
            "desc": "直接点击右上角HUD无名勋礼坐标",
            "recognition": "DirectHit",
            "action": "Click",
            "target": [
                876,
                44
            ],
            "max_hit": 1,
            "post_delay": 900,
            "next": [
                "HonorAlreadyOpen",
                "HonorDoneClose"
            ]
        },
        "HonorAlreadyOpen": {
            "desc": "确认已在无名勋礼界面",
            "recognition": "OCR",
            "expected": [
                "无名勋礼"
            ],
            "roi": [
                20,
                10,
                220,
                70
            ],
            "action": "DoNothing",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "HonorSwitchToQuestTab"
            ]
        },
        "HonorSwitchToQuestTab": {
            "desc": "点击左侧任务标签",
            "action": "Click",
            "target": [
                46,
                208
            ],
            "post_delay": 700,
            "next": [
                "HonorClaimQuests",
                "HonorSwitchToRewardTab"
            ]
        },
        "HonorClaimQuests": {
            "desc": "点击任务一键领取",
            "recognition": "OCR",
            "expected": [
                "一键领取",
                "领取"
            ],
            "roi": [
                750,
                580,
                490,
                125
            ],
            "action": "Click",
            "post_delay": 800,
            "focus": {
                "Node.Recognition.Succeeded": "已领取无名勋礼任务经验"
            },
            "next": [
                "HonorDismissPopup",
                "HonorSwitchToRewardTab"
            ]
        },
        "HonorDismissPopup": {
            "desc": "关闭经验等级弹窗",
            "recognition": "OCR",
            "expected": [
                "点击空白处关闭",
                "获得物品",
                "等级提升"
            ],
            "roi": [
                400,
                100,
                480,
                600
            ],
            "action": "Click",
            "target": [
                640,
                680
            ],
            "post_delay": 600,
            "next": [
                "HonorSwitchToRewardTab"
            ]
        },
        "HonorSwitchToRewardTab": {
            "desc": "点击左侧奖励标签",
            "action": "Click",
            "target": [
                46,
                122
            ],
            "post_delay": 700,
            "next": [
                "HonorClaimRewards",
                "HonorClaimRewardsTemplate",
                "HonorDoneClose"
            ]
        },
        "HonorClaimRewards": {
            "desc": "点击奖励一键领取（兼容未解锁荣勋时位于左侧 [788,646,166,46] 与右侧两种位置）",
            "recognition": "OCR",
            "expected": [
                "一键领取"
            ],
            "roi": [
                750,
                620,
                490,
                90
            ],
            "action": "Click",
            "post_delay": 800,
            "focus": {
                "Node.Recognition.Succeeded": "已领取无名勋礼等级奖励"
            },
            "next": [
                "HonorDismissRewardPopup",
                "HonorDoneClose"
            ]
        },
        "HonorClaimRewardsTemplate": {
            "desc": "通过模板匹配点击无名勋礼奖励一键领取按钮",
            "recognition": "TemplateMatch",
            "template": "honor_reward_claim_all.png",
            "roi": [
                750,
                620,
                490,
                90
            ],
            "threshold": 0.75,
            "action": "Click",
            "post_delay": 800,
            "focus": {
                "Node.Recognition.Succeeded": "已领取无名勋礼等级奖励"
            },
            "next": [
                "HonorDismissRewardPopup",
                "HonorDoneClose"
            ]
        },
        "HonorDismissRewardPopup": {
            "desc": "关闭无名勋礼奖励弹窗",
            "recognition": "OCR",
            "expected": [
                "点击空白处关闭",
                "获得物品"
            ],
            "roi": [
                400,
                100,
                480,
                600
            ],
            "action": "Click",
            "target": [
                640,
                680
            ],
            "post_delay": 600,
            "next": [
                "HonorDoneClose"
            ]
        },
        "HonorDoneClose": {
            "desc": "关闭无名勋礼界面",
            "action": "Click",
            "target": [
                1235,
                42
            ],
            "post_delay": 600,
            "next": [
                "HonorExitPhone",
                "CheckMainWorld"
            ]
        },
        "HonorExitPhone": {
            "desc": "关闭手机菜单退回大世界",
            "recognition": "TemplateMatch",
            "template": [
                "phone_close_mask.png",
                "stage_close_dark_mask.png",
                "phone_close.png",
                "stage_close_dark.png"
            ],
            "green_mask": True,
            "roi": [
                1190,
                5,
                85,
                80
            ],
            "threshold": 0.65,
            "action": "Click",
            "target": [
                1235,
                42
            ],
            "post_delay": 600,
            "next": [
                "CheckMainWorld"
            ]
        }
    }
    (PIPELINE_DIR / "NamelessHonor.json").write_text(json.dumps(honor_pipeline, ensure_ascii=False, indent=4), encoding="utf-8")
    print("  + 已生成 NamelessHonor.json")

    # TrailblazePower.json
    power_pipeline = {
        "TrailblazePower": {
            "desc": "消耗开拓力刷副本/拟造花萼/饰品提取/侵蚀隧洞",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "PowerStageReady",
                "PowerInStageDetail",
                "PowerInSurvivalIndex",
                "PowerOpenGuideFromHud",
                "PowerOpenPhone",
                "PowerFromPhone"
            ]
        },
        "PowerOpenGuideFromHud": {
            "desc": "在大世界点击右上角指南图标",
            "recognition": "TemplateMatch",
            "template": [
                "hud_guide_mask.png",
                "hud_guide.png"
            ],
            "green_mask": True,
            "roi": [970, 10, 80, 75],
            "threshold": 0.65,
            "action": "Click",
            "target": [1010, 44],
            "post_delay": 800,
            "next": [
                "PowerInSurvivalIndex",
                "PowerSwitchToSurvivalTab"
            ]
        },
        "PowerOpenPhone": {
            "desc": "在大世界点击左上角手机图标",
            "recognition": "TemplateMatch",
            "template": [
                "hud_phone_mask.png",
                "hud_phone.png"
            ],
            "green_mask": True,
            "roi": [5, 25, 65, 70],
            "threshold": 0.65,
            "action": "Click",
            "target": [30, 60],
            "post_delay": 700,
            "next": [
                "PowerFromPhone"
            ]
        },
        "PowerFromPhone": {
            "desc": "从手机菜单点击指南磁贴",
            "recognition": "OCR",
            "expected": ["指南"],
            "roi": [740, 575, 130, 115],
            "action": "Click",
            "target": [802, 633],
            "post_delay": 800,
            "next": [
                "PowerInSurvivalIndex",
                "PowerSwitchToSurvivalTab"
            ]
        },
        "PowerSwitchToSurvivalTab": {
            "desc": "识别已在指南界面后点击生存索引标签",
            "recognition": "OCR",
            "expected": [
                "每日实训",
                "生存索引",
                "旷宇纷争",
                "战术训练",
                "星际和平指南"
            ],
            "roi": [20, 10, 600, 150],
            "action": "Click",
            "target": [284, 112],
            "post_delay": 700,
            "next": [
                "PowerInSurvivalIndex"
            ]
        },
        "PowerInSurvivalIndex": {
            "desc": "确认已在生存索引页面",
            "recognition": "OCR",
            "expected": [
                "培养目标",
                "饰品提取",
                "拟造花萼",
                "凝滞虚影",
                "侵蚀隧洞"
            ],
            "roi": [105, 220, 330, 460],
            "action": "DoNothing",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "PowerSelectCategory",
                "PowerScrollLeftToTop"
            ]
        },
        "PowerScrollLeftToTop": {
            "desc": "若左侧分类已下滑则拉回顶部",
            "recognition": "DirectHit",
            "action": "Swipe",
            "begin": [270, 260],
            "end": [270, 580],
            "duration": 350,
            "post_delay": 600,
            "max_hit": 1,
            "next": [
                "PowerSelectCategory"
            ]
        },
        "PowerSelectCategory": {
            "desc": "OCR识别并点击左侧副本分类（默认培养目标，由选项覆写）",
            "recognition": "OCR",
            "expected": ["培养目标"],
            "roi": [105, 220, 330, 460],
            "action": "Click",
            "post_delay": 700,
            "next": [
                "PowerClickEnterStage"
            ]
        },
        "PowerClickCavernTab": {
            "desc": "点击侵蚀隧洞分类",
            "recognition": "OCR",
            "expected": ["侵蚀隧洞", "遗器"],
            "roi": [105, 220, 330, 460],
            "action": "Click",
            "post_delay": 700,
            "next": [
                "PowerClickEnterStage"
            ]
        },
        "PowerClickStagnantTab": {
            "desc": "点击凝滞虚影分类",
            "recognition": "OCR",
            "expected": ["凝滞虚影", "角色晋阶材料"],
            "roi": [105, 220, 330, 460],
            "action": "Click",
            "post_delay": 700,
            "next": [
                "PowerClickEnterStage"
            ]
        },
        "PowerClickEchoTab": {
            "desc": "点击历战余响分类",
            "recognition": "OCR",
            "expected": ["历战余响", "行迹高级材料"],
            "roi": [105, 220, 330, 460],
            "action": "Click",
            "post_delay": 700,
            "next": [
                "PowerClickEnterStage"
            ]
        },
        "PowerClickEnterStage": {
            "desc": "点击右侧列表第一排的【进入】或【传送】",
            "recognition": "OCR",
            "expected": [
                "进入",
                "传送"
            ],
            "roi": [985, 195, 190, 135],
            "order_by": "Vertical",
            "index": 0,
            "action": "Click",
            "post_delay": 900,
            "focus": {
                "Node.Recognition.Succeeded": "已从生存索引进入副本关卡页"
            },
            "next": [
                "PowerWaitStagePanel"
            ]
        },
        "PowerWaitStagePanel": {
            "desc": "等待关卡准备面板加载完成",
            "recognition": "OCR",
            "expected": [
                "挑战次数",
                "开始挑战",
                "挑战"
            ],
            "roi": [750, 540, 500, 155],
            "action": "DoNothing",
            "pre_delay": 0,
            "post_delay": 100,
            "next": [
                "PowerEnableQuickRefill",
                "PowerAddChallengeCount",
                "PowerAfterSetCount"
            ]
        },
        "PowerEnableQuickRefill": {
            "desc": "检查并开启【快捷补充开拓力】开关（兼容普通副本与位面饰品提取不同纵坐标）",
            "recognition": "TemplateMatch",
            "template": "quick_refill_off.png",
            "roi": [1175, 460, 80, 95],
            "threshold": 0.72,
            "action": "Click",
            "pre_delay": 80,
            "post_delay": 450,
            "max_hit": 1,
            "focus": {
                "Node.Recognition.Succeeded": "已开启【快捷补充开拓力】开关"
            },
            "next": [
                "PowerAddChallengeCount",
                "PowerAfterSetCount"
            ]
        },
        "PowerAddChallengeCount": {
            "desc": "通过模板匹配点击右下角亮色【+】按钮设置挑战次数（到达上限变灰时自动停止）",
            "recognition": "TemplateMatch",
            "template": "count_plus.png",
            "roi": [1170, 515, 85, 95],
            "threshold": 0.72,
            "action": "Click",
            "pre_delay": 40,
            "post_delay": 160,
            "max_hit": 0,
            "next": [
                "PowerAddChallengeCount",
                "PowerAfterSetCount"
            ]
        },
        "PowerAfterSetCount": {
            "desc": "完成挑战次数设置后进入挑战或编队",
            "recognition": "DirectHit",
            "action": "DoNothing",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "PowerQuickBattleClick",
                "PowerStageReady",
                "PowerInStageDetail"
            ]
        },
        "PowerQuickBattleClick": {
            "desc": "点击【快速刷取】使用助燃券秒刷（拟造花萼/凝滞虚影）",
            "recognition": "OCR",
            "expected": ["快速刷取"],
            "roi": [600, 620, 190, 80],
            "action": "Click",
            "target": [694, 662],
            "post_delay": 1000,
            "max_hit": 0,
            "focus": {
                "Node.Recognition.Succeeded": "已点击【快速刷取】，等待确认弹窗..."
            },
            "next": [
                "PowerInsufficientCancel",
                "PowerQuickBattleConfirm",
                "PowerStageReady",
                "PowerInStageDetail"
            ]
        },
        "PowerQuickBattleConfirm": {
            "desc": "在快速刷取确认弹窗中点击【确认】",
            "recognition": "OCR",
            "expected": ["确认", "确定", "使用助燃券"],
            "roi": [620, 360, 400, 270],
            "action": "Click",
            "target": [815, 590],
            "post_delay": 1500,
            "focus": {
                "Node.Recognition.Succeeded": "已确认使用助燃券快速刷取，等待刷取完成..."
            },
            "next": [
                "PowerInsufficientCancel",
                "PowerQuickBattleDismiss",
                "PowerQuickBattleCloseTemplate"
            ]
        },
        "PowerQuickBattleDismiss": {
            "desc": "助燃券快速刷取完成后点击【关闭】按钮",
            "recognition": "OCR",
            "expected": ["关闭", "再来一次", "第1次刷取"],
            "roi": [280, 280, 720, 350],
            "action": "Click",
            "target": [465, 590],
            "post_delay": 1000,
            "focus": {
                "Node.Recognition.Succeeded": "已完成助燃券快速刷取，点击【关闭】并退回大世界"
            },
            "next": [
                "PowerCloseAfterExit",
                "PowerCloseStageByText",
                "PowerDoneClose",
                "CheckMainWorld"
            ]
        },
        "PowerQuickBattleCloseTemplate": {
            "desc": "通过模板匹配点击快速刷取完成后的【关闭】按钮",
            "recognition": "TemplateMatch",
            "template": "quick_battle_close.png",
            "roi": [290, 540, 350, 90],
            "threshold": 0.85,
            "action": "Click",
            "target": [465, 590],
            "post_delay": 1000,
            "focus": {
                "Node.Recognition.Succeeded": "已完成助燃券快速刷取，点击【关闭】并退回大世界"
            },
            "next": [
                "PowerCloseAfterExit",
                "PowerCloseStageByText",
                "PowerDoneClose",
                "CheckMainWorld"
            ]
        },
        "PowerInStageDetail": {
            "desc": "在副本详情页识别并点击【挑战】",
            "recognition": "OCR",
            "expected": ["挑战"],
            "roi": [790, 615, 470, 85],
            "action": "Click",
            "target": [1030, 662],
            "post_delay": 900,
            "next": [
                "PowerInsufficientCancel",
                "PowerStageReady"
            ]
        },
        "PowerStageReady": {
            "desc": "关卡准备就绪（匹配位面饰品提取与编成页开始挑战）",
            "recognition": "OCR",
            "expected": [
                "开始挑战"
            ],
            "roi": [830, 610, 430, 85],
            "action": "DoNothing",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "PowerClickStartChallenge"
            ]
        },
        "PowerClickSupportBtn": {
            "desc": "点击【支援】按钮选择支援角色",
            "recognition": "OCR",
            "expected": ["支援"],
            "roi": [470, 520, 760, 170],
            "action": "Click",
            "post_delay": 700,
            "max_hit": 1,
            "focus": {
                "Node.Recognition.Succeeded": "正在打开支援列表选择好友第一位支援角色..."
            },
            "next": [
                "PowerSelectFirstSupport"
            ]
        },
        "PowerSelectFirstSupport": {
            "desc": "在支援角色列表中点击左侧第一位好友支援角色卡片",
            "recognition": "OCR",
            "expected": [
                "支援列表",
                "支援角色",
                "仅查看好友",
                "刷新列表",
                "支援详情"
            ],
            "roi": [
                20,
                40,
                480,
                660
            ],
            "action": "Click",
            "target": [
                220,
                190
            ],
            "post_delay": 550,
            "focus": {
                "Node.Recognition.Succeeded": "已选中第一位好友支援角色"
            },
            "next": [
                "PowerConfirmSupportJoin",
                "PowerClickStartChallenge"
            ]
        },
        "PowerConfirmSupportJoin": {
            "desc": "在普通副本支援角色页点击右下角【确认】让第一位好友支援角色入队",
            "recognition": "OCR",
            "expected": [
                "确认",
                "入队",
                "更换"
            ],
            "roi": [
                900,
                615,
                350,
                85
            ],
            "action": "Click",
            "target": [
                1085,
                664
            ],
            "post_delay": 700,
            "focus": {
                "Node.Recognition.Succeeded": "已确认第一位好友支援角色入队"
            },
            "next": [
                "PowerClickStartChallenge"
            ]
        },
        "PowerClickStartChallenge": {
            "desc": "点击【开始挑战】进入关卡战斗",
            "recognition": "OCR",
            "expected": ["开始挑战"],
            "roi": [830, 610, 430, 85],
            "action": "Click",
            "target": [1070, 660],
            "post_delay": 2500,
            "max_hit": 2,
            "focus": {
                "Node.Recognition.Succeeded": "已点击【开始挑战】，进入战斗流程..."
            },
            "next": [
                "PowerInsufficientCancel",
                "PowerBattleSuccess",
                "PowerClickStartChallenge",
                "PowerWaitBattleFinish"
            ]
        },
        "PowerWaitBattleFinish": {
            "desc": "等待战斗完成，循环点击普攻区触发位面饰品提取/凝滞虚影大世界开怪",
            "recognition": "DirectHit",
            "action": "Click",
            "target": [1110, 580],
            "post_delay": 2500,
            "next": [
                "PowerInsufficientCancel",
                "PowerBattleSuccess",
                "PowerWaitBattleFinish"
            ],
            "timeout": 300000
        },
        "PowerBattleSuccess": {
            "desc": "战斗结算成功，判断是否再来一次或退出关卡",
            "recognition": "OCR",
            "expected": [
                "挑战成功",
                "退出关卡",
                "再来一次"
            ],
            "roi": [250, 50, 780, 630],
            "action": "DoNothing",
            "pre_delay": 0,
            "post_delay": 0,
            "next": [
                "PowerBattleAgain",
                "PowerBattleExit"
            ]
        },
        "PowerBattleAgain": {
            "desc": "当自定义刷取次数超过单次上限时，点击【再来一次】继续下一整轮",
            "recognition": "OCR",
            "expected": ["再来一次"],
            "roi": [670, 595, 340, 80],
            "action": "Click",
            "target": [844, 634],
            "post_delay": 2500,
            "max_hit": 0,
            "focus": {
                "Node.Recognition.Succeeded": "自定义次数未满，点击【再来一次】继续下一轮刷取"
            },
            "next": [
                "PowerInsufficientCancel",
                "PowerBattleSuccess",
                "PowerWaitBattleFinish"
            ]
        },
        "PowerBattleExit": {
            "desc": "点击【退出关卡】",
            "recognition": "OCR",
            "expected": ["退出关卡"],
            "roi": [260, 595, 350, 80],
            "action": "Click",
            "target": [436, 634],
            "post_delay": 2000,
            "focus": {
                "Node.Recognition.Succeeded": "已完成当前轮次，退出关卡"
            },
            "next": [
                "PowerRemainderReenter",
                "CheckMainWorld",
                "PowerCloseAfterExit",
                "PowerCloseStageByText",
                "PowerExitDomainToMainWorld"
            ]
        },
        "PowerRemainderReenter": {
            "desc": "当自定义次数有余数轮次时，在退回关卡面板后重新设置余数次数并再次挑战",
            "recognition": "OCR",
            "expected": [
                "挑战次数",
                "开始挑战",
                "挑战"
            ],
            "roi": [750, 540, 500, 155],
            "action": "DoNothing",
            "pre_delay": 0,
            "post_delay": 150,
            "max_hit": 0,
            "focus": {
                "Node.Recognition.Succeeded": "开始执行自定义刷取次数的剩余轮次..."
            },
            "next": [
                "PowerAddRemainderCount",
                "PowerAfterSetCount"
            ]
        },
        "PowerAddRemainderCount": {
            "desc": "为剩余轮次点击【+】按钮设置余数挑战次数",
            "recognition": "TemplateMatch",
            "template": "count_plus.png",
            "roi": [1170, 515, 85, 95],
            "threshold": 0.72,
            "action": "Click",
            "pre_delay": 40,
            "post_delay": 160,
            "max_hit": 0,
            "next": [
                "PowerAddRemainderCount",
                "PowerAfterSetCount"
            ]
        },
        "PowerExitDomainToMainWorld": {
            "desc": "若退关后停留在关卡详情页或指南页，点击右上角叉号关闭",
            "recognition": "TemplateMatch",
            "template": [
                "phone_close_mask.png",
                "stage_close_dark_mask.png",
                "phone_close.png",
                "stage_close_dark.png"
            ],
            "green_mask": True,
            "roi": [1190, 5, 85, 80],
            "threshold": 0.65,
            "action": "Click",
            "target": [1235, 42],
            "post_delay": 900,
            "next": [
                "CheckMainWorld",
                "PowerCloseAfterExit",
                "PowerCloseStageByText"
            ]
        },
        "PowerInsufficientCancel": {
            "desc": "开拓力与后备开拓力均不足时弹出【开拓力补充】弹窗，点击取消并退回大世界",
            "recognition": "OCR",
            "expected": [
                "开拓力补充",
                "请选择补充方式",
                "取出等量后备开拓力",
                "星琼补充"
            ],
            "roi": [260, 140, 760, 360],
            "action": "Click",
            "target": [465, 520],
            "post_delay": 1100,
            "focus": {
                "Node.Recognition.Succeeded": "体力不足，已停止刷取并退回大世界"
            },
            "next": [
                "PowerCloseAfterExit",
                "PowerCloseStageByText",
                "PowerDoneClose",
                "CheckMainWorld"
            ]
        },
        "PowerCloseAfterExit": {
            "desc": "若退关后仍有深色/浅色右上角叉号窗口，点击叉号关闭",
            "recognition": "TemplateMatch",
            "template": [
                "phone_close_mask.png",
                "stage_close_dark_mask.png",
                "phone_close.png",
                "stage_close_dark.png"
            ],
            "green_mask": True,
            "roi": [1190, 5, 85, 80],
            "threshold": 0.65,
            "action": "Click",
            "target": [1235, 42],
            "post_delay": 900,
            "max_hit": 4,
            "next": [
                "CheckMainWorld",
                "PowerCloseAfterExit",
                "PowerCloseStageByText"
            ]
        },
        "PowerCloseStageByText": {
            "desc": "通过识别关卡页或指南页文字直接点击右上角叉号退出",
            "recognition": "OCR",
            "expected": [
                "挑战",
                "开始挑战",
                "挑战次数",
                "拟造花萼",
                "位面饰品",
                "生存索引",
                "星际和平指南"
            ],
            "roi": [20, 10, 1240, 690],
            "action": "Click",
            "target": [1235, 42],
            "post_delay": 900,
            "max_hit": 4,
            "next": [
                "CheckMainWorld",
                "PowerCloseAfterExit",
                "PowerCloseStageByText"
            ]
        },
        "PowerDoneClose": {
            "desc": "关闭并退回大世界",
            "action": "Click",
            "target": [1235, 42],
            "post_delay": 800,
            "next": [
                "CheckMainWorld"
            ]
        }
    }

    (PIPELINE_DIR / "TrailblazePower.json").write_text(json.dumps(power_pipeline, ensure_ascii=False, indent=4), encoding="utf-8")
    print("  + 已生成 TrailblazePower.json")
    print("[OK] 所有流水线 JSON 生成完成！\n")


def update_interface_and_locales():
    print("[*] 更新 interface.json 与 locales/zh_cn.json...")
    interface_path = ASSETS_DIR / "interface.json"
    zh_cn_path = LOCALES_DIR / "zh_cn.json"

    # 读取旧 interface
    interface_data = json.loads(interface_path.read_text(encoding="utf-8"))
    interface_data["version"] = "v0.0.2"
    interface_data["github"] = "https://github.com/Tspme1/MaaHSR"
    interface_data["title"] = "MaaHSR v0.0.2"

    # 默认预设配置（新安装 APK 自动生成包含全部 6 项日常任务的默认配置）
    interface_data["preset"] = [
        {
            "name": "DailyDefault",
            "label": "日常一条龙",
            "description": "默认包含启动游戏、每日委托、邮件领取、消耗开拓力、每日实训与无名勋礼",
            "task": [
                {"name": "StartUp", "enabled": True},
                {"name": "Assignments", "enabled": True},
                {"name": "Mail", "enabled": True},
                {"name": "TrailblazePower", "enabled": True},
                {"name": "DailyTraining", "enabled": True},
                {"name": "NamelessHonor", "enabled": True},
                {"name": "KeepAliveCapture", "enabled": False}
            ]
        }
    ]

    # 注册日常任务（消耗开拓力排第4，每日实训第5，无名勋礼第6，屏幕保活不带编号）
    interface_data["task"] = [
        {
            "name": "StartUp",
            "label": "$task.startup.label",
            "entry": "StartUp",
            "default_check": True,
            "description": "$task.startup.desc",
            "option": [
                "ClientChannel"
            ]
        },
        {
            "name": "Assignments",
            "label": "$task.assignments.label",
            "entry": "Assignments",
            "default_check": True,
            "description": "$task.assignments.desc",
            "option": [
                "AssignmentAction"
            ]
        },
        {
            "name": "Mail",
            "label": "$task.mail.label",
            "entry": "Mail",
            "default_check": True,
            "description": "$task.mail.desc",
            "option": [
                "MailAction"
            ]
        },
        {
            "name": "TrailblazePower",
            "label": "$task.trailblaze_power.label",
            "entry": "TrailblazePower",
            "default_check": True,
            "description": "$task.trailblaze_power.desc",
            "option": [
                "TrailblazeTarget",
                "ChallengeCount",
                "UseSupport",
                "UseFuelVoucher"
            ]
        },
        {
            "name": "DailyTraining",
            "label": "$task.daily_training.label",
            "entry": "DailyTraining",
            "default_check": True,
            "description": "$task.daily_training.desc",
            "option": [
                "DailyTrainingAction"
            ]
        },
        {
            "name": "NamelessHonor",
            "label": "$task.nameless_honor.label",
            "entry": "NamelessHonor",
            "default_check": True,
            "description": "$task.nameless_honor.desc",
            "option": [
                "NamelessHonorAction"
            ]
        },
        {
            "name": "KeepAliveCapture",
            "label": "$task.capture.label",
            "entry": "KeepAliveCapture",
            "default_check": False,
            "description": "$task.capture.desc",
            "option": [
                "ClientChannel"
            ]
        }
    ]

    # 添加 Option
    if "option" not in interface_data:
        interface_data["option"] = {}

    interface_data["option"]["ClientChannel"] = {
        "type": "select",
        "label": "$option.channel.label",
        "default_case": "Official",
        "cases": [
            {
                "name": "Official",
                "label": "$resource.official.label",
                "pipeline_override": {
                    "StartUp": {
                        "package": "com.miHoYo.hkrpg"
                    },
                    "KeepAliveLaunchApp": {
                        "package": "com.miHoYo.hkrpg"
                    }
                }
            },
            {
                "name": "Bilibili",
                "label": "$resource.bilibili.label",
                "pipeline_override": {
                    "StartUp": {
                        "package": "com.miHoYo.hkrpg.bilibili"
                    },
                    "KeepAliveLaunchApp": {
                        "package": "com.miHoYo.hkrpg.bilibili"
                    }
                }
            }
        ]
    }

    interface_data["option"]["TrailblazeTarget"] = {
        "type": "select",
        "label": "$option.trailblaze_target.label",
        "default_case": "BuildTargetOrnament",
        "cases": [
            {
                "name": "BuildTargetOrnament",
                "label": "培养目标 - 推荐位面饰品（内圈）",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "recognition": "OCR",
                        "expected": ["饰品提取", "位面饰品"],
                        "roi": [105, 220, 330, 460],
                        "action": "Click",
                        "post_delay": 800,
                        "next": ["PowerClickEnterStage"]
                    },
                    "PowerClickEnterStage": {
                        "roi": [985, 295, 190, 75]
                    }
                }
            },
            {
                "name": "BuildTargetRelic",
                "label": "培养目标 - 推荐隧洞遗器（外圈）",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "recognition": "DirectHit",
                        "action": "Swipe",
                        "begin": [270, 580],
                        "end": [270, 240],
                        "duration": 450,
                        "post_delay": 700,
                        "next": ["PowerClickCavernTab"]
                    },
                    "PowerClickEnterStage": {
                        "roi": [985, 195, 190, 75]
                    }
                }
            },
            {
                "name": "CalyxGolden",
                "label": "拟造花萼（金）- 经验/信用点",
                "option": [
                    "CalyxGoldenStage"
                ],
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "recognition": "OCR",
                        "expected": ["经验材料", "信用点", "拟造花萼（金）", "拟造花萼(金)"],
                        "roi": [105, 220, 330, 460],
                        "action": "Click",
                        "post_delay": 700,
                        "next": ["PowerClickEnterStage"]
                    }
                }
            },
            {
                "name": "CalyxCrimson",
                "label": "拟造花萼（赤）- 行迹材料",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "recognition": "OCR",
                        "expected": ["行迹材料", "拟造花萼（赤）", "拟造花萼(赤)"],
                        "roi": [105, 220, 330, 460],
                        "action": "Click",
                        "post_delay": 700,
                        "next": ["PowerClickEnterStage"]
                    }
                }
            },
            {
                "name": "StagnantShadow",
                "label": "凝滞虚影 - 角色晋阶材料",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "recognition": "DirectHit",
                        "action": "Swipe",
                        "begin": [270, 580],
                        "end": [270, 240],
                        "duration": 450,
                        "post_delay": 700,
                        "next": ["PowerClickStagnantTab"]
                    },
                    "PowerClickEnterStage": {
                        "roi": [985, 195, 190, 75]
                    }
                }
            },
            {
                "name": "EchoOfWar",
                "label": "历战余响 - 周本高阶材料",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "recognition": "DirectHit",
                        "action": "Swipe",
                        "begin": [270, 580],
                        "end": [270, 240],
                        "duration": 450,
                        "post_delay": 700,
                        "next": ["PowerClickEchoTab"]
                    },
                    "PowerClickEnterStage": {
                        "roi": [985, 195, 190, 75]
                    }
                }
            }
        ]
    }

    interface_data["option"]["CalyxGoldenStage"] = {
        "type": "select",
        "label": "$option.calyx_golden_stage.label",
        "default_case": "Memories",
        "cases": [
            {
                "name": "Memories",
                "label": "回忆之蕾 - 角色经验材料",
                "pipeline_override": {
                    "PowerClickEnterStage": {
                        "roi": [985, 240, 190, 100],
                        "order_by": "Vertical",
                        "index": 0
                    }
                }
            },
            {
                "name": "Aether",
                "label": "以太之蕾 - 光锥经验材料",
                "pipeline_override": {
                    "PowerClickEnterStage": {
                        "roi": [985, 340, 190, 95],
                        "order_by": "Vertical",
                        "index": 0
                    }
                }
            },
            {
                "name": "Treasures",
                "label": "藏珍之蕾 - 信用点",
                "pipeline_override": {
                    "PowerClickEnterStage": {
                        "roi": [985, 440, 190, 95],
                        "order_by": "Vertical",
                        "index": 0
                    }
                }
            }
        ]
    }

    interface_data["option"]["ChallengeCount"] = {
        "type": "select",
        "label": "$option.challenge_count.label",
        "default_case": "Count1",
        "cases": [
            {
                "name": "Count1",
                "label": "1 次",
                "pipeline_override": {
                    "PowerAddChallengeCount": {
                        "max_hit": 0
                    }
                }
            },
            {
                "name": "Count2",
                "label": "2 次",
                "pipeline_override": {
                    "PowerAddChallengeCount": {
                        "max_hit": 1
                    }
                }
            },
            {
                "name": "Count3",
                "label": "3 次",
                "pipeline_override": {
                    "PowerAddChallengeCount": {
                        "max_hit": 2
                    }
                }
            },
            {
                "name": "Count4",
                "label": "4 次",
                "pipeline_override": {
                    "PowerAddChallengeCount": {
                        "max_hit": 3
                    }
                }
            },
            {
                "name": "Count6",
                "label": "6 次",
                "pipeline_override": {
                    "PowerAddChallengeCount": {
                        "max_hit": 5
                    }
                }
            },
            {
                "name": "CountMax",
                "label": "最大次数",
                "pipeline_override": {
                    "PowerAddChallengeCount": {
                        "max_hit": 23
                    }
                }
            },
            {
                "name": "CustomCount",
                "label": "自定义刷取次数",
                "option": [
                    "CustomChallengeCountInput"
                ],
                "pipeline_override": {}
            }
        ]
    }

    interface_data["option"]["CustomChallengeCountInput"] = {
        "type": "input",
        "label": "$option.custom_count_input.label",
        "inputs": [
            {
                "name": "custom_count",
                "label": "$option.custom_count_field.label",
                "default": "6",
                "pipeline_type": "int",
                "verify": "^[1-9][0-9]*$",
                "pattern_msg": "$option.custom_count_pattern.msg"
            }
        ],
        "pipeline_override": {
            "PowerAddChallengeCount": {
                "max_hit": "{custom_count}"
            }
        }
    }

    interface_data["option"]["UseSupport"] = {
        "type": "select",
        "label": "$option.use_support.label",
        "default_case": "NoSupport",
        "cases": [
            {
                "name": "NoSupport",
                "label": "不使用支援角色",
                "pipeline_override": {
                    "PowerStageReady": {
                        "next": [
                            "PowerClickStartChallenge"
                        ]
                    }
                }
            },
            {
                "name": "UseFirstFriendSupport",
                "label": "使用好友支援角色",
                "option": [
                    "SupportSlot"
                ],
                "pipeline_override": {
                    "PowerStageReady": {
                        "next": [
                            "PowerClickSupportBtn",
                            "PowerClickStartChallenge"
                        ]
                    }
                }
            }
        ]
    }

    interface_data["option"]["SupportSlot"] = {
        "type": "select",
        "label": "$option.support_slot.label",
        "default_case": "Slot1",
        "cases": [
            {
                "name": "Slot1",
                "label": "第 1 位支援角色",
                "pipeline_override": {
                    "PowerSelectFirstSupport": {
                        "target": [220, 190],
                        "focus": {
                            "Node.Recognition.Succeeded": "已选中第 1 位好友支援角色"
                        }
                    }
                }
            },
            {
                "name": "Slot2",
                "label": "第 2 位支援角色",
                "pipeline_override": {
                    "PowerSelectFirstSupport": {
                        "target": [220, 306],
                        "focus": {
                            "Node.Recognition.Succeeded": "已选中第 2 位好友支援角色"
                        }
                    }
                }
            },
            {
                "name": "Slot3",
                "label": "第 3 位支援角色",
                "pipeline_override": {
                    "PowerSelectFirstSupport": {
                        "target": [220, 422],
                        "focus": {
                            "Node.Recognition.Succeeded": "已选中第 3 位好友支援角色"
                        }
                    }
                }
            },
            {
                "name": "Slot4",
                "label": "第 4 位支援角色",
                "pipeline_override": {
                    "PowerSelectFirstSupport": {
                        "target": [220, 538],
                        "focus": {
                            "Node.Recognition.Succeeded": "已选中第 4 位好友支援角色"
                        }
                    }
                }
            }
        ]
    }

    interface_data["option"]["UseFuelVoucher"] = {
        "type": "select",
        "label": "$option.use_fuel_voucher.label",
        "default_case": "NoVoucher",
        "cases": [
            {
                "name": "NoVoucher",
                "label": "不使用助燃券",
                "pipeline_override": {
                    "PowerQuickBattleClick": {
                        "max_hit": 0
                    }
                }
            },
            {
                "name": "UseVoucher",
                "label": "优先使用助燃券快速刷取",
                "pipeline_override": {
                    "PowerQuickBattleClick": {
                        "max_hit": 1
                    }
                }
            }
        ]
    }


    interface_data["option"]["AssignmentAction"] = {
        "type": "select",
        "label": "$option.assignment_action.label",
        "default_case": "ClaimAndRedispatch",
        "cases": [
            {
                "name": "ClaimAndRedispatch",
                "label": "一键领取并再次派遣",
                "pipeline_override": {}
            },
            {
                "name": "ClaimOnly",
                "label": "仅领取委托奖励",
                "pipeline_override": {
                    "AssignmentClickOneKeyClaim": {
                        "next": [
                            "AssignmentDismissReward",
                            "AssignmentDoneClose"
                        ]
                    }
                }
            }
        ]
    }

    interface_data["option"]["MailAction"] = {
        "type": "select",
        "label": "$option.mail_action.label",
        "default_case": "ClaimAll",
        "cases": [
            {
                "name": "ClaimAll",
                "label": "一键领取全部附件邮件",
                "pipeline_override": {}
            }
        ]
    }

    interface_data["option"]["DailyTrainingAction"] = {
        "type": "select",
        "label": "$option.daily_training_action.label",
        "default_case": "ClaimAll",
        "cases": [
            {
                "name": "ClaimAll",
                "label": "领取任务活跃度与全部档位奖励",
                "pipeline_override": {}
            },
            {
                "name": "ClaimNodesOnly",
                "label": "仅领取顶部活跃度进度奖励",
                "pipeline_override": {
                    "DailyAlreadyOpen": {
                        "next": [
                            "DailyCheckAlreadyFull",
                            "DailyClaimProgressNodes"
                        ]
                    }
                }
            }
        ]
    }

    interface_data["option"]["NamelessHonorAction"] = {
        "type": "select",
        "label": "$option.nameless_honor_action.label",
        "default_case": "ClaimQuestsAndRewards",
        "cases": [
            {
                "name": "ClaimQuestsAndRewards",
                "label": "领取任务经验与勋礼等级奖励",
                "pipeline_override": {}
            },
            {
                "name": "ClaimRewardsOnly",
                "label": "仅领取勋礼等级奖励",
                "pipeline_override": {
                    "HonorAlreadyOpen": {
                        "next": [
                            "HonorSwitchToRewardTab"
                        ]
                    }
                }
            }
        ]
    }

    interface_path.write_text(json.dumps(interface_data, ensure_ascii=False, indent=4), encoding="utf-8")
    print(f"  + interface.json 已更新至 v0.0.2")

    # 更新 zh_cn.json（非必要括号全部删除，任务标题只保留每日实训括号并改为领取每日活跃度奖励）
    locales_data = json.loads(zh_cn_path.read_text(encoding="utf-8"))
    locales_data.update({
        "task.startup.label": "1. 启动游戏",
        "task.startup.desc": "在虚拟屏中启动星铁，自动点击进入游戏并处理列车补给凭证领取浮层，进入大世界。",
        "task.assignments.label": "2. 每日委托",
        "task.assignments.desc": "自动进入委托界面，一键领取已完成的委托奖励并再次派遣。",
        "task.mail.label": "3. 邮件一键领取",
        "task.mail.desc": "自动打开手机菜单邮箱，一键领取所有未读或系统赠送邮件奖励。",
        "task.trailblaze_power.label": "4. 消耗开拓力",
        "task.trailblaze_power.desc": "自动前往生存索引，打开快捷补充开拓力并挑战指定副本，完成后自动退回大世界。",
        "task.daily_training.label": "5. 每日实训",
        "task.daily_training.desc": "自动打开星际和平指南每日实训页，领取已完成的任务活跃度及全部档位奖励。",
        "task.nameless_honor.label": "6. 无名勋礼",
        "task.nameless_honor.desc": "自动进入无名勋礼，一键领取任务经验与当前已解锁的勋礼等级奖励。",
        "task.capture.label": "虚拟屏后台保活与调试抓图",
        "option.trailblaze_target.label": "开拓力消耗副本目标",
        "option.calyx_golden_stage.label": "拟造花萼（金）具体副本",
        "option.assignment_action.label": "每日委托设置",
        "option.mail_action.label": "邮件领取设置",
        "option.daily_training_action.label": "每日实训设置",
        "option.nameless_honor_action.label": "无名勋礼设置",
        "option.challenge_count.label": "挑战次数",
        "option.custom_count_input.label": "自定义刷取次数",
        "option.custom_count_field.label": "输入刷取总次数",
        "option.custom_count_pattern.msg": "请输入大于 0 的正整数",
        "option.use_support.label": "是否使用支援角色",
        "option.support_slot.label": "选择支援位序号",
        "option.use_fuel_voucher.label": "助燃券快速刷取"
    })
    zh_cn_path.write_text(json.dumps(locales_data, ensure_ascii=False, indent=4), encoding="utf-8")
    print(f"  + locales/zh_cn.json 文案已更新")
    print("[OK] 界面与多语言配置更新完成！\n")


if __name__ == "__main__":
    crop_templates()
    build_masked_white_icons()
    build_pipelines()
    update_interface_and_locales()
    print("ALL DONE for MaaHSR v0.0.2 Resource Build!")
