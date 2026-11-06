package uz.qoriqchi.apkguard

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Environment
import android.os.FileObserver
import android.os.IBinder
import androidx.core.app.NotificationCompat
import java.io.File

class FileWatcherService : Service() {

    private val observers = mutableListOf<FileObserver>()
    private val CHANNEL_ID = "apk_guard_realtime_channel"
    private val NOTIF_ID = 7788

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
        val foregroundNotification = createForegroundNotification()
        startForeground(NOTIF_ID, foregroundNotification)
        startWatchingDirectories()
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "APK Qo'riqchi Xizmati",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Yangi yuklangan APK fayllar bo'yicha tezkor ogohlantirishlar"
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun createForegroundNotification(): Notification {
        val launchIntent = packageManager.getLaunchIntentForPackage(packageName)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            launchIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("APK Qo'riqchi Pro Faol")
            .setContentText("Yuklamalar va messenjerlar real-vaqtda himoyalanmoqda")
            .setSmallIcon(android.R.drawable.ic_lock_idle_lock)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }

    private fun startWatchingDirectories() {
        val paths = listOf(
            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)?.absolutePath,
            File(Environment.getExternalStorageDirectory(), "Download/Telegram").absolutePath,
            File(Environment.getExternalStorageDirectory(), "Telegram/Telegram Documents").absolutePath
        )

        for (path in paths) {
            if (path != null && File(path).exists()) {
                val observer = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    object : FileObserver(File(path), CREATE or CLOSE_WRITE) {
                        override fun onEvent(event: Int, fileName: String?) {
                            handleFileEvent(path, fileName)
                        }
                    }
                } else {
                    @Suppress("DEPRECATION")
                    object : FileObserver(path, CREATE or CLOSE_WRITE) {
                        override fun onEvent(event: Int, fileName: String?) {
                            handleFileEvent(path, fileName)
                        }
                    }
                }
                observer.startWatching()
                observers.add(observer)
            }
        }
    }

    private fun handleFileEvent(parentDir: String, fileName: String?) {
        if (fileName != null && fileName.endsWith(".apk", ignoreCase = true)) {
            val fullPath = File(parentDir, fileName).absolutePath
            showApkWarningNotification(fileName, fullPath)
        }
    }

    private fun showApkWarningNotification(fileName: String, filePath: String) {
        val launchIntent = packageManager.getLaunchIntentForPackage(packageName)?.apply {
            putExtra("action", "scan_apk")
            putExtra("filePath", filePath)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }

        val pendingIntent = PendingIntent.getActivity(
            this,
            System.currentTimeMillis().toInt(),
            launchIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        val warningNotification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("⚠️ Yangi APK yuklandi: $fileName")
            .setContentText("Ilovani ochishdan oldin APK Qo'riqchi bilan tekshiring!")
            .setSmallIcon(android.R.drawable.stat_sys_warning)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()

        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify((System.currentTimeMillis() % 10000).toInt(), warningNotification)
    }

    override fun onDestroy() {
        for (observer in observers) {
            observer.stopWatching()
        }
        observers.clear()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
