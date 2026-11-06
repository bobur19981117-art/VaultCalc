import 'package:flutter/services.dart';
import '../models/apk_item.dart';

class ApkScannerService {
  static const MethodChannel _channel = MethodChannel('uz.qoriqchi.apkguard/scanner');

  static Future<List<ApkItem>> scanAllApks() async {
    try {
      final List<dynamic>? result = await _channel.invokeMethod('scanAllApks');
      if (result == null) return [];
      return result.map((item) => ApkItem.fromMap(Map<dynamic, dynamic>.from(item))).toList();
    } on MissingPluginException {
      // Fallback preview mode for non-Android / demo testing
      return _getDemoApks();
    } catch (e) {
      rethrow;
    }
  }

  static Future<ApkItem?> analyzeSingleApk(String path) async {
    try {
      final Map<dynamic, dynamic>? result =
          await _channel.invokeMethod('analyzeSingleApk', {'path': path});
      if (result == null) return null;
      return ApkItem.fromMap(result);
    } catch (e) {
      return null;
    }
  }

  static Future<List<InstalledAppAudit>> getInstalledAppsAudit() async {
    try {
      final List<dynamic>? result = await _channel.invokeMethod('getInstalledAppsAudit');
      if (result == null) return [];
      return result
          .map((item) => InstalledAppAudit.fromMap(Map<dynamic, dynamic>.from(item)))
          .toList();
    } on MissingPluginException {
      return _getDemoInstalledAudit();
    } catch (e) {
      return [];
    }
  }

  static Future<bool> deleteApk(String path) async {
    try {
      final bool? success = await _channel.invokeMethod('deleteApk', {'path': path});
      return success ?? false;
    } catch (e) {
      return false;
    }
  }

  static Future<bool> installApk(String path) async {
    try {
      final bool? success = await _channel.invokeMethod('installApk', {'path': path});
      return success ?? false;
    } catch (e) {
      return false;
    }
  }

  static Future<bool> startWatcherService() async {
    try {
      final bool? success = await _channel.invokeMethod('startWatcherService');
      return success ?? false;
    } catch (e) {
      return false;
    }
  }

  static Future<bool> stopWatcherService() async {
    try {
      final bool? success = await _channel.invokeMethod('stopWatcherService');
      return success ?? false;
    } catch (e) {
      return false;
    }
  }

  static Future<bool> isWatcherRunning() async {
    try {
      final bool? running = await _channel.invokeMethod('isWatcherRunning');
      return running ?? false;
    } catch (e) {
      return false;
    }
  }

  static Future<void> openAccessibilitySettings() async {
    try {
      await _channel.invokeMethod('openAccessibilitySettings');
    } catch (_) {}
  }

  static Future<bool> isAccessibilityEnabled() async {
    try {
      final bool? enabled = await _channel.invokeMethod('isAccessibilityEnabled');
      return enabled ?? false;
    } catch (_) {
      return false;
    }
  }

  static Future<void> requestStorageManagePermission() async {
    try {
      await _channel.invokeMethod('requestStorageManagePermission');
    } catch (_) {}
  }

  // Demo fallback for immediate preview
  static List<ApkItem> _getDemoApks() {
    return [
      ApkItem(
        fileName: 'Online_Bank_Bonus_2026.apk',
        filePath: '/storage/emulated/0/Download/Telegram/Online_Bank_Bonus_2026.apk',
        fileSize: 4200000,
        lastModified: DateTime.now().subtract(const Duration(minutes: 15)),
        isCorrupt: false,
        appName: 'Online Bank Bonus',
        packageName: 'com.fake.uz.banking',
        versionName: '1.0.4',
        versionCode: 4,
        permissions: [
          'android.permission.RECEIVE_SMS',
          'android.permission.READ_SMS',
          'android.permission.BIND_ACCESSIBILITY_SERVICE',
          'android.permission.SYSTEM_ALERT_WINDOW',
          'android.permission.INTERNET',
          'android.permission.READ_CONTACTS'
        ],
        criticalCount: 4,
        highCount: 1,
        riskLevel: RiskLevel.critical,
        riskScore: 98,
      ),
      ApkItem(
        fileName: 'Telegram_Premium_Free.apk',
        filePath: '/storage/emulated/0/Download/Telegram_Premium_Free.apk',
        fileSize: 18500000,
        lastModified: DateTime.now().subtract(const Duration(hours: 3)),
        isCorrupt: false,
        appName: 'TG Premium Mod',
        packageName: 'org.tg.mod.fake',
        versionName: '9.8.0',
        versionCode: 2901,
        permissions: [
          'android.permission.READ_CONTACTS',
          'android.permission.RECORD_AUDIO',
          'android.permission.ACCESS_FINE_LOCATION',
          'android.permission.INTERNET'
        ],
        criticalCount: 0,
        highCount: 3,
        riskLevel: RiskLevel.high,
        riskScore: 50,
      ),
      ApkItem(
        fileName: 'Calculator_Pro_Clean.apk',
        filePath: '/storage/emulated/0/Download/Calculator_Pro_Clean.apk',
        fileSize: 2100000,
        lastModified: DateTime.now().subtract(const Duration(days: 1)),
        isCorrupt: false,
        appName: 'Oddiy Kalkulyator',
        packageName: 'com.simple.calculator',
        versionName: '2.1',
        versionCode: 21,
        permissions: [
          'android.permission.VIBRATE',
        ],
        criticalCount: 0,
        highCount: 0,
        riskLevel: RiskLevel.safe,
        riskScore: 0,
      )
    ];
  }

  static List<InstalledAppAudit> _getDemoInstalledAudit() {
    return [
      InstalledAppAudit(
        appName: 'Shubhali Tezkor Kassa',
        packageName: 'com.fastkassa.app',
        versionName: '1.2.0',
        permissions: [
          'android.permission.RECEIVE_SMS',
          'android.permission.READ_SMS',
          'android.permission.INTERNET'
        ],
        criticalPermissions: [
          'android.permission.RECEIVE_SMS',
          'android.permission.READ_SMS'
        ],
      )
    ];
  }
}
