#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

script_path = Path("tools/build_hsr_resources.py")
content = script_path.read_text(encoding="utf-8")

old_roi = '"roi": [980, 240, 200, 420],\n            "action": "Click",'
new_roi = '"roi": [980, 240, 200, 420],\n            "order_by": "Vertical",\n            "index": 0,\n            "action": "Click",'
assert old_roi in content, "old_roi not found"
content = content.replace(old_roi, new_roi)

old_challenge = '"expected": ["^挑战$"],'
new_challenge = '"expected": ["挑战"],'
assert old_challenge in content, "old_challenge not found"
content = content.replace(old_challenge, new_challenge)

script_path.write_text(content, encoding="utf-8")
print("[OK] Updated tools/build_hsr_resources.py successfully!")
