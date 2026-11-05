#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

script_path = Path("tools/build_hsr_resources.py")
content = script_path.read_text(encoding="utf-8")

# 1. Update CROPS
old_crops = '''    ("battle_exit.png", "manual_20261103_213633_788.png", (282, 612, 590, 656)),
    ("battle_again.png", "manual_20261103_213633_788.png", (690, 612, 998, 656)),
]'''

new_crops = '''    ("battle_exit.png", "manual_20261103_213633_788.png", (282, 612, 590, 656)),
    ("battle_again.png", "manual_20261103_213633_788.png", (690, 612, 998, 656)),
    ("ornament_start_challenge.png", "manual_20261103_222651_770.png", (876, 636, 1244, 684)),
    ("support_btn_green.png", "manual_20261103_222651_770.png", (520, 570, 644, 604)),
    ("survival_cavern_tab.png", "manual_20261103_222749_789.png", (118, 430, 422, 514)),
    ("survival_stagnant_tab.png", "manual_20261103_222749_789.png", (118, 330, 422, 414)),
]'''

assert old_crops in content, "old_crops not found in build_hsr_resources.py"
content = content.replace(old_crops, new_crops)

# 2. Update TrailblazePower pipeline dictionary
old_power_section_start = '    # TrailblazePower.json\n    power_pipeline = {'
old_power_section_end = '    (PIPELINE_DIR / "TrailblazePower.json").write_text(json.dumps(power_pipeline, ensure_ascii=False, indent=4), encoding="utf-8")'

idx1 = content.find(old_power_section_start)
idx2 = content.find(old_power_section_end)
assert idx1 != -1 and idx2 != -1, "power section bounds not found"

new_power_pipeline = '''    # TrailblazePower.json
    power_pipeline = {
        "TrailblazePower": {
            "desc": "消耗开拓力刷副本/拟造花萼/饰品提取/侵蚀隧洞",
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
            "template": "hud_guide.png",
            "roi": [970, 10, 80, 75],
            "threshold": 0.7,
            "action": "Click",
            "target": [1010, 44],
            "post_delay": 1800,
            "next": [
                "PowerSwitchToSurvivalTab"
            ]
        },
        "PowerOpenPhone": {
            "desc": "在大世界点击左上角手机图标",
            "recognition": "TemplateMatch",
            "template": "hud_phone.png",
            "roi": [5, 30, 65, 75],
            "threshold": 0.7,
            "action": "Click",
            "target": [36, 64],
            "post_delay": 1500,
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
            "post_delay": 1800,
            "next": [
                "PowerSwitchToSurvivalTab"
            ]
        },
        "PowerSwitchToSurvivalTab": {
            "desc": "点击生存索引标签",
            "action": "Click",
            "target": [284, 112],
            "post_delay": 1500,
            "next": [
                "PowerSelectCategory"
            ]
        },
        "PowerInSurvivalIndex": {
            "desc": "确认已在生存索引页面",
            "recognition": "OCR",
            "expected": [
                "生存索引",
                "培养目标",
                "拟造花萼"
            ],
            "roi": [180, 80, 800, 550],
            "action": "DoNothing",
            "next": [
                "PowerSelectCategory"
            ]
        },
        "PowerSelectCategory": {
            "desc": "选择副本分类（默认培养目标，可通过选项重写）",
            "action": "Click",
            "target": [270, 280],
            "post_delay": 1200,
            "next": [
                "PowerClickEnterStage"
            ]
        },
        "PowerClickCavernTab": {
            "desc": "点击侵蚀隧洞分类",
            "recognition": "OCR",
            "expected": ["侵蚀隧洞"],
            "roi": [110, 220, 320, 450],
            "action": "Click",
            "post_delay": 1500,
            "next": [
                "PowerClickEnterStage"
            ]
        },
        "PowerClickStagnantTab": {
            "desc": "点击凝滞虚影分类",
            "recognition": "OCR",
            "expected": ["凝滞虚影"],
            "roi": [110, 220, 320, 450],
            "action": "Click",
            "post_delay": 1500,
            "next": [
                "PowerClickEnterStage"
            ]
        },
        "PowerClickEnterStage": {
            "desc": "点击右侧列表中的【进入】或【传送】",
            "recognition": "OCR",
            "expected": [
                "进入",
                "传送"
            ],
            "roi": [980, 240, 200, 420],
            "action": "Click",
            "post_delay": 3500,
            "focus": {
                "Node.Recognition.Succeeded": "已从生存索引进入副本关卡页"
            },
            "next": [
                "PowerStageReady",
                "PowerInStageDetail"
            ]
        },
        "PowerInStageDetail": {
            "desc": "在副本详情页识别并点击【挑战】",
            "recognition": "OCR",
            "expected": ["^挑战$"],
            "roi": [790, 615, 470, 85],
            "action": "Click",
            "target": [1030, 662],
            "post_delay": 2500,
            "next": [
                "PowerStageReady",
                "PowerInsufficientCancel"
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
            "next": [
                "PowerClickStartChallenge"
            ]
        },
        "PowerClickSupportBtn": {
            "desc": "点击【支援】按钮选择支援角色",
            "recognition": "OCR",
            "expected": ["支援"],
            "roi": [470, 540, 200, 150],
            "action": "Click",
            "post_delay": 2000,
            "max_hit": 1,
            "focus": {
                "Node.Recognition.Succeeded": "正在选择好友第一位支援角色..."
            },
            "next": [
                "PowerSelectFirstSupportSlot"
            ]
        },
        "PowerSelectFirstSupportSlot": {
            "desc": "点击列表第一位好友支援角色",
            "recognition": "DirectHit",
            "action": "Click",
            "target": [175, 230],
            "post_delay": 1000,
            "next": [
                "PowerConfirmSupportJoin"
            ]
        },
        "PowerConfirmSupportJoin": {
            "desc": "点击【入队】或【更换】确认支援角色加入",
            "recognition": "OCR",
            "expected": ["入队", "更换"],
            "roi": [880, 600, 380, 100],
            "action": "Click",
            "target": [1080, 660],
            "post_delay": 2000,
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
            "post_delay": 5000,
            "focus": {
                "Node.Recognition.Succeeded": "已点击【开始挑战】，进入战斗流程..."
            },
            "next": [
                "PowerBattleSuccess",
                "PowerInsufficientCancel",
                "PowerWaitBattleFinish"
            ]
        },
        "PowerWaitBattleFinish": {
            "desc": "等待战斗完成，循环点击普攻区触发位面饰品提取/凝滞虚影大世界开怪",
            "recognition": "DirectHit",
            "action": "Click",
            "target": [1110, 580],
            "post_delay": 3000,
            "next": [
                "PowerBattleSuccess",
                "PowerInsufficientCancel",
                "PowerWaitBattleFinish"
            ],
            "timeout": 300000
        },
        "PowerBattleSuccess": {
            "desc": "战斗结算成功，选择再来一次或退出关卡",
            "recognition": "OCR",
            "expected": [
                "挑战成功",
                "退出关卡",
                "再来一次"
            ],
            "roi": [250, 50, 780, 630],
            "action": "DoNothing",
            "next": [
                "PowerBattleAgain",
                "PowerBattleExit"
            ]
        },
        "PowerBattleAgain": {
            "desc": "点击【再来一次】继续刷本",
            "recognition": "OCR",
            "expected": ["再来一次"],
            "roi": [660, 595, 360, 80],
            "action": "Click",
            "target": [844, 634],
            "post_delay": 4000,
            "max_hit": 0,
            "focus": {
                "Node.Recognition.Succeeded": "继续挑战下一轮（再来一次）..."
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
            "post_delay": 4000,
            "focus": {
                "Node.Recognition.Succeeded": "已完成设定挑战次数，退出关卡"
            },
            "next": [
                "CheckMainWorld",
                "PowerCloseAfterExit",
                "PowerExitDomainToMainWorld"
            ]
        },
        "PowerExitDomainToMainWorld": {
            "desc": "若位面饰品提取退关后停留在关卡详情页，点击右上角关闭",
            "recognition": "TemplateMatch",
            "template": "phone_close.png",
            "roi": [1190, 5, 85, 80],
            "threshold": 0.72,
            "action": "Click",
            "target": [1235, 42],
            "post_delay": 2500,
            "next": [
                "CheckMainWorld",
                "PowerCloseAfterExit"
            ]
        },
        "PowerInsufficientCancel": {
            "desc": "开拓力不足弹窗，点击取消",
            "recognition": "OCR",
            "expected": [
                "开拓力补充",
                "取消"
            ],
            "roi": [300, 150, 680, 450],
            "action": "Click",
            "target": [500, 500],
            "post_delay": 1500,
            "focus": {
                "Node.Recognition.Succeeded": "开拓力不足，结束刷本"
            },
            "next": [
                "PowerBattleExit",
                "PowerDoneClose",
                "CheckMainWorld"
            ]
        },
        "PowerCloseAfterExit": {
            "desc": "若退关后仍有窗口，点击关闭",
            "recognition": "TemplateMatch",
            "template": "phone_close.png",
            "roi": [1190, 5, 85, 80],
            "threshold": 0.72,
            "action": "Click",
            "target": [1235, 42],
            "post_delay": 1500,
            "next": [
                "CheckMainWorld"
            ]
        },
        "PowerDoneClose": {
            "desc": "关闭并退回大世界",
            "action": "Click",
            "target": [1235, 42],
            "post_delay": 1500,
            "next": [
                "CheckMainWorld"
            ]
        }
    }
'''

content = content[:idx1] + new_power_pipeline + "\n" + content[idx2:]

# 3. Update interface.json and locales generation
old_interface_part = '''    interface_data["version"] = "v0.3.0"
    interface_data["title"] = "MaaHSR v0.3.0"'''
new_interface_part = '''    interface_data["version"] = "v0.4.0"
    interface_data["title"] = "MaaHSR v0.4.0"'''
assert old_interface_part in content
content = content.replace(old_interface_part, new_interface_part)

old_power_task_option = '''            "option": [
                "TrailblazeTarget"
            ]'''
new_power_task_option = '''            "option": [
                "TrailblazeTarget",
                "ChallengeCount",
                "UseSupport"
            ]'''
assert old_power_task_option in content
content = content.replace(old_power_task_option, new_power_task_option)

old_trailblaze_target_def = '''    interface_data["option"]["TrailblazeTarget"] = {
        "type": "select",
        "label": "$option.trailblaze_target.label",
        "default_case": "TargetDefault",
        "cases": [
            {
                "name": "TargetDefault",
                "label": "培养目标（默认推荐）",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "action": "Click",
                        "target": [270, 280]
                    }
                }
            },
            {
                "name": "CalyxGolden",
                "label": "拟造花萼（金）- 经验/信用点",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "action": "Click",
                        "target": [270, 482]
                    }
                }
            },
            {
                "name": "CalyxCrimson",
                "label": "拟造花萼（赤）- 行迹与光锥晋阶材料",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "action": "Click",
                        "target": [270, 582]
                    }
                }
            }
        ]
    }'''

new_trailblaze_target_def = '''    interface_data["option"]["TrailblazeTarget"] = {
        "type": "select",
        "label": "$option.trailblaze_target.label",
        "default_case": "BuildTargetMaterial",
        "cases": [
            {
                "name": "BuildTargetMaterial",
                "label": "培养目标 - 行迹/晋阶材料",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "action": "Click",
                        "target": [270, 280],
                        "post_delay": 1200,
                        "next": ["PowerClickEnterStage"]
                    }
                }
            },
            {
                "name": "BuildTargetOrnament",
                "label": "培养目标 - 推荐位面饰品（内圈）",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "action": "Click",
                        "target": [270, 382],
                        "post_delay": 1500,
                        "next": ["PowerClickEnterStage"]
                    }
                }
            },
            {
                "name": "BuildTargetRelic",
                "label": "培养目标 - 推荐隧洞遗器（外圈）",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "action": "Swipe",
                        "begin": [270, 580],
                        "end": [270, 240],
                        "duration": 600,
                        "post_delay": 1500,
                        "next": ["PowerClickCavernTab"]
                    }
                }
            },
            {
                "name": "CalyxGolden",
                "label": "拟造花萼（金）- 经验/信用点",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "action": "Click",
                        "target": [270, 482],
                        "post_delay": 1500,
                        "next": ["PowerClickEnterStage"]
                    }
                }
            },
            {
                "name": "CalyxCrimson",
                "label": "拟造花萼（赤）- 行迹材料",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "action": "Click",
                        "target": [270, 582],
                        "post_delay": 1500,
                        "next": ["PowerClickEnterStage"]
                    }
                }
            },
            {
                "name": "StagnantShadow",
                "label": "凝滞虚影 - 角色晋阶材料",
                "pipeline_override": {
                    "PowerSelectCategory": {
                        "action": "Swipe",
                        "begin": [270, 580],
                        "end": [270, 240],
                        "duration": 600,
                        "post_delay": 1500,
                        "next": ["PowerClickStagnantTab"]
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
                    "PowerBattleAgain": {
                        "max_hit": 0
                    }
                }
            },
            {
                "name": "Count2",
                "label": "2 次",
                "pipeline_override": {
                    "PowerBattleAgain": {
                        "max_hit": 1
                    }
                }
            },
            {
                "name": "Count3",
                "label": "3 次",
                "pipeline_override": {
                    "PowerBattleAgain": {
                        "max_hit": 2
                    }
                }
            },
            {
                "name": "Count4",
                "label": "4 次",
                "pipeline_override": {
                    "PowerBattleAgain": {
                        "max_hit": 3
                    }
                }
            },
            {
                "name": "Count6",
                "label": "6 次",
                "pipeline_override": {
                    "PowerBattleAgain": {
                        "max_hit": 5
                    }
                }
            },
            {
                "name": "CountAll",
                "label": "清空全部开拓力",
                "pipeline_override": {
                    "PowerBattleAgain": {
                        "max_hit": 99
                    }
                }
            }
        ]
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
                "label": "使用支援角色（选好友第一位）",
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
    }'''

assert old_trailblaze_target_def in content
content = content.replace(old_trailblaze_target_def, new_trailblaze_target_def)

old_locales_end = '''        "option.trailblaze_target.label": "开拓力消耗副本目标"'''
new_locales_end = '''        "option.trailblaze_target.label": "开拓力消耗副本目标",
        "option.challenge_count.label": "挑战次数",
        "option.use_support.label": "是否使用支援角色"'''
assert old_locales_end in content
content = content.replace(old_locales_end, new_locales_end)

content = content.replace("v0.3.0", "v0.4.0")

script_path.write_text(content, encoding="utf-8")
print("[OK] Successfully updated tools/build_hsr_resources.py")
