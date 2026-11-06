import 'dart:convert';
import 'package:flutter/material.dart';
import '../models/apk_item.dart';
import '../services/apk_scanner_service.dart';
import '../services/risk_evaluator.dart';

class InstalledAppsScreen extends StatefulWidget {
  const InstalledAppsScreen({super.key});

  @override
  State<InstalledAppsScreen> createState() => _InstalledAppsScreenState();
}

class _InstalledAppsScreenState extends State<InstalledAppsScreen> {
  bool _isLoading = true;
  List<InstalledAppAudit> _audits = [];

  @override
  void initState() {
    super.initState();
    _loadAudit();
  }

  Future<void> _loadAudit() async {
    setState(() => _isLoading = true);
    final results = await ApkScannerService.getInstalledAppsAudit();
    if (mounted) {
      setState(() {
        _audits = results;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161922),
        elevation: 0,
        title: const Text('O\'rnatilgan Ilovalar Auditi', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Color(0xFF00E5FF)),
            onPressed: _loadAudit,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF)))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1B1F2A),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFFF9900).withOpacity(0.3)),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.info_outline_rounded, color: Color(0xFFFF9900), size: 28),
                      SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Bu ro\'yxatda SMS o\'qish yoki Ekran nazorati (Accessibility) kabi maxfiy huquqlarga ega bo\'lgan o\'rnatilgan ilovalar ko\'rsatilgan.',
                          style: TextStyle(color: Colors.white70, fontSize: 13),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                if (_audits.isEmpty)
                  Container(
                    padding: const EdgeInsets.all(30),
                    child: const Center(
                      child: Column(
                        children: [
                          Icon(Icons.verified_user_rounded, color: Color(0xFF00E676), size: 48),
                          SizedBox(height: 12),
                          Text(
                            'Shubhali ruxsatlarga ega notanish ilova topilmadi!',
                            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ),
                  )
                else
                  ..._audits.map((app) {
                    return Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1B1F2A),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFFFF3366).withOpacity(0.2)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Container(
                                width: 44,
                                height: 44,
                                decoration: BoxDecoration(
                                  color: const Color(0xFF262C3A),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: app.iconBase64 != null
                                    ? ClipRRect(
                                        borderRadius: BorderRadius.circular(10),
                                        child: Image.memory(
                                          base64Decode(app.iconBase64!),
                                          fit: BoxFit.cover,
                                        ),
                                      )
                                    : const Icon(Icons.android_rounded, color: Color(0xFFFF3366)),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      app.appName,
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 15,
                                      ),
                                    ),
                                    Text(
                                      app.packageName,
                                      style: const TextStyle(color: Colors.grey, fontSize: 11),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          const Text(
                            'Berilgan xavfli huquqlar:',
                            style: TextStyle(color: Colors.white54, fontSize: 12),
                          ),
                          const SizedBox(height: 6),
                          Wrap(
                            spacing: 6,
                            runSpacing: 6,
                            children: app.criticalPermissions.map((perm) {
                              final detail = RiskEvaluator.getDetail(perm);
                              return Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFFF3366).withOpacity(0.12),
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: const Color(0xFFFF3366).withOpacity(0.3)),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(Icons.warning_rounded, color: Color(0xFFFF3366), size: 12),
                                    const SizedBox(width: 4),
                                    Text(
                                      detail.titleUz,
                                      style: const TextStyle(
                                        color: Color(0xFFFF3366),
                                        fontSize: 11,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),
                              );
                            }).toList(),
                          ),
                        ],
                      ),
                    );
                  }),
              ],
            ),
    );
  }
}
