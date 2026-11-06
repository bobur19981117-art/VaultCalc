import 'dart:convert';
import 'package:flutter/material.dart';
import '../models/apk_item.dart';
import '../services/apk_scanner_service.dart';
import '../services/risk_evaluator.dart';
import '../widgets/risk_badge.dart';

class ApkDetailScreen extends StatefulWidget {
  final ApkItem apk;
  final VoidCallback? onDeleted;

  const ApkDetailScreen({
    super.key,
    required this.apk,
    this.onDeleted,
  });

  @override
  State<ApkDetailScreen> createState() => _ApkDetailScreenState();
}

class _ApkDetailScreenState extends State<ApkDetailScreen> {
  bool _isProcessing = false;

  void _confirmDelete() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E222D),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Row(
          children: [
            Icon(Icons.delete_forever_rounded, color: Color(0xFFFF3366)),
            SizedBox(width: 8),
            Text('Faylni o\'chirish', style: TextStyle(color: Colors.white, fontSize: 18)),
          ],
        ),
        content: Text(
          '"${widget.apk.fileName}" faylini xotiradan butunlay o\'chirmoqchimisiz?',
          style: const TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Bekor qilish', style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFFF3366),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: () async {
              Navigator.pop(ctx);
              setState(() => _isProcessing = true);
              final deleted = await ApkScannerService.deleteApk(widget.apk.filePath);
              setState(() => _isProcessing = false);

              if (mounted) {
                if (deleted) {
                  widget.onDeleted?.call();
                  Navigator.pop(context, true);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      backgroundColor: Color(0xFF00E676),
                      content: Text('Zararli APK fayl muvaffaqiyatli o\'chirildi!'),
                    ),
                  );
                } else {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      backgroundColor: Colors.red,
                      content: Text('Xatolik: Faylni o\'chirib bo\'lmadi.'),
                    ),
                  );
                }
              }
            },
            child: const Text('O\'chirish', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _installApk() {
    if (widget.apk.riskLevel == RiskLevel.critical) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          backgroundColor: const Color(0xFF261418),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: const Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: Color(0xFFFF3366)),
              SizedBox(width: 8),
              Text('OGOHLANTIRISH!', style: TextStyle(color: Color(0xFFFF3366), fontWeight: FontWeight.bold)),
            ],
          ),
          content: const Text(
            'Ushbu ilovada xavfli ruxsatlar (SMS, ekran nazorati) mavjud! O\'rnatish orqali bank hisoblaringizni xavf ostiga qo\'yishingiz mumkin. Baribir o\'rnatmoqchimisiz?',
            style: TextStyle(color: Colors.white70),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('To\'xtatish (Tavsiya)', style: TextStyle(color: Colors.white)),
            ),
            TextButton(
              onPressed: () {
                Navigator.pop(ctx);
                ApkScannerService.installApk(widget.apk.filePath);
              },
              child: const Text('Baribir davom etish', style: TextStyle(color: Colors.redAccent)),
            ),
          ],
        ),
      );
    } else {
      ApkScannerService.installApk(widget.apk.filePath);
    }
  }

  @override
  Widget build(BuildContext context) {
    final apk = widget.apk;
    final isCritical = apk.riskLevel == RiskLevel.critical;

    return Scaffold(
      backgroundColor: const Color(0xFF0F1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161922),
        elevation: 0,
        title: const Text('APK Tahlil Tafsiloti', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline_rounded, color: Color(0xFFFF3366)),
            onPressed: _isProcessing ? null : _confirmDelete,
            tooltip: "O'chirish",
          ),
        ],
      ),
      body: _isProcessing
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF)))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Header Card
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1B1F2A),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: isCritical
                          ? const Color(0xFFFF3366).withOpacity(0.4)
                          : Colors.white.withOpacity(0.06),
                    ),
                  ),
                  child: Row(
                    children: [
                      // App Icon
                      Container(
                        width: 64,
                        height: 64,
                        decoration: BoxDecoration(
                          color: const Color(0xFF262C3A),
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: apk.iconBase64 != null
                            ? ClipRRect(
                                borderRadius: BorderRadius.circular(16),
                                child: Image.memory(
                                  base64Decode(apk.iconBase64!),
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, __, ___) => const Icon(
                                    Icons.android_rounded,
                                    size: 36,
                                    color: Color(0xFF00E676),
                                  ),
                                ),
                              )
                            : Icon(
                                Icons.android_rounded,
                                size: 36,
                                color: apk.riskLevel.color,
                              ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              apk.appName,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              apk.packageName,
                              style: const TextStyle(color: Colors.grey, fontSize: 12),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                RiskBadge(category: apk.category, compact: true),
                                const SizedBox(width: 8),
                                Text(
                                  'v${apk.versionName}',
                                  style: const TextStyle(color: Colors.white54, fontSize: 12),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // Risk Score Gauge Banner
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        apk.riskLevel.color.withOpacity(0.2),
                        const Color(0xFF1B1F2A),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: apk.riskLevel.color.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 58,
                        height: 58,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: apk.riskLevel.color.withOpacity(0.15),
                          border: Border.all(color: apk.riskLevel.color, width: 2),
                        ),
                        child: Center(
                          child: Text(
                            '${apk.riskScore}',
                            style: TextStyle(
                              color: apk.riskLevel.color,
                              fontWeight: FontWeight.bold,
                              fontSize: 18,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Xavf darajasi: ${apk.riskLevel.labelUz}',
                              style: TextStyle(
                                color: apk.riskLevel.color,
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              isCritical
                                  ? 'Ushbu ilovada kiberxavfsizlikka tahdid soluvchi xususiyatlar aniqlandi!'
                                  : 'Ilova me\'yordagi ruxsatlar bilan ishlaydi.',
                              style: const TextStyle(color: Colors.white70, fontSize: 12),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // Technical Info Card
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1B1F2A),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    children: [
                      _buildInfoRow('Fayl hajmi', apk.formattedSize),
                      const Divider(color: Colors.white10),
                      _buildInfoRow('Versiya kodi', '${apk.versionCode}'),
                      const Divider(color: Colors.white10),
                      _buildInfoRow('Fayl yo\'li', apk.filePath, isPath: true),
                    ],
                  ),
                ),

                const SizedBox(height: 20),

                // Permissions Section
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Talab qilingan ruxsatlar',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: const Color(0xFF262C3A),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '${apk.permissions.length} ta',
                        style: const TextStyle(color: Colors.white70, fontSize: 12),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                if (apk.permissions.isEmpty)
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1B1F2A),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Center(
                      child: Text(
                        'Hech qanday maxsus ruxsat talab qilinmagan (Toza).',
                        style: TextStyle(color: Colors.grey),
                      ),
                    ),
                  )
                else
                  ...apk.permissions.map((perm) {
                    final detail = RiskEvaluator.getDetail(perm);
                    final isPermCritical = detail.severity == 'CRITICAL';
                    final isPermHigh = detail.severity == 'HIGH';

                    final permColor = isPermCritical
                        ? const Color(0xFFFF3366)
                        : (isPermHigh ? const Color(0xFFFF9900) : Colors.white60);

                    return Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1B1F2A),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: isPermCritical
                              ? const Color(0xFFFF3366).withOpacity(0.3)
                              : Colors.white.withOpacity(0.04),
                        ),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: permColor.withOpacity(0.12),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Icon(detail.icon, color: permColor, size: 20),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Expanded(
                                      child: Text(
                                        detail.titleUz,
                                        style: TextStyle(
                                          color: permColor,
                                          fontSize: 14,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                    if (isPermCritical)
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFFFF3366).withOpacity(0.2),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: const Text(
                                          'TAHLIKA',
                                          style: TextStyle(
                                            color: Color(0xFFFF3366),
                                            fontSize: 9,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  detail.descriptionUz,
                                  style: const TextStyle(color: Colors.white70, fontSize: 12),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  perm,
                                  style: const TextStyle(color: Colors.grey, fontSize: 10),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  }),

                const SizedBox(height: 30),

                // Action Buttons Bottom
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: const Color(0xFFFF3366),
                          side: const BorderSide(color: Color(0xFFFF3366)),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        ),
                        onPressed: _confirmDelete,
                        icon: const Icon(Icons.delete_forever_rounded),
                        label: const Text('Faylni o\'chirish', style: TextStyle(fontWeight: FontWeight.bold)),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: isCritical ? const Color(0xFF262C3A) : const Color(0xFF00E676),
                          foregroundColor: isCritical ? Colors.white70 : Colors.black,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        ),
                        onPressed: _installApk,
                        icon: const Icon(Icons.install_mobile_rounded),
                        label: const Text('O\'rnatish', style: TextStyle(fontWeight: FontWeight.bold)),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 30),
              ],
            ),
    );
  }

  Widget _buildInfoRow(String label, String value, {bool isPath = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: isPath ? CrossAxisAlignment.start : CrossAxisAlignment.center,
        children: [
          SizedBox(
            width: 100,
            child: Text(label, style: const TextStyle(color: Colors.grey, fontSize: 13)),
          ),
          Expanded(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: TextStyle(
                color: Colors.white,
                fontSize: isPath ? 11 : 13,
                fontWeight: isPath ? FontWeight.normal : FontWeight.w600,
              ),
              maxLines: isPath ? 2 : 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
