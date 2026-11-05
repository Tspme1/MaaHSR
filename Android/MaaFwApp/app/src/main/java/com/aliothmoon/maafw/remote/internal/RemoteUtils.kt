package com.aliothmoon.maafw.remote.internal

import android.content.pm.IPackageManager
import android.os.IDeviceIdleController
import com.aliothmoon.maafw.third.FakeContext
import com.aliothmoon.maafw.third.Ln
import com.android.internal.app.IAppOpsService
import rikka.shizuku.SystemServiceHelper
import java.util.concurrent.ConcurrentHashMap

object RemoteUtils {
    private const val TAG = "RemoteUtils"

    private val uidCache = ConcurrentHashMap<String, Int>()

    val packageManager: IPackageManager by lazy {
        val binder = SystemServiceHelper.getSystemService("package")
        IPackageManager.Stub.asInterface(binder)
    }

    val appOpsService: IAppOpsService by lazy {
        val binder = SystemServiceHelper.getSystemService("appops")
        IAppOpsService.Stub.asInterface(binder)
    }

    val deviceIdleController: IDeviceIdleController by lazy {
        val binder = SystemServiceHelper.getSystemService("deviceidle")
        IDeviceIdleController.Stub.asInterface(binder)
    }

    fun getAppUid(packageName: String): Int {
        uidCache[packageName]?.let { return it }
        return runCatching {
            val uid = FakeContext.get().packageManager.getApplicationInfo(packageName, 0).uid
            if (uid >= 0) {
                uidCache[packageName] = uid
            }
            uid
        }.getOrElse {
            uidCache[packageName] = -1
            -1
        }
    }

    fun shellExec(command: String): Int {
        val process = Runtime.getRuntime().exec(arrayOf("sh", "-c", command))
        val exitCode = process.waitFor()
        Ln.i("$TAG: $command -> exitCode=$exitCode")
        return exitCode
    }
}
