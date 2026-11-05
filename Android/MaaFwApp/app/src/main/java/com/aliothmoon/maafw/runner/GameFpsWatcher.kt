package com.aliothmoon.maafw.runner

import com.aliothmoon.maafw.MaaDispatchers
import com.aliothmoon.maafw.R
import com.aliothmoon.maafw.i18n.uiTextOf
import com.aliothmoon.maafw.privileged.PrivilegedServicePort
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.math.roundToInt

interface GameFpsReader {
    /** null = 远端未监控或无法读取 */
    suspend fun readGameFps(): Float?
}

class RemoteGameFpsReader(private val servicePort: PrivilegedServicePort) : GameFpsReader {
    override suspend fun readGameFps(): Float? = withContext(MaaDispatchers.IO) {
        runCatching { servicePort.serviceOrNull()?.getGameFps() }
            .getOrNull()
            ?.takeIf { it >= 0f }
    }
}

/** 后台运行期轮询游戏帧率：供预览显示，并在持续低帧率时写运行日志 */
class GameFpsWatcher(
    private val reader: GameFpsReader,
    private val journal: RunJournal,
    private val scope: CoroutineScope,
    private val fpsLimit: () -> Int = { 60 },
) {

    private val _fps = MutableStateFlow<Float?>(null)
    val fps: StateFlow<Float?> = _fps.asStateFlow()
    private var job: Job? = null

    @Synchronized
    fun start(executionId: String) {
        stop()
        // 每轮自带判定器：stop 不等旧一轮退出，它可能还在判定，共用一个会被两轮同时改
        // 用户开启了后台低帧率限制（15/20/30 FPS）时，按上限等比下调告警阈值，避免误报低帧率
        val limit = fpsLimit()
        val advisor = if (limit in 1..59) {
            GameFpsAdvisor(
                lowThreshold = (limit * 0.5f).coerceAtMost(10f),
                degradedThreshold = (limit * 0.7f).coerceAtMost(15f),
            )
        } else {
            GameFpsAdvisor()
        }
        job = scope.launch {
            while (isActive) {
                delay(POLL_INTERVAL_MS)
                pollOnce(executionId, advisor)
            }
        }
    }

    @Synchronized
    fun stop() {
        job?.cancel()
        job = null
        _fps.value = null
    }

    internal suspend fun pollOnce(executionId: String, advisor: GameFpsAdvisor) {
        val value = reader.readGameFps()
        // 读数取消不掉（binder 调用），已停的一轮读回来直接丢：不把旧帧率写回已清空的状态，也不再判定
        currentCoroutineContext().ensureActive()
        _fps.value = value
        advisor.onSample(value ?: 0f)?.let { advice ->
            val fps = advice.medianFps.roundToInt()
            when (advice.level) {
                GameFpsAdvisor.Level.LOW ->
                    journal.note(executionId, RunNote.Error, uiTextOf(R.string.run_log_game_fps_low, fps))

                GameFpsAdvisor.Level.DEGRADED ->
                    journal.note(executionId, RunNote.Warning, uiTextOf(R.string.run_log_game_fps_degraded, fps))
            }
        }
    }

    private companion object {
        const val POLL_INTERVAL_MS = 1_000L
    }
}
