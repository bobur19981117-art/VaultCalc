package uz.qoriqchi.apkguard

import android.accessibilityservice.AccessibilityService
import android.os.Handler
import android.os.Looper
import android.view.accessibility.AccessibilityEvent
import android.widget.Toast

class GuardAccessibilityService : AccessibilityService() {

    private val installerPackages = setOf(
        "com.android.packageinstaller",
        "com.google.android.packageinstaller",
        "com.samsung.android.packageinstaller",
        "com.miui.packageinstaller"
    )

    private var lastToastTime = 0L

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return

        val pkgName = event.packageName?.toString() ?: return
        if (installerPackages.contains(pkgName)) {
            val now = System.currentTimeMillis()
            if (now - lastToastTime > 5000) {
                lastToastTime = now
                Handler(Looper.getMainLooper()).post {
                    Toast.makeText(
                        applicationContext,
                        "🛡 APK Qo'riqchi: Diqqat! Yangi ilova o'rnatilmoqda. Ruxsatlarni tekshirganingizga ishonch hosil qiling!",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }
        }
    }

    override fun onInterrupt() {
        // Handle interruption
    }
}
