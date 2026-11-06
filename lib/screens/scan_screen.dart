import 'dart:convert';
import 'package:flutter/material.dart';
import '../models/apk_item.dart';
import '../services/apk_scanner_service.dart';
import '../widgets/risk_badge.dart';
import '../widgets/shield_pulse.dart';
import 'apk_detail_screen.dart';

class ScanScreen extends StatefulWidget {
  final ApkCategory initialCategory;

  const ScanScreen({
    super.key,
    this.initialCategory = ApkCategory.xavfli,
  });

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  bool _isScanning = true;
  bool _hasStoragePermission = true;
  List<ApkItem> _foundApks = [];
  late ApkCategory _selectedCategory;
  String _statusMessage = "Xotira va yuklamalar papkasi tekshirilmoqda...";

  @override
  void initState() {
    super.initState();
    _selectedCategory = widget.initialCategory;
    _checkPermissionAndScan();
  }

  Future<void> _checkPermissionAndScan() async {
    final granted = await ApkScannerService.isStorageManagePermissionGranted();
    if (mounted) {
      setState(() => _hasStoragePermission = granted);
    }
    _startDeepScan();
  }

  Future<void> _startDeepScan() async {
    setState(() {
      _isScanning = true;
      _foundApks.clear();
      _statusMessage = "Fayllar tizimi indeksatsiyalanmoqda...";
    });

    try {
      await Future.delayed(const Duration(milliseconds: 500));
      if (mounted) {
        setState(() => _statusMessage = "APK manifestlari va ruxsatlar tahlil qilinmoqda...");
      }

      final results = await ApkScannerService.scanAllApks();

      if (mounted) {
        setState(() {
          _foundApks = results;
          _isScanning = false;
          _statusMessage = "Tahlil yakunlandi! Jami ${_foundApks.length} ta APK topildi.";

          // Agar tanlangan kategoriyada hech narsa bo'lmasa, bor kategoriyaga o'tish
          final xavfli = _foundApks.where((a) => a.category == ApkCategory.xavfli).length;
          final shubhali = _foundApks.where((a) => a.category == ApkCategory.shubhali).length;
          if (_selectedCategory == ApkCategory.xavfli && xavfli == 0) {
            if (shubhali > 0) {
              _selectedCategory = ApkCategory.shubhali;
            } else if (_foundApks.isNotEmpty) {
              _selectedCategory = ApkCategory.xavfsiz;
            }
          }
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isScanning = false;
          _statusMessage = "Skanerlashda xatolik yuz berdi.";
        });
      }
    }
  }

  List<ApkItem> get _xavfliList =>
      _foundApks.where((a) => a.category == ApkCategory.xavfli).toList();
  List<ApkItem> get _shubhaliList =>
      _foundApks.where((a) => a.category == ApkCategory.shubhali).toList();
  List<ApkItem> get _xavfsizList =>
      _foundApks.where((a) => a.category == ApkCategory.xavfsiz).toList();

  List<ApkItem> get _currentList {
    switch (_selectedCategory) {
      case ApkCategory.xavfli:
        return _xavfliList;
      case ApkCategory.shubhali:
        return _shubhaliList;
      case ApkCategory.xavfsiz:
        return _xavfsizList;
    }
  }

  void _deleteApk(ApkItem apk) async {
    final confirm = await showDialog<bool>(
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
          '"${apk.fileName}" zararli faylini xotiradan butunlay o\'chirmoqchimisiz?',
          style: const TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Bekor qilish', style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFFF3366),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('O\'chirish', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      final deleted = await ApkScannerService.deleteApk(apk.filePath);
      if (mounted) {
        if (deleted) {
          setState(() {
            _foundApks.removeWhere((item) => item.filePath == apk.filePath);
          });
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              backgroundColor: Color(0xFF00E676),
              content: Text('Zararli fayl muvaffaqiyatli o\'chirildi!'),
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              backgroundColor: Colors.red,
              content: Text('Faylni o\'chirib bo\'lmadi.'),
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final criticalCount = _xavfliList.length;

    return Scaffold(
      backgroundColor: const Color(0xFF0F1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161922),
        elevation: 0,
        title: const Text('To\'liq Skanerlash', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          if (!_isScanning)
            IconButton(
              icon: const Icon(Icons.refresh_rounded, color: Color(0xFF00E5FF)),
              onPressed: _checkPermissionAndScan,
              tooltip: "Qayta skanerlash",
            ),
        ],
      ),
      body: Column(
        children: [
          // Scan Visual Header
          Container(
            padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 20),
            decoration: const BoxDecoration(
              color: Color(0xFF161922),
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(28),
                bottomRight: Radius.circular(28),
              ),
            ),
            child: Column(
              children: [
                ShieldPulse(
                  isScanning: _isScanning,
                  isDangerous: criticalCount > 0,
                  onTap: () {
                    if (!_isScanning) _checkPermissionAndScan();
                  },
                ),
                const SizedBox(height: 12),
                Text(
                  _isScanning
                      ? "Tizim tahlil qilinmoqda..."
                      : (criticalCount > 0 ? "Diqqat: Xavfli dasturlar topildi!" : "Skanerlash yakunlandi"),
                  style: TextStyle(
                    color: criticalCount > 0 ? const Color(0xFFFF3366) : Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  _statusMessage,
                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                  textAlign: TextAlign.center,
                ),
                if (_isScanning) ...[
                  const SizedBox(height: 14),
                  const LinearProgressIndicator(
                    backgroundColor: Color(0xFF262C3A),
                    valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00E5FF)),
                  ),
                ],
              ],
            ),
          ),

          // Permission Warning Banner if missing
          if (!_hasStoragePermission)
            Container(
              margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFF2E2211),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFFFFB300).withOpacity(0.5)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.folder_special_rounded, color: Color(0xFFFFB300), size: 26),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Text(
                      'Barcha papkalarni ko\'rish uchun ruxsat bering:',
                      style: TextStyle(color: Colors.white, fontSize: 12),
                    ),
                  ),
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFFFB300),
                      foregroundColor: Colors.black,
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    onPressed: () async {
                      await ApkScannerService.requestStorageManagePermission();
                      final granted = await ApkScannerService.isStorageManagePermissionGranted();
                      setState(() => _hasStoragePermission = granted);
                      if (granted) _startDeepScan();
                    },
                    child: const Text('Ruxsat', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                  ),
                ],
              ),
            ),

          const SizedBox(height: 14),

          // ==========================================
          // 3 TA KATEGORIYA TUGMALARI (Xavfli, Shubhali, Xavfsiz)
          // ==========================================
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Container(
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: const Color(0xFF161922),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: Colors.white.withOpacity(0.06)),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: _buildCategoryTab(
                      category: ApkCategory.xavfli,
                      count: _xavfliList.length,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Expanded(
                    child: _buildCategoryTab(
                      category: ApkCategory.shubhali,
                      count: _shubhaliList.length,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Expanded(
                    child: _buildCategoryTab(
                      category: ApkCategory.xavfsiz,
                      count: _xavfsizList.length,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Kategoriya tavsifi
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 10, 20, 6),
            child: Row(
              children: [
                Icon(_selectedCategory.icon, color: _selectedCategory.color, size: 16),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    _selectedCategory.descriptionUz,
                    style: TextStyle(color: Colors.grey[400], fontSize: 11),
                  ),
                ),
              ],
            ),
          ),

          const Divider(color: Color(0xFF1F2430), height: 12),

          // APK List
          Expanded(
            child: _isScanning
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF)))
                : _currentList.isEmpty
                    ? _buildEmptyState()
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        itemCount: _currentList.length,
                        itemBuilder: (context, index) {
                          final apk = _currentList[index];
                          return _buildApkCard(apk);
                        },
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryTab({
    required ApkCategory category,
    required int count,
  }) {
    final isSelected = _selectedCategory == category;
    final color = category.color;

    return GestureDetector(
      onTap: () {
        setState(() => _selectedCategory = category);
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? color.withOpacity(0.18) : Colors.transparent,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: isSelected ? color : Colors.transparent,
            width: 1.5,
          ),
        ),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(category.icon, size: 14, color: isSelected ? color : Colors.grey),
                const SizedBox(width: 4),
                Text(
                  category.labelUz,
                  style: TextStyle(
                    color: isSelected ? Colors.white : Colors.grey,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 3),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: isSelected ? color : const Color(0xFF262C3A),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '$count ta',
                style: TextStyle(
                  color: isSelected ? Colors.black : Colors.white70,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    IconData icon;
    String title;
    String subtitle;
    Color color;

    switch (_selectedCategory) {
      case ApkCategory.xavfli:
        icon = Icons.verified_user_rounded;
        color = const Color(0xFF00E676);
        title = "Zo'r! Hech qanday xavfli virus topilmadi";
        subtitle = "Telefoningizda SMS yoki bank hisoblarini o'g'irlaydigan troyanlar aniqlanmadi.";
        break;
      case ApkCategory.shubhali:
        icon = Icons.check_circle_outline_rounded;
        color = const Color(0xFFFFB300);
        title = "Shubhali ilovalar topilmadi";
        subtitle = "Ortiqcha ruxsatlarni talab qiladigan dasturlar yo'q.";
        break;
      case ApkCategory.xavfsiz:
        icon = Icons.folder_open_rounded;
        color = Colors.grey;
        title = "Xavfsiz APK fayllar topilmadi";
        subtitle = "Xotirangizda yuklab olingan boshqa APK fayllar mavjud emas.";
        break;
    }

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, size: 48, color: color),
            ),
            const SizedBox(height: 16),
            Text(
              title,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              subtitle,
              style: const TextStyle(color: Colors.grey, fontSize: 12),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildApkCard(ApkItem apk) {
    final isXavfli = apk.category == ApkCategory.xavfli;
    final borderColor = apk.category.color.withOpacity(isXavfli ? 0.5 : 0.15);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF1B1F2A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: borderColor, width: isXavfli ? 1.5 : 1),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () async {
            final res = await Navigator.push(
              context,
              MaterialPageRoute(
                builder: (ctx) => ApkDetailScreen(
                  apk: apk,
                  onDeleted: () {
                    setState(() {
                      _foundApks.removeWhere((item) => item.filePath == apk.filePath);
                    });
                  },
                ),
              ),
            );
            if (res == true) {
              setState(() {
                _foundApks.removeWhere((item) => item.filePath == apk.filePath);
              });
            }
          },
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Icon
                    Container(
                      width: 48,
                      height: 48,
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
                                errorBuilder: (_, __, ___) =>
                                    Icon(Icons.android_rounded, color: apk.category.color),
                              ),
                            )
                          : Icon(Icons.android_rounded, color: apk.category.color),
                    ),
                    const SizedBox(width: 12),

                    // App Title & File
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            apk.appName,
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 15,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 3),
                          Text(
                            apk.fileName,
                            style: const TextStyle(color: Colors.grey, fontSize: 11),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 4),
                          Row(
                            children: [
                              RiskBadge(category: apk.category, compact: true),
                              const SizedBox(width: 8),
                              Text(
                                apk.formattedSize,
                                style: const TextStyle(color: Colors.white38, fontSize: 11),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),

                    // Chevron
                    const Icon(Icons.chevron_right_rounded, color: Colors.white38),
                  ],
                ),

                // Xavfli yoki Shubhali bo'lsa xavf sababini ko'rsatish
                if (apk.criticalCount > 0 || apk.highCount > 0) ...[
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF131722),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          isXavfli ? Icons.warning_amber_rounded : Icons.info_outline_rounded,
                          color: apk.category.color,
                          size: 14,
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            isXavfli
                                ? '🚨 ${apk.criticalCount} ta o\'ta xavfli ruxsat (SMS, Ekran kuzatish)'
                                : '⚠️ ${apk.highCount} ta shubhali ruxsat (Kontakt, Joylashuv)',
                            style: TextStyle(
                              color: apk.category.color,
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],

                // Xavfli bo'lsa tezkor O'chirish tugmasi
                if (isXavfli) ...[
                  const SizedBox(height: 10),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFFFF3366),
                        side: const BorderSide(color: Color(0xFFFF3366)),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      onPressed: () => _deleteApk(apk),
                      icon: const Icon(Icons.delete_forever_rounded, size: 16),
                      label: const Text('Faylni butunlay o\'chirish', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
