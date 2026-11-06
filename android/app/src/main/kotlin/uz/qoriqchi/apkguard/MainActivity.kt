package uz.qoriqchi.apkguard

import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.Settings
import android.view.accessibility.AccessibilityManager
import androidx.core.content.FileProvider
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File
import kotlin.concurrent.thread

class MainActivity : FlutterActivity() {

    private val CHANNEL = "uz.qoriqchi.apkguard/scanner"
    private var isWatcherRunning = false

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "scanAllApks" -> {
                    thread {
                        try {
                            val apks = ApkAnalyzer.scanAllApkFiles(applicationContext)
                            runOnUiThread {
                                result.success(apks)
                            }
                        } catch (e: Exception) {
                            runOnUiThread {
                                result.error("SCAN_ERROR", e.localizedMessage, null)
                            }
                        }
                    }
                }
                "analyzeSingleApk" -> {
                    val path = call.argument<String>("path")
                    if (path != null) {
                        thread {
                            val analysis = ApkAnalyzer.analyzeApk(applicationContext, path)
                            runOnUiThread {
                                result.success(analysis)
                            }
                        }
                    } else {
                        result.error("INVALID_PATH", "Path is required", null)
                    }
                }
                "getInstalledAppsAudit" -> {
                    thread {
                        val audit = ApkAnalyzer.getInstalledAppsAudit(applicationContext)
                        runOnUiThread {
                            result.success(audit)
                        }
                    }
                }
                "deleteApk" -> {
                    val path = call.argument<String>("path")
                    if (path != null) {
                        val file = File(path)
                        val deleted = if (file.exists()) file.delete() else false
                        result.success(deleted)
                    } else {
                        result.error("INVALID_PATH", "Path is null", null)
                    }
                }
                "installApk" -> {
                    val path = call.argument<String>("path")
                    if (path != null) {
                        val file = File(path)
                        if (file.exists()) {
                            val intent = Intent(Intent.ACTION_VIEW).apply {
                                val uri: Uri = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                                    FileProvider.getUriForFile(
                                        this@MainActivity,
                                        "${applicationContext.packageName}.fileprovider",
                                        file
                                    )
                                } else {
                                    Uri.fromFile(file)
                                }
                                setDataAndType(uri, "application/vnd.android.package-archive")
                                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_GRANT_READ_URI_PERMISSION
                            }
                            startActivity(intent)
                            result.success(true)
                        } else {
                            result.error("NOT_FOUND", "Fayl topilmadi", null)
                        }
                    } else {
                        result.error("INVALID_PATH", "Path is null", null)
                    }
                }
                "startWatcherService" -> {
                    try {
                        val intent = Intent(this, FileWatcherService::class.java)
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            startForegroundService(intent)
                        } else {
                            startService(intent)
                        }
                        isWatcherRunning = true
                        result.success(true)
                    } catch (e: Exception) {
                        result.error("SERVICE_ERROR", e.localizedMessage, null)
                    }
                }
                "stopWatcherService" -> {
                    val intent = Intent(this, FileWatcherService::class.java)
                    stopService(intent)
                    isWatcherRunning = false
                    result.success(true)
                }
                "isWatcherRunning" -> {
                    result.success(isWatcherRunning)
                }
                "openAccessibilitySettings" -> {
                    val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                    startActivity(intent)
                    result.success(true)
                }
                "isAccessibilityEnabled" -> {
                    val am = getSystemService(Context.ACCESSIBILITY_SERVICE) as AccessibilityManager
                    val enabledServices = am.getEnabledAccessibilityServiceList(AccessibilityServiceInfo.FEEDBACK_ALL_MASK)
                    val isEnabled = enabledServices.any {
                        it.resolveInfo.serviceInfo.packageName == packageName
                    }
                    result.success(isEnabled)
                }
                "requestStorageManagePermission" -> {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                        if (!Environment.isExternalStorageManager()) {
                            val intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION).apply {
                                data = Uri.parse("package:$packageName")
                            }
                            startActivity(intent)
                        }
                    }
                    result.success(true)
                }
                else -> result.notImplemented()
            }
        }
    }
}
