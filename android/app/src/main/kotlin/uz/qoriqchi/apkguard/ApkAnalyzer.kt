package uz.qoriqchi.apkguard

import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageInfo
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.Drawable
import android.os.Build
import android.os.Environment
import android.util.Base64
import java.io.ByteArrayOutputStream
import java.io.File

object ApkAnalyzer {

    // Critical permissions commonly abused by Android banking Trojans and spyware
    val CRITICAL_PERMISSIONS = setOf(
        "android.permission.RECEIVE_SMS",
        "android.permission.READ_SMS",
        "android.permission.SEND_SMS",
        "android.permission.BIND_ACCESSIBILITY_SERVICE",
        "android.permission.SYSTEM_ALERT_WINDOW",
        "android.permission.REQUEST_INSTALL_PACKAGES",
        "android.permission.PROCESS_OUTGOING_CALLS",
        "android.permission.USE_SIP"
    )

    // High risk permissions
    val HIGH_RISK_PERMISSIONS = setOf(
        "android.permission.READ_CONTACTS",
        "android.permission.WRITE_CONTACTS",
        "android.permission.RECORD_AUDIO",
        "android.permission.CAMERA",
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.READ_CALL_LOG",
        "android.permission.WRITE_CALL_LOG",
        "android.permission.READ_PHONE_STATE",
        "android.permission.CALL_PHONE"
    )

    fun scanAllApkFiles(context: Context): List<Map<String, Any?>> {
        val results = mutableListOf<Map<String, Any?>>()
        val searchDirs = listOf(
            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
            File(Environment.getExternalStorageDirectory(), "Download/Telegram"),
            File(Environment.getExternalStorageDirectory(), "Telegram/Telegram Documents"),
            File(Environment.getExternalStorageDirectory(), "Android/media/org.telegram.messenger/Telegram/Telegram Documents"),
            File(Environment.getExternalStorageDirectory(), "WhatsApp/Media/WhatsApp Documents"),
            Environment.getExternalStorageDirectory()
        )

        val visitedPaths = HashSet<String>()

        for (dir in searchDirs) {
            if (dir != null && dir.exists() && dir.canRead()) {
                scanDirectoryRecursively(dir, 0, 3, visitedPaths) { file ->
                    try {
                        val analysis = analyzeApk(context, file.absolutePath)
                        if (analysis != null) {
                            results.add(analysis)
                        }
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }
                }
            }
        }

        return results
    }

    private fun scanDirectoryRecursively(
        dir: File,
        currentDepth: Int,
        maxDepth: Int,
        visited: HashSet<String>,
        onApkFound: (File) -> Unit
    ) {
        if (currentDepth > maxDepth || !dir.exists() || !dir.canRead()) return

        val files = dir.listFiles() ?: return
        for (file in files) {
            val path = file.absolutePath
            if (visited.contains(path)) continue
            visited.add(path)

            if (file.isDirectory && !file.name.startsWith(".")) {
                // Avoid scanning non-user folders like Android/data which may be restricted
                if (!file.name.equals("data", ignoreCase = true) || !path.contains("Android/data")) {
                    scanDirectoryRecursively(file, currentDepth + 1, maxDepth, visited, onApkFound)
                }
            } else if (file.isFile && file.name.endsWith(".apk", ignoreCase = true)) {
                onApkFound(file)
            }
        }
    }

    fun analyzeApk(context: Context, apkPath: String): Map<String, Any?>? {
        val file = File(apkPath)
        if (!file.exists()) return null

        val pm = context.packageManager
        val flags = PackageManager.GET_PERMISSIONS or PackageManager.GET_META_DATA
        val packageInfo: PackageInfo? = try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                pm.getPackageArchiveInfo(apkPath, PackageManager.PackageInfoFlags.of(flags.toLong()))
            } else {
                @Suppress("DEPRECATION")
                pm.getPackageArchiveInfo(apkPath, flags)
            }
        } catch (e: Exception) {
            null
        }

        if (packageInfo == null) {
            // Corrupt or encrypted APK
            return mapOf(
                "fileName" to file.name,
                "filePath" to file.absolutePath,
                "fileSize" to file.length(),
                "lastModified" to file.lastModified(),
                "isCorrupt" to true,
                "appName" to file.name,
                "packageName" to "Noma'lum / Shikastlangan",
                "versionName" to "-",
                "versionCode" to 0,
                "permissions" to emptyList<String>(),
                "criticalCount" to 0,
                "highCount" to 0,
                "riskLevel" to "CRITICAL",
                "riskScore" to 100,
                "iconBase64" to null
            )
        }

        packageInfo.applicationInfo?.sourceDir = apkPath
        packageInfo.applicationInfo?.publicSourceDir = apkPath

        val appName = try {
            packageInfo.applicationInfo?.loadLabel(pm)?.toString() ?: file.name
        } catch (e: Exception) {
            file.name
        }

        val iconBase64 = try {
            val drawable = packageInfo.applicationInfo?.loadIcon(pm)
            drawableToBase64(drawable)
        } catch (e: Exception) {
            null
        }

        val permissions = packageInfo.requestedPermissions?.toList() ?: emptyList()
        val criticals = permissions.filter { CRITICAL_PERMISSIONS.contains(it) }
        val highs = permissions.filter { HIGH_RISK_PERMISSIONS.contains(it) }

        // Calculate risk score: 0 (Safe) to 100 (Extremely Dangerous)
        var score = (criticals.size * 30) + (highs.size * 10)
        if (permissions.contains("android.permission.RECEIVE_SMS") && permissions.contains("android.permission.INTERNET")) {
            score += 25 // SMS Stealer combo
        }
        if (permissions.contains("android.permission.BIND_ACCESSIBILITY_SERVICE")) {
            score += 35 // Screen grabber / accessibility trojan
        }
        if (score > 100) score = 100

        val riskLevel = when {
            score >= 60 -> "CRITICAL"
            score >= 30 -> "HIGH"
            score >= 10 -> "MEDIUM"
            else -> "SAFE"
        }

        return mapOf(
            "fileName" to file.name,
            "filePath" to file.absolutePath,
            "fileSize" to file.length(),
            "lastModified" to file.lastModified(),
            "isCorrupt" to false,
            "appName" to appName,
            "packageName" to (packageInfo.packageName ?: "Noma'lum"),
            "versionName" to (packageInfo.versionName ?: "1.0"),
            "versionCode" to (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) packageInfo.longVersionCode else @Suppress("DEPRECATION") packageInfo.versionCode.toLong()),
            "permissions" to permissions,
            "criticalCount" to criticals.size,
            "highCount" to highs.size,
            "riskLevel" to riskLevel,
            "riskScore" to score,
            "iconBase64" to iconBase64
        )
    }

    fun getInstalledAppsAudit(context: Context): List<Map<String, Any?>> {
        val pm = context.packageManager
        val installedApps = pm.getInstalledPackages(PackageManager.GET_PERMISSIONS)
        val auditList = mutableListOf<Map<String, Any?>>()

        for (pkg in installedApps) {
            // Filter non-system apps or apps with critical permissions
            val isSystem = (pkg.applicationInfo?.flags ?: 0) and ApplicationInfo.FLAG_SYSTEM != 0
            val permissions = pkg.requestedPermissions?.toList() ?: emptyList()
            val criticals = permissions.filter { CRITICAL_PERMISSIONS.contains(it) }

            if (criticals.isNotEmpty() && !isSystem) {
                val appName = try {
                    pkg.applicationInfo?.loadLabel(pm)?.toString() ?: pkg.packageName
                } catch (e: Exception) {
                    pkg.packageName
                }

                val iconBase64 = try {
                    val drawable = pkg.applicationInfo?.loadIcon(pm)
                    drawableToBase64(drawable)
                } catch (e: Exception) {
                    null
                }

                auditList.add(
                    mapOf(
                        "appName" to appName,
                        "packageName" to pkg.packageName,
                        "versionName" to (pkg.versionName ?: "1.0"),
                        "permissions" to permissions,
                        "criticalPermissions" to criticals,
                        "iconBase64" to iconBase64
                    )
                )
            }
        }

        return auditList
    }

    private fun drawableToBase64(drawable: Drawable?): String? {
        if (drawable == null) return null
        val bitmap = if (drawable is BitmapDrawable && drawable.bitmap != null) {
            drawable.bitmap
        } else {
            val width = if (drawable.intrinsicWidth > 0) drawable.intrinsicWidth else 96
            val height = if (drawable.intrinsicHeight > 0) drawable.intrinsicHeight else 96
            val bm = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
            val canvas = Canvas(bm)
            drawable.setBounds(0, 0, canvas.width, canvas.height)
            drawable.draw(canvas)
            bm
        }

        val outputStream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.PNG, 85, outputStream)
        return Base64.encodeToString(outputStream.toByteArray(), Base64.NO_WRAP)
    }
}
