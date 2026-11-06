import 'package:flutter/material.dart';

enum RiskLevel {
  critical,
  high,
  medium,
  safe;

  static RiskLevel fromString(String val) {
    switch (val.toUpperCase()) {
      case 'CRITICAL':
        return RiskLevel.critical;
      case 'HIGH':
        return RiskLevel.high;
      case 'MEDIUM':
        return RiskLevel.medium;
      case 'SAFE':
      default:
        return RiskLevel.safe;
    }
  }

  String get labelUz {
    switch (this) {
      case RiskLevel.critical:
        return "O'TA XAVFLI";
      case RiskLevel.high:
        return "YUQORI XAVF";
      case RiskLevel.medium:
        return "O'RTACHA XAVF";
      case RiskLevel.safe:
        return "XAVFSIZ";
    }
  }

  Color get color {
    switch (this) {
      case RiskLevel.critical:
        return const Color(0xFFFF3366);
      case RiskLevel.high:
        return const Color(0xFFFF9900);
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
        return Icons.warning_amber_rounded;
      case RiskLevel.medium:
        return Icons.info_outline_rounded;
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
