import 'dart:convert';
import 'package:flutter/material.dart';
import '../models/apk_item.dart';
import '../services/apk_scanner_service.dart';
import '../widgets/risk_badge.dart';
import '../widgets/shield_pulse.dart';
import '../widgets/stat_card.dart';
import 'apk_detail_screen.dart';
import 'cyber_tips_screen.dart';
import 'installed_apps_screen.dart';
import 'scan_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isLoading = true;
  bool _isRealtimeActive = true;
  bool _hasStoragePermission = true;
  List<ApkItem> _recentApks = [];

  @override
  void initState() {
    super.initState();
    _initApp();
  }

  Future<void> _initApp() async {
    setState(() => _isLoading = true);
    try {
      final running = await ApkScannerService.isWatcherRunning();
      final hasPerm = await ApkScannerService.isStorageManagePermissionGranted();
      final apks = await ApkScannerService.scanAllApks();

      if (mounted) {
        setState(() {
          _isRealtimeActive = running;
          _hasStoragePermission = hasPerm;
          _recentApks = apks;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _toggleRealtime(bool value) async {
    setState(() => _isRealtimeActive = value);
    if (value) {
      await ApkScannerService.startWatcherService();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            backgroundColor: Color(0xFF00E676),
            content: Text('Real-vaqt himoyasi faollashtirildi!'),
          ),
        );
      }
    } else {
      await ApkScannerService.stopWatcherService();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            backgroundColor: Colors.grey,
            content: Text('Real-vaqt himoyasi to\'xtatildi.'),
          ),
        );
      }
    }
  }

  void _openScanCategory(ApkCategory category) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ScanScreen(initialCategory: category),
      ),
    ).then((_) => _initApp());
  }

  @override
  Widget build(BuildContext context) {
    final xavfliCount = _recentApks.where((a) => a.category == ApkCategory.xavfli).length;
    final shubhaliCount = _recentApks.where((a) => a.category == ApkCategory.shubhali).length;
    final xavfsizCount = _recentApks.where((a) => a.category == ApkCategory.xavfsiz).length;

    return Scaffold(
      backgroundColor: const Color(0xFF0F1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161922),
        elevation: 0,
        title: const Row(
          children: [
            Icon(Icons.security_rounded, color: Color(0xFF00E5FF), size: 24),
            SizedBox(width: 10),
            Text(
              'APK Qo\'riqchi Pro',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.school_outlined, color: Colors.white70),
            tooltip: 'Maslahatlar',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const CyberTipsScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Colors.white70),
            tooltip: 'Yangilash',
            onPressed: _initApp,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF)))
          : RefreshIndicator(
              onRefresh: _initApp,
              color: const Color(0xFF00E5FF),
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Storage permission warning banner
                  if (!_hasStoragePermission) ...[
                    Container(
                      margin: const EdgeInsets.only(bottom: 14),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF2E2211),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFFFFB300).withOpacity(0.5)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.folder_special_rounded, color: Color(0xFFFFB300), size: 28),
                          const SizedBox(width: 10),
                          const Expanded(
                            child: Text(
                              'To\'liq skanerlash uchun «Barcha fayllarga ruxsat»ni yoqing',
                              style: TextStyle(color: Colors.white, fontSize: 12),
                            ),
                          ),
                          ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFFFFB300),
                              foregroundColor: Colors.black,
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            ),
                            onPressed: () async {
                              await ApkScannerService.requestStorageManagePermission();
                              _initApp();
                            },
                            child: const Text('Ruxsat', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
                          ),
                        ],
                      ),
                    ),
                  ],

                  // Shield Hero Card
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: xavfliCount > 0
                            ? [
                                const Color(0xFF3B1522),
                                const Color(0xFF1B1F2A),
                              ]
                            : [
                                const Color(0xFF122C24),
                                const Color(0xFF1B1F2A),
                              ],
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                      ),
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: xavfliCount > 0
                            ? const Color(0xFFFF3366).withOpacity(0.4)
                            : const Color(0xFF00E676).withOpacity(0.3),
                      ),
                    ),
                    child: Column(
                      children: [
                        ShieldPulse(
                          isScanning: false,
                          isDangerous: xavfliCount > 0,
                          onTap: () => _openScanCategory(ApkCategory.xavfli),
                        ),
                        const SizedBox(height: 14),
                        Text(
                          xavfliCount > 0
                              ? '$xavfliCount ta xavfli APK aniqlandi!'
                              : 'Qurilmangiz himoyalangan',
                          style: TextStyle(
                            color: xavfliCount > 0 ? const Color(0xFFFF3366) : const Color(0xFF00E676),
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 6),
                        Text(
                          xavfliCount > 0
                              ? 'Xavfli ilovalarni ochmang va zudlik bilan o\'chirib tashlang!'
                              : 'Real-vaqt monitoringi barcha yangi yuklamalarni nazorat qilmoqda.',
                          style: const TextStyle(color: Colors.white70, fontSize: 13),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 18),
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF00E5FF),
                              foregroundColor: Colors.black,
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                              elevation: 4,
                            ),
                            onPressed: () => _openScanCategory(ApkCategory.xavfli),
                            icon: const Icon(Icons.radar_rounded),
                            label: const Text(
                              'To\'liq skanerlashni boshlash',
                              style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Real-time Protection Banner
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1B1F2A),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(color: Colors.white.withOpacity(0.04)),
                    ),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: (_isRealtimeActive ? const Color(0xFF00E676) : Colors.grey).withOpacity(0.12),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            Icons.bolt_rounded,
                            color: _isRealtimeActive ? const Color(0xFF00E676) : Colors.grey,
                            size: 20,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Real-vaqt himoyasi',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                ),
                              ),
                              Text(
                                _isRealtimeActive ? 'Faol nazorat qilinmoqda' : 'Himoya o\'chirilgan',
                                style: TextStyle(
                                  color: _isRealtimeActive ? const Color(0xFF00E676) : Colors.grey,
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Switch(
                          value: _isRealtimeActive,
                          onChanged: _toggleRealtime,
                          activeColor: const Color(0xFF00E676),
                          activeTrackColor: const Color(0xFF00E676).withOpacity(0.3),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 18),

                  // ==========================================
                  // 3 TA KATEGORIYA KARTALARI (Xavfli, Shubhali, Xavfsiz)
                  // ==========================================
                  const Text(
                    'Kategoriyalar bo\'yicha tahlil',
                    style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 10),

                  Row(
                    children: [
                      Expanded(
                        child: StatCard(
                          title: 'Xavfli',
                          value: '$xavfliCount ta',
                          icon: Icons.gpp_bad_rounded,
                          color: const Color(0xFFFF3366),
                          onTap: () => _openScanCategory(ApkCategory.xavfli),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: StatCard(
                          title: 'Shubhali',
                          value: '$shubhaliCount ta',
                          icon: Icons.warning_amber_rounded,
                          color: const Color(0xFFFFB300),
                          onTap: () => _openScanCategory(ApkCategory.shubhali),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: StatCard(
                          title: 'Xavfsiz',
                          value: '$xavfsizCount ta',
                          icon: Icons.verified_user_rounded,
                          color: const Color(0xFF00E676),
                          onTap: () => _openScanCategory(ApkCategory.xavfsiz),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 18),

                  // Action Buttons List
                  _buildActionCard(
                    title: 'O\'rnatilgan ilovalar auditi',
                    subtitle: 'Barcha o\'rnatilgan dasturlarning xavfsizlik darajasi',
                    icon: Icons.apps_rounded,
                    color: const Color(0xFF00E5FF),
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const InstalledAppsScreen()),
                      );
                    },
                  ),
                  const SizedBox(height: 10),

                  _buildActionCard(
                    title: 'O\'rnatishni ushlash (Accessibility)',
                    subtitle: 'Shubhali ilova ochilganda avtomatik ogohlantirish',
                    icon: Icons.accessibility_new_rounded,
                    color: const Color(0xFFFF9900),
                    onTap: () => ApkScannerService.openAccessibilitySettings(),
                  ),

                  const SizedBox(height: 22),

                  // Recent APKs
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'So\'nggi topilgan fayllar',
                        style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      TextButton(
                        onPressed: () => _openScanCategory(ApkCategory.xavfli),
                        child: const Text('Barchasi', style: TextStyle(color: Color(0xFF00E5FF))),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  if (_recentApks.isEmpty)
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1B1F2A),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: const Center(
                        child: Text(
                          'Hozircha hech qanday APK fayl topilmadi.',
                          style: TextStyle(color: Colors.grey),
                        ),
                      ),
                    )
                  else
                    ..._recentApks.take(5).map((apk) => _buildApkTile(apk)),

                  const SizedBox(height: 24),
                ],
              ),
            ),
    );
  }

  Widget _buildActionCard({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1B1F2A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.04)),
      ),
      child: ListTile(
        onTap: onTap,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: color.withOpacity(0.12),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: color, size: 22),
        ),
        title: Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
        subtitle: Text(subtitle, style: const TextStyle(color: Colors.grey, fontSize: 11)),
        trailing: const Icon(Icons.arrow_forward_ios_rounded, color: Colors.white30, size: 14),
      ),
    );
  }

  Widget _buildApkTile(ApkItem apk) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: const Color(0xFF1B1F2A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: apk.category == ApkCategory.xavfli
              ? const Color(0xFFFF3366).withOpacity(0.3)
              : Colors.white.withOpacity(0.04),
        ),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => ApkDetailScreen(
                apk: apk,
                onDeleted: _initApp,
              ),
            ),
          ).then((_) => _initApp());
        },
        leading: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: const Color(0xFF262C3A),
            borderRadius: BorderRadius.circular(12),
          ),
          child: apk.iconBase64 != null
              ? ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.memory(
                    base64Decode(apk.iconBase64!),
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => Icon(Icons.android_rounded, color: apk.category.color),
                  ),
                )
              : Icon(Icons.android_rounded, color: apk.category.color),
        ),
        title: Text(
          apk.appName,
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Row(
          children: [
            RiskBadge(category: apk.category, compact: true),
            const SizedBox(width: 8),
            Text(apk.formattedSize, style: const TextStyle(color: Colors.grey, fontSize: 11)),
          ],
        ),
        trailing: const Icon(Icons.chevron_right_rounded, color: Colors.white30),
      ),
    );
  }
}
