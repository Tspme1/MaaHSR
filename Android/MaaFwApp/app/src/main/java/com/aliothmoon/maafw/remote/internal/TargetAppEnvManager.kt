package com.aliothmoon.maafw.remote.internal

import android.app.AppOpsManager
import android.os.Build
import com.aliothmoon.maafw.bridge.NativeBridgeLib
import com.aliothmoon.maafw.constant.DefaultDisplayConfig
import com.aliothmoon.maafw.third.Ln
import java.util.concurrent.ConcurrentHashMap

/**
 * 统一管理目标应用在虚拟屏运行期间的环境策略：
 * 1. 启动/运行期全时段零漏音静音（基于 [AppOpsHelper] 的 `PLAY_AUDIO` + `TAKE_AUDIO_FOCUS` ignore 与 80ms 高频 Binder IPlayer.setVolume(0f) 守护线程）
 * 2. 后台低帧率限制（基于 [NativeBridgeLib.setCaptureFpsLimit] 与 Android 12+ `cmd game set --fps`）
 */
object TargetAppEnvManager {
    private const val TAG = "TargetAppEnvManager"

    private val KNOWN_GAME_PACKAGES = listOf("com.miHoYo.hkrpg", "com.miHoYo.hkrpg.bilibili")

    @Volatile
    private var muteEnabled: Boolean = true

    @Volatile
    private var backgroundFpsLimit: Int = 30

    @Volatile
    private var currentTargetPackage: String? = null

    @Volatile
    private var muteGuardThread: Thread? = null

    private val mutedPackages = ConcurrentHashMap.newKeySet<String>()
    private val fpsLimitedPackages = ConcurrentHashMap.newKeySet<String>()

    /** 快速获取已知/当前目标包名（不调耗时的 probeDisplay，供 80ms 高频音频守护循环使用） */
    private fun resolveFastTargetPackages(): List<String> {
        val pkgs = linkedSetOf<String>()
        currentTargetPackage?.takeIf { it.isNotBlank() }?.let { pkgs.add(it) }
        AppWatchdog.targetPackage?.takeIf { it.isNotBlank() }?.let { pkgs.add(it) }
        pkgs.addAll(mutedPackages)
        for (pkg in KNOWN_GAME_PACKAGES) {
            if (RemoteUtils.getAppUid(pkg) >= 0) {
                pkgs.add(pkg)
            }
        }
        return pkgs.toList()
    }

    fun resolveActiveOrKnownPackages(): List<String> {
        val pkgs = linkedSetOf<String>()
        pkgs.addAll(resolveFastTargetPackages())
        val displayId = VirtualDisplayManager.getDisplayId()
        if (displayId != DefaultDisplayConfig.DISPLAY_NONE) {
            val top = (ActivityUtils.probeDisplay(displayId) as? ActivityUtils.DisplayOccupancy.Occupied)?.topPackage
            if (!top.isNullOrBlank()) {
                pkgs.add(top)
            }
        }
        return pkgs.toList()
    }

    @JvmStatic
    @Synchronized
    fun setMuteEnabled(enabled: Boolean) {
        val prev = muteEnabled
        muteEnabled = enabled
        Ln.i("$TAG: setMuteEnabled($enabled)")
        if (enabled) {
            resolveFastTargetPackages().forEach { applyMute(it) }
            ensureMuteGuardStarted()
        } else if (prev || mutedPackages.isNotEmpty()) {
            stopMuteGuard()
            restoreMutedPackages()
        }
    }

    @JvmStatic
    fun isMuteEnabled(): Boolean = muteEnabled

    @JvmStatic
    @Synchronized
    fun ensureMutedIfOnVirtualDisplay() {
        if (!muteEnabled) return
        Ln.i("$TAG: ensureMutedIfOnVirtualDisplay")
        resolveFastTargetPackages().forEach { applyMute(it) }
        ensureMuteGuardStarted()
    }

    @Synchronized
    private fun ensureMuteGuardStarted() {
        if (!muteEnabled) return
        if (muteGuardThread?.isAlive == true) return

        muteGuardThread = Thread({
            Ln.i("$TAG: high-frequency (80ms) mute guard daemon started")
            var tickCount = 0
            while (muteEnabled) {
                try {
                    val pkgs = resolveFastTargetPackages()
                    for (pkg in pkgs) {
                        val uid = RemoteUtils.getAppUid(pkg)
                        if (uid >= 0) {
                            // 每次循环（80ms）通过缓存的 Binder 立即将目标游戏所有新创建的 AudioTrack/AAudio/Wwise IPlayer 音量压为 0
                            AppOpsHelper.setActivePlayersVolume(uid, pkg, true)
                            // 每约 800ms 校验一次 AppOps 状态并补发 Binder ignore
                            if (tickCount % 10 == 0) {
                                AppOpsHelper.setPlayAudioModeFastBinder(pkg, uid, AppOpsManager.MODE_IGNORED)
                            }
                        }
                    }
                    tickCount++
                    Thread.sleep(80)
                } catch (ignored: InterruptedException) {
                    break
                } catch (e: Throwable) {
                    Ln.w("$TAG: error in mute guard loop: ${e.message}")
                    try { Thread.sleep(200) } catch (_: InterruptedException) { break }
                }
            }
            Ln.i("$TAG: mute guard daemon exited")
        }, "target-mute-guard").apply {
            isDaemon = true
            priority = Thread.MAX_PRIORITY
            start()
        }
    }

    @Synchronized
    private fun stopMuteGuard() {
        muteGuardThread?.interrupt()
        muteGuardThread = null
    }

    @JvmStatic
    @Synchronized
    fun setBackgroundFpsLimit(fps: Int) {
        val normalized = if (fps <= 0 || fps >= 60) 60 else fps.coerceIn(10, 60)
        backgroundFpsLimit = normalized
        Ln.i("$TAG: setBackgroundFpsLimit($normalized)")
        if (NativeBridgeLib.LOADED) {
            runCatching { NativeBridgeLib.setCaptureFpsLimit(normalized) }
                .onFailure { Ln.w("$TAG: NativeBridgeLib.setCaptureFpsLimit failed: ${it.message}") }
        }
        val pkg = currentTargetPackage ?: AppWatchdog.targetPackage
        if (!pkg.isNullOrBlank()) {
            if (normalized < 60) {
                applyGameModeFps(pkg, normalized)
            } else {
                restoreFpsPackages()
            }
        }
    }

    @JvmStatic
    fun getBackgroundFpsLimit(): Int = backgroundFpsLimit

    @JvmStatic
    fun onRunStarted() {
        Ln.i("$TAG: onRunStarted")
        if (NativeBridgeLib.LOADED) {
            runCatching { NativeBridgeLib.setCaptureFpsLimit(backgroundFpsLimit) }
                .onFailure { Ln.w("$TAG: NativeBridgeLib.setCaptureFpsLimit failed: ${it.message}") }
        }
        resolveFastTargetPackages().forEach { onTargetAppActive(it) }
        if (muteEnabled) {
            ensureMuteGuardStarted()
        }
    }

    /**
     * 当目标应用在虚拟屏被拉起或被看门狗捕获时调用
     */
    @JvmStatic
    fun onTargetAppActive(rawPackageSpec: String) {
        val pkg = ActivityUtils.packageNameOf(rawPackageSpec).takeIf { it.isNotBlank() } ?: return
        currentTargetPackage = pkg
        if (muteEnabled) {
            applyMute(pkg)
            ensureMuteGuardStarted()
        }
        val fps = backgroundFpsLimit
        if (fps in 10..59 && !fpsLimitedPackages.contains(pkg)) {
            applyGameModeFps(pkg, fps)
        }
    }

    private fun applyMute(pkg: String) {
        runCatching {
            val uid = RemoteUtils.getAppUid(pkg)
            if (uid >= 0) {
                val ok = AppOpsHelper.setPlayAudioMode(pkg, uid, AppOpsManager.MODE_IGNORED)
                mutedPackages.add(pkg)
                Ln.i("$TAG: muted target app $pkg (uid=$uid, ok=$ok)")
            } else {
                RemoteUtils.shellExec("cmd appops set --uid $pkg PLAY_AUDIO ignore; cmd appops set $pkg PLAY_AUDIO ignore; cmd appops set $pkg TAKE_AUDIO_FOCUS ignore; appops set $pkg PLAY_AUDIO ignore")
                mutedPackages.add(pkg)
                Ln.i("$TAG: muted target app $pkg via shell")
            }
        }.onFailure {
            Ln.w("$TAG: applyMute failed for $pkg: ${it.message}")
        }
    }

    private fun applyGameModeFps(pkg: String, fps: Int) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return
        fpsLimitedPackages.add(pkg)
        Thread {
            runCatching {
                RemoteUtils.shellExec("cmd game set --fps $fps $pkg")
            }.onFailure {
                Ln.w("$TAG: applyGameModeFps failed for $pkg: ${it.message}")
            }
        }.apply {
            name = "target-fps-limiter"
            isDaemon = true
            start()
        }
    }

    @JvmStatic
    @Synchronized
    fun restoreMutedPackages() {
        stopMuteGuard()
        val targets = linkedSetOf<String>()
        targets.addAll(mutedPackages)
        currentTargetPackage?.let(targets::add)
        AppWatchdog.targetPackage?.let(targets::add)
        for (pkg in KNOWN_GAME_PACKAGES) {
            if (RemoteUtils.getAppUid(pkg) >= 0) {
                targets.add(pkg)
            }
        }
        mutedPackages.clear()

        for (pkg in targets) {
            if (pkg.isBlank()) continue
            runCatching {
                AppOpsHelper.resetPackage(pkg)
                Ln.i("$TAG: restored audio for $pkg")
            }.onFailure {
                Ln.w("$TAG: restore audio failed for $pkg: ${it.message}")
            }
        }
    }

    @JvmStatic
    @Synchronized
    fun restoreFpsPackages() {
        val targets = fpsLimitedPackages.toList()
        fpsLimitedPackages.clear()
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return
        for (pkg in targets) {
            if (pkg.isBlank()) continue
            runCatching {
                RemoteUtils.shellExec("cmd game reset $pkg")
            }.onFailure {
                Ln.w("$TAG: restore game fps failed for $pkg: ${it.message}")
            }
        }
    }

    @JvmStatic
    @Synchronized
    fun restoreAll() {
        stopMuteGuard()
        if (!muteEnabled) {
            restoreMutedPackages()
        }
        restoreFpsPackages()
        currentTargetPackage = null
    }
}
