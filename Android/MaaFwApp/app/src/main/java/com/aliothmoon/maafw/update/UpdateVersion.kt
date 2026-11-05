package com.aliothmoon.maafw.update

import io.github.z4kn4fein.semver.Version
import io.github.z4kn4fein.semver.toVersionOrNull

/** 版本解析、比较与预发布判定一律按 SemVer 2.0.0，不自定义规则 */
internal object UpdateVersion {

    private val FOUR_SEGMENT_VERSION = Regex("""^[vV]?(\d+)\.(\d+)\.(\d+)\.(\d+)(.*)$""")

    /** 宽松模式：支持正式版 3 段式 vX.Y.Z 与测试版 4 段式 vX.Y.Z.x（自动映射为 SemVer 预发布版 X.Y.Z-beta.x） */
    fun parse(raw: String): Version? {
        val trimmed = raw.trim()
        val normalized = FOUR_SEGMENT_VERSION.matchEntire(trimmed)?.let { m ->
            "${m.groupValues[1]}.${m.groupValues[2]}.${m.groupValues[3]}-beta.${m.groupValues[4]}${m.groupValues[5]}"
        } ?: trimmed
        return normalized.toVersionOrNull(strict = false)
    }
}

/** stable 只收正式版；beta 收任意预发布（SemVer 不区分 alpha / beta / rc） */
internal fun Version.allowedFor(channel: UpdateChannel): Boolean = when (channel) {
    UpdateChannel.STABLE -> !isPreRelease
    UpdateChannel.BETA -> true
}
