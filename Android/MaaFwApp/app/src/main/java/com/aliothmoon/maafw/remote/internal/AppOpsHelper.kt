package com.aliothmoon.maafw.remote.internal

import android.app.AppOpsManager
import com.aliothmoon.maafw.third.Ln
import rikka.shizuku.SystemServiceHelper
import java.lang.reflect.Method

object AppOpsHelper {
    private const val TAG = "AppOpsHelper"

    private const val OP_PLAY_AUDIO = 28
    private const val OP_TAKE_AUDIO_FOCUS = 32

    private val audioService: Any? by lazy {
        runCatching {
            val binder = SystemServiceHelper.getSystemService("audio") ?: return@runCatching null
            val stubClass = Class.forName("android.media.IAudioService\$Stub")
            val asInterface = stubClass.getMethod("asInterface", android.os.IBinder::class.java)
            asInterface.invoke(null, binder)
        }.onFailure {
            Ln.w("$TAG: failed to bind IAudioService: ${it.message}")
        }.getOrNull()
    }

    private val getActivePlaybackConfigsMethod: Method? by lazy {
        runCatching {
            audioService?.javaClass?.getMethod("getActivePlaybackConfigurations")
        }.getOrNull()
    }

    private val setUidModeMethod: Method? by lazy {
        runCatching {
            RemoteUtils.appOpsService.javaClass.getMethod(
                "setUidMode",
                Int::class.javaPrimitiveType,
                Int::class.javaPrimitiveType,
                Int::class.javaPrimitiveType,
            )
        }.getOrNull()
    }

    /** 读取当前生效 mode；读取失败返回 -1 */
    fun checkPlayAudioMode(packageName: String, uid: Int): Int = runCatching {
        RemoteUtils.appOpsService.checkOperation(OP_PLAY_AUDIO, uid, packageName)
    }.getOrElse {
        Ln.w("$TAG: checkOperation failed for $packageName: ${it.message}")
        -1
    }

    /** 通过 Binder 快速设置 PLAY_AUDIO 与 TAKE_AUDIO_FOCUS */
    fun setPlayAudioModeFastBinder(packageName: String, uid: Int, mode: Int) {
        if (uid < 0) return
        runCatching {
            RemoteUtils.appOpsService.setMode(OP_PLAY_AUDIO, uid, packageName, mode)
            RemoteUtils.appOpsService.setMode(OP_TAKE_AUDIO_FOCUS, uid, packageName, mode)
        }
        runCatching {
            setUidModeMethod?.invoke(RemoteUtils.appOpsService, OP_PLAY_AUDIO, uid, mode)
            setUidModeMethod?.invoke(RemoteUtils.appOpsService, OP_TAKE_AUDIO_FOCUS, uid, mode)
        }
        if (mode == AppOpsManager.MODE_IGNORED) {
            setActivePlayersVolume(uid, packageName, true)
        }
    }

    /** 设置 PLAY_AUDIO mode 并校验实际生效 */
    fun setPlayAudioMode(packageName: String, uid: Int, mode: Int): Boolean {
        if (uid >= 0) {
            setPlayAudioModeFastBinder(packageName, uid, mode)
        }

        val arg = if (mode == AppOpsManager.MODE_ALLOWED) "allow" else "ignore"
        Thread {
            runCatching {
                RemoteUtils.shellExec(
                    "cmd appops set --uid $packageName PLAY_AUDIO $arg; " +
                        "cmd appops set $packageName PLAY_AUDIO $arg; " +
                        "cmd appops set --uid $packageName TAKE_AUDIO_FOCUS $arg; " +
                        "cmd appops set $packageName TAKE_AUDIO_FOCUS $arg"
                )
            }
        }.apply {
            name = "appops-shell-mute"
            isDaemon = true
            start()
        }

        return if (uid >= 0) checkPlayAudioMode(packageName, uid) == mode else true
    }

    /**
     * 将该包 AppOps 恢复为系统默认（`appops reset <package>`）。
     * 成功条件：PLAY_AUDIO 不再是 IGNORED；读不到 mode 时以 shell exitCode 为准。
     */
    fun resetPackage(packageName: String): Boolean {
        val uid = RemoteUtils.getAppUid(packageName)
        if (uid >= 0) {
            setPlayAudioModeFastBinder(packageName, uid, AppOpsManager.MODE_ALLOWED)
        }
        val exitCode = RemoteUtils.shellExec(
            "cmd appops reset $packageName; " +
                "cmd appops set --uid $packageName PLAY_AUDIO allow; " +
                "cmd appops set $packageName PLAY_AUDIO allow; " +
                "cmd appops set --uid $packageName TAKE_AUDIO_FOCUS allow; " +
                "cmd appops set $packageName TAKE_AUDIO_FOCUS allow; " +
                "appops reset $packageName"
        )
        if (uid < 0) {
            return exitCode == 0
        }
        val mode = checkPlayAudioMode(packageName, uid)
        if (mode < 0) {
            return exitCode == 0
        }
        return isPlayAudioRestored(mode)
    }

    fun setActivePlayersVolume(uid: Int, packageName: String, muted: Boolean) {
        if (uid < 0) return
        val service = audioService ?: return
        val getConfigs = getActivePlaybackConfigsMethod ?: return
        runCatching {
            val configs = getConfigs.invoke(service) as? List<*> ?: return@runCatching
            val targetVolume = if (muted) 0f else 1f
            for (config in configs) {
                if (config == null) continue
                val configUid = runCatching {
                    config.javaClass.getMethod("getClientUid").invoke(config) as? Int
                }.getOrNull() ?: runCatching {
                    val f = config.javaClass.getDeclaredField("mClientUid").apply { isAccessible = true }
                    f.getInt(config)
                }.getOrNull()

                if (configUid == uid) {
                    val playerProxy = runCatching {
                        config.javaClass.getMethod("getPlayerProxy").invoke(config)
                    }.getOrNull() ?: runCatching {
                        config.javaClass.getMethod("getIPlayer").invoke(config)
                    }.getOrNull() ?: runCatching {
                        val f = config.javaClass.getDeclaredField("mIPlayer").apply { isAccessible = true }
                        f.get(config)
                    }.getOrNull()

                    if (playerProxy != null) {
                        runCatching {
                            val setVol = playerProxy.javaClass.getMethod("setVolume", Float::class.javaPrimitiveType)
                            setVol.invoke(playerProxy, targetVolume)
                        }
                    }
                }
            }
        }
    }

    internal fun isPlayAudioRestored(mode: Int): Boolean =
        mode >= 0 && mode != AppOpsManager.MODE_IGNORED
}
