# MaaHSR — 《崩坏：星穹铁道》Android 原生后台虚拟屏自动化助手

<p align="center">
  <img src="assets/locales/icon.png" width="128" alt="MaaHSR Icon" />
</p>

<p align="center">
  <a href="https://github.com/Tspme1/MaaHSR/releases"><img src="https://img.shields.io/badge/release-v0.0.2-blue?style=flat-square" alt="Release v0.0.2" /></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License" /></a>
  <a href="https://github.com/MaaXYZ/MaaFramework"><img src="https://img.shields.io/badge/MaaFramework-v5.14.0-orange?style=flat-square" alt="MaaFramework v5.14.0" /></a>
</p>

**MaaHSR** 是基于 [MaaFramework v5.14.0](https://github.com/MaaXYZ/MaaFramework) 与 [MaaFwApp](https://github.com/Aliothmoon/MaaFwApp) 开发的《崩坏：星穹铁道》Android 原生自动化工具。通过 **Shizuku / Root** 特权后端在系统底层创建独立的 **`1280×720 @ 240dpi` 后台虚拟屏（VirtualDisplay）**，实现游戏在后台静音挂机清日常，前台手机可同时正常刷视频、聊天或锁屏息屏运行。

---

## 一、核心特性与架构亮点

### 1. 后台 720P 虚拟屏零干扰运行
- **独立虚拟屏幕**：通过 Shizuku 特权进程在后台挂载 `1280×720`（16:9）虚拟屏幕，将《崩坏：星穹铁道》（支持官服 `com.miHoYo.hkrpg` 与 B 站服 `com.miHoYo.hkrpg.bilibili`）投放到虚拟屏内运行。
- **画中画（PiP）与屏保模式**：支持小窗实时预览虚拟屏画面、触控透传操作，以及极低功耗 OLED 黑屏屏保模式。
- **全程零漏音后台静音**：
  - 采用 Android `AppOpsManager` 多通道音频管控（`OP_PLAY_AUDIO = 28` + `OP_TAKE_AUDIO_FOCUS = 32`）结合 `cmd appops set --uid` 双重静音锁。
  - 在关闭虚拟屏或强停游戏前，预先维持静音锁并先执行 `am force-stop`，彻底消除退出瞬间 1 秒声音外漏问题。

### 2. 日常一条龙全流程自动化（`v0.0.2`）
安装 APK 后默认内置 **「日常一条龙」** 配置预设，开箱即用，包含以下 6 大核心任务模块：

| 顺序 | 任务名称 | 功能与自动化细节 |
| :--- | :--- | :--- |
| **1** | **1. 启动游戏** | 自动在虚拟屏启动星铁客户端（支持官服 / B 服切换），识别并点击「点击进入/开始游戏」，自动领取「列车补给凭证（月卡）」并进入大世界。 |
| **2** | **2. 每日委托** | 自动打开左上角手机菜单 → 委托，一键领取已完成委托奖励并自动点击「再次派遣」（支持设置仅领取或领取并重派）。 |
| **3** | **3. 邮件一键领取** | 自动打开手机右侧栏邮箱，一键领取全部附件邮件奖励并退回大世界。 |
| **4** | **4. 消耗开拓力** | 全功能体力刷取引擎（支持培养目标内圈/外圈、拟造花萼金/赤、凝滞虚影、历战余响、自定义次数拆轮、自动快捷补充体力、好友支援及助燃券速刷）。 |
| **5** | **5. 每日实训** | 自动打开星际和平指南，**强制先切回第一页「每日实训」标签**（防止因实训完成默认停留在第二页），逐一领取实训任务活跃度并点满顶部 500 活跃度奖励。 |
| **6** | **6. 无名勋礼** | 自动进入无名勋礼，先切换至任务页一键领取经验并处理升级弹窗，再切换至奖励页点击右下角「一键领取」收取等级奖励。 |
| **附** | **虚拟屏后台保活与调试抓图** | 辅助保活与 `1280×720` 现场截图采集工具。 |

### 3. 「消耗开拓力」深度定制能力
1. **副本目标精准导航（保留标准括号标注）**：
   - `培养目标 - 推荐位面饰品（内圈）`：自动定位生存索引「饰品提取」并兼容跳过队内确认页直接进入战斗。
   - `培养目标 - 推荐隧洞遗器（外圈）`：自动滑动定位「侵蚀隧洞」并进入推荐遗器关卡。
   - `拟造花萼（金）- 经验/信用点`：支持二级下拉框选择具体副本（**回忆之蕾 - 角色经验材料** / **以太之蕾 - 光锥经验材料** / **藏珍之蕾 - 信用点**）。
   - `拟造花萼（赤）- 行迹材料`、`凝滞虚影 - 角色晋阶材料`、`历战余响 - 周本高阶材料`。
2. **自定义刷取次数与自动分轮（`RunPlanBuilder` 编译器）**：
   - 除预设的 `1 / 2 / 3 / 4 / 6 / 最大次数` 外，支持**「自定义刷取次数」**自由输入任意正整数 $N$。
   - 自动根据副本单轮上限（历战余响 $M=3$、位面饰品/侵蚀隧洞 $M=6$、拟造花萼 $M=24$）将总次数 $N$ 拆分为多轮 pipeline 节点序列自动循环刷取。
   - 使用 `count_plus.png` 模版匹配精准定位「+」号按钮，解决位面饰品（内圈）与普通副本「+」号坐标差异导致无法拉满 6 次的问题。
3. **自动开启「快捷补充」与体力不足智能中止**：
   - 进入关卡准备页后自动检测「快捷补充」开关（兼容普通副本 `[1216, 519]` 与位面饰品 `[1210, 583]` 双位置），关闭时自动打开，实现后备开拓力无缝续刷。
   - 若体力与后备开拓力均耗尽弹出补充确认框，自动识别并点击「取消」，在运行日志中输出 **「体力不足，已停止刷取并退回大世界」**，随后安全退回大世界继续执行后续任务。
4. **好友支援角色（支持指定第 1 / 2 / 3 / 4 位序号） & 助燃券速刷闭环**：
   - 支援列表精准点击指定的好友支援槽位（默认第 1 位 `[215, 220]`，支持第 1~4 位任意自选）并点击入队确认。
   - 助燃券快速战斗支持：点击「快速战斗」→ 弹窗点击「确认」→ 等待结算完成点击「关闭」→ 点击右上角「×」安全退回大世界。

### 4. 任务与日志交互优化
- **任务页与添加任务职责分离**：
  - 主页（任务列表）每行右侧的**铅笔编辑图标**直接打开该任务的**设置项编辑弹窗（`TaskOptionSheet`）**，所有日常任务均支持点开编辑设置。
  - **自定义修改任务名称**功能移入**「添加任务」**抽屉界面，选定任务时可点击右侧铅笔图标修改自定义名称。
- **运行日志自动弹出与底部快捷关闭**：
  - 点击「开始行动」后自动展开实时运行日志面板，面板底部常驻全宽「关闭」按钮，方便随时切回任务列表。
- **通知栏与实时更新进度条**：
  - 专为 Android 状态栏与 OriginOS 实时活动通知定制 `ic_notification_maahsr` 镂空剪影小图标 + 彩色星穹铁道大图标 + 进度条白色圆球游标（`ic_progress_tracker`）。

### 5. GitHub 双轨 OTA 更新系统与版本更新通知
- **版本更新通知与变更日志**：详见根目录专用文档 [`CHANGELOG.md`](./CHANGELOG.md)。MaaHSR 客户端每次检测到新版本时，将自动解析并展示对应版本的更新说明弹窗。
- **更新源地址**：`https://github.com/Tspme1/MaaHSR`（默认使用 GitHub 源，已屏蔽 Mirror 酱选项并开启启动自动检查更新）。
- **双轨智能识别**：
  - **全量版本更新（APK）**：当 GitHub Release 包含 `MaaHSR-v<version>-arm64-v8a.apk` 时，自动下载并拉起系统安装器升级。
  - **轻量资源热更新（ZIP）**：当 GitHub Release 仅上传 `MaaHSR-resource-v<version>.zip`（约 480 KB，不含 18MB OCR 模型）时，APP 自动下载并在应用内增量覆盖解压重载，**无需重新安装 APK 即可秒级更新流水线与截图模版**。
- **版本号体系**：正式版采用标准三段式 `vX.Y.Z`（当前版本为 `v0.0.2`），测试/热更构建支持四段式 `vX.Y.Z.W`（如 `v0.0.1.1`，由 `UpdateVersion.kt` 自动转换为高优先级补丁号参与比较）。

---

## 二、目录结构说明

```text
MaaHSR/
├── CHANGELOG.md                       # 版本变更日志与客户端更新通知数据源
├── assets/
│   ├── interface.json                 # MaaFramework 项目定义、任务、选项与默认预设配置
│   ├── locales/
│   │   ├── zh_cn.json                 # 简体中文界面文案字典
│   │   └── icon.png                   # MaaHSR 应用图标
│   └── resource/
│       ├── image/                     # 1280x720 标准模版切图 (.png)
│       ├── model/ocr/                 # PP-OCRv4 离线文字识别模型 (det.onnx / rec.onnx)
│       └── pipeline/                  # 6 大日常任务流水线定义 (.json)
├── Android/
│   ├── profile.yaml                   # Android 客户端构建配置 (包名 com.aliothmoon.maafw.maahsr)
│   └── MaaFwApp/                      # Android 客户端源码工程 (Kotlin / Jetpack Compose)
├── tools/
│   ├── build_hsr_resources.py         # 一键切图、流水线 JSON 与 interface.json 生成脚本
│   ├── build_resource_pack.py         # 轻量级 OTA 资源热更新包 (.zip) 打包脚本
│   └── capture_720p.py                # 720P 虚拟屏截图采集工具
└── LICENSE                            # MIT 开源许可证与第三方开源组件声明
```

---

## 三、构建与发布命令速查

### 1. 生成流水线与轻量资源热更新包
```powershell
python tools/build_hsr_resources.py
python tools/build_resource_pack.py --version v0.0.2
```

### 2. 编译 Android APK（内置完整 `pi.zip` 资源包）
```powershell
cd Android/MaaFwApp
./gradlew.bat :app:assembleDebug -Ppi.archive=true
```

---

## 四、致谢（Acknowledgements）

本项目的诞生与完善离不开以下优秀开源项目的奠基与启发，特此致以诚挚感谢：

- **[MaaAssistantArknights (MAA)](https://github.com/MaaAssistantArknights/MaaAssistantArknights)**：感谢 MAA 团队开创的图像识别与自动化设计范式，以及成熟可靠的分体式 OTA 更新设计理念。
- **[MaaFramework](https://github.com/MaaXYZ/MaaFramework)**：感谢 MaaXYZ 团队提供的跨平台次世代视觉自动化流水线引擎（Pipeline V2 / TemplateMatch / PP-OCRv4）。
- **[MaaFwApp](https://github.com/Aliothmoon/MaaFwApp)**：感谢 [@Aliothmoon](https://github.com/Aliothmoon) 打造的 Android 原生 MaaFramework 宿主工程与 Shizuku 后台虚拟屏（VirtualDisplay）架构。
- **[Shizuku](https://github.com/RikkaApps/Shizuku)**：感谢 RikkaApps 提供的 Android 无 Root 系统 API 跨进程调用框架。
- **[PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)**：感谢飞桨团队提供的轻量级高精度离线中文 OCR 识别模型。

---

## 五、开源许可（License）

本项目资源配置与自动化流水线脚本基于 **[MIT License](./LICENSE)** 开源（完整许可证正文见仓库根目录 [`LICENSE`](./LICENSE) 文件）：

```text
MIT License

Copyright (c) 2026 Tspme1 (MaaHSR Contributors)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

> **补充说明**：本项目仅用于学习与技术交流，通过视觉识别模拟正常触控操作，绝不修改任何游戏内存、客户端代码或网络封包。请合理使用自动化工具。
