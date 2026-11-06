import 'package:flutter/material.dart';

enum ApkCategory {
  xavfli,
  shubhali,
  xavfsiz;

  static ApkCategory fromRiskLevel(RiskLevel level) {
    switch (level) {
      case RiskLevel.critical:
        return ApkCategory.xavfli;
      case RiskLevel.high:
      case RiskLevel.medium:
        return ApkCategory.shubhali;
      case RiskLevel.safe:
        return ApkCategory.xavfsiz;
    }
  }

  String get labelUz {
    switch (this) {
      case ApkCategory.xavfli:
        return "Xavfli";
      case ApkCategory.shubhali:
        return "Shubhali";
      case ApkCategory.xavfsiz:
        return "Xavfsiz";
    }
  }

  Color get color {
    switch (this) {
      case ApkCategory.xavfli:
        return const Color(0xFFFF3366);
      case ApkCategory.shubhali:
        return const Color(0xFFFFB300);
      case ApkCategory.xavfsiz:
        return const Color(0xFF00E676);
    }
  }

  IconData get icon {
    switch (this) {
      case ApkCategory.xavfli:
        return Icons.gpp_bad_rounded;
      case ApkCategory.shubhali:
        return Icons.warning_amber_rounded;
      case ApkCategory.xavfsiz:
        return Icons.verified_user_rounded;
    }
  }

  String get descriptionUz {
    switch (this) {
      case ApkCategory.xavfli:
        return "Bank, SMS, ekran va shaxsiy parollarni o'g'irlash xavfi mavjud.";
      case ApkCategory.shubhali:
        return "Kontaktlar, kamera yoki joylashuv kabi sezgir ruxsatlarni talab qiladi.";
      case ApkCategory.xavfsiz:
        return "Hech qanday zararli yoki shubhali ruxsatlar aniqlanmadi.";
    }
  }
}

enum RiskLevel {
  critical,
  high,
  medium,
  safe;

  static RiskLevel fromString(String val) {
    switch (val.toUpperCase()) {
      case 'CRITICAL':
      case 'XAVFLI':
        return RiskLevel.critical;
      case 'HIGH':
      case 'SHUBHALI':
        return RiskLevel.high;
      case 'MEDIUM':
        return RiskLevel.medium;
      case 'SAFE':
      case 'XAVFSIZ':
      default:
        return RiskLevel.safe;
    }
  }

  String get labelUz {
    switch (this) {
      case RiskLevel.critical:
        return "XAVFLI";
      case RiskLevel.high:
        return "SHUBHALI";
      case RiskLevel.medium:
        return "SHUBHALI";
      case RiskLevel.safe:
        return "XAVFSIZ";
    }
  }

  Color get color {
    switch (this) {
      case RiskLevel.critical:
        return const Color(0xFFFF3366);
      case RiskLevel.high:
        return const Color(0xFFFFB300);
      case RiskLevel.medium:
        return const Color(0xFFFFCC00);
      case RiskLevel.safe:
        return const Color(0xFF00E676);
    }
  }

  IconData get icon {
    switch (this) {
      case RiskLevel.critical:
        return Icons.gpp_bad_rounded;
      case RiskLevel.high:
      case RiskLevel.medium:
        return Icons.warning_amber_rounded;
      case RiskLevel.safe:
        return Icons.verified_user_rounded;
    }
  }
}

class ApkItem {
  final String fileName;
  final String filePath;
  final int fileSize;
  final DateTime lastModified;
  final bool isCorrupt;
  final String appName;
  final String packageName;
  final String versionName;
  final int versionCode;
  final List<String> permissions;
  final int criticalCount;
  final int highCount;
  final RiskLevel riskLevel;
  final int riskScore;
  final String? iconBase64;

  ApkItem({
    required this.fileName,
    required this.filePath,
    required this.fileSize,
    required this.lastModified,
    required this.isCorrupt,
    required this.appName,
    required this.packageName,
    required this.versionName,
    required this.versionCode,
    required this.permissions,
    required this.criticalCount,
    required this.highCount,
    required this.riskLevel,
    required this.riskScore,
    this.iconBase64,
  });

  ApkCategory get category {
    if (criticalCount > 0 || riskLevel == RiskLevel.critical || riskScore >= 50) {
      return ApkCategory.xavfli;
    } else if (highCount > 0 || riskLevel == RiskLevel.high || riskLevel == RiskLevel.medium || riskScore >= 15) {
      return ApkCategory.shubhali;
    } else {
      return ApkCategory.xavfsiz;
    }
  }

  factory ApkItem.fromMap(Map<dynamic, dynamic> map) {
    return ApkItem(
      fileName: map['fileName'] ?? '',
      filePath: map['filePath'] ?? '',
      fileSize: (map['fileSize'] as num?)?.toInt() ?? 0,
      lastModified: DateTime.fromMillisecondsSinceEpoch(
        (map['lastModified'] as num?)?.toInt() ?? DateTime.now().millisecondsSinceEpoch,
      ),
      isCorrupt: map['isCorrupt'] ?? false,
      appName: map['appName'] ?? (map['fileName'] ?? 'Noma\'lum'),
      packageName: map['packageName'] ?? '',
      versionName: map['versionName'] ?? '1.0',
      versionCode: (map['versionCode'] as num?)?.toInt() ?? 1,
      permissions: List<String>.from(map['permissions'] ?? []),
      criticalCount: (map['criticalCount'] as num?)?.toInt() ?? 0,
      highCount: (map['highCount'] as num?)?.toInt() ?? 0,
      riskLevel: RiskLevel.fromString(map['riskLevel']?.toString() ?? 'SAFE'),
      riskScore: (map['riskScore'] as num?)?.toInt() ?? 0,
      iconBase64: map['iconBase64'],
    );
  }

  String get formattedSize {
    if (fileSize < 1024) return '$fileSize B';
    if (fileSize < 1024 * 1024) return '${(fileSize / 1024).toStringAsFixed(1)} KB';
    return '${(fileSize / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}

class InstalledAppAudit {
  final String appName;
  final String packageName;
  final String versionName;
  final List<String> permissions;
  final List<String> criticalPermissions;
  final String? iconBase64;

  InstalledAppAudit({
    required this.appName,
    required this.packageName,
    required this.versionName,
    required this.permissions,
    required this.criticalPermissions,
    this.iconBase64,
  });

  ApkCategory get category {
    if (criticalPermissions.isNotEmpty) {
      return ApkCategory.xavfli;
    } else if (permissions.any((p) => p.contains("CONTACTS") || p.contains("CAMERA") || p.contains("RECORD_AUDIO") || p.contains("LOCATION"))) {
      return ApkCategory.shubhali;
    } else {
      return ApkCategory.xavfsiz;
    }
  }

  factory InstalledAppAudit.fromMap(Map<dynamic, dynamic> map) {
    return InstalledAppAudit(
      appName: map['appName'] ?? '',
      packageName: map['packageName'] ?? '',
      versionName: map['versionName'] ?? '',
      permissions: List<String>.from(map['permissions'] ?? []),
      criticalPermissions: List<String>.from(map['criticalPermissions'] ?? []),
      iconBase64: map['iconBase64'],
    );
  }
}
