import 'dart:convert';
import 'package:flutter/material.dart';
import '../models/apk_item.dart';
import '../services/apk_scanner_service.dart';
import '../widgets/risk_badge.dart';
import '../widgets/shield_pulse.dart';
import 'apk_detail_screen.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  bool _isScanning = true;
  List<ApkItem> _foundApks = [];
  String _statusMessage = "Xotira va yuklamalar papkasi tekshirilmoqda...";

  @override
  void initState() {
    super.initState();
    _startDeepScan();
  }

  Future<void> _startDeepScan() async {
    setState(() {
      _isScanning = true;
      _foundApks.clear();
      _statusMessage = "Fayllar tizimi indeksatsiyalanmoqda...";
    });

    try {
      await Future.delayed(const Duration(milliseconds: 600));
      setState(() => _statusMessage = "APK manifestlari va ruxsatlar tahlil qilinmoqda...");

      final results = await ApkScannerService.scanAllApks();

      if (mounted) {
        setState(() {
          _foundApks = results;
          _isScanning = false;
          _statusMessage = "Tahlil yakunlandi! Jami ${_foundApks.length} ta APK topildi.";
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

  @override
  Widget build(BuildContext context) {
    final criticalCount = _foundApks.where((a) => a.riskLevel == RiskLevel.critical).length;
    final highCount = _foundApks.where((a) => a.riskLevel == RiskLevel.high).length;

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
              onPressed: _startDeepScan,
              tooltip: "Qayta skanerlash",
            ),
        ],
      ),
      body: Column(
        children: [
          // Scan Visual Header
          Container(
            padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 20),
            decoration: const BoxDecoration(
              color: Color(0xFF161922),
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(30),
                bottomRight: Radius.circular(30),
              ),
            ),
            child: Column(
              children: [
                ShieldPulse(
                  isScanning: _isScanning,
                  isDangerous: criticalCount > 0,
                  onTap: () {
                    if (!_isScanning) _startDeepScan();
                  },
                ),
                const SizedBox(height: 16),
                Text(
                  _isScanning ? "Tizim tahlil qilinmoqda..." : (criticalCount > 0 ? "Xavfli APKlar aniqlandi!" : "Skanerlash yakunlandi"),
                  style: TextStyle(
                    color: criticalCount > 0 ? const Color(0xFFFF3366) : Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  _statusMessage,
                  style: const TextStyle(color: Colors.grey, fontSize: 13),
                  textAlign: TextAlign.center,
                ),
                if (_isScanning) ...[
                  const SizedBox(height: 16),
                  const LinearProgressIndicator(
                    backgroundColor: Color(0xFF262C3A),
                    valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00E5FF)),
                  ),
                ],
              ],
            ),
          ),

          // Found Results Count Bar
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Topilgan fayllar (${_foundApks.length})',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (criticalCount > 0 || highCount > 0)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFF3366).withOpacity(0.15),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFFFF3366).withOpacity(0.4)),
                    ),
                    child: Text(
                      '$criticalCount ta xavfli',
                      style: const TextStyle(
                        color: Color(0xFFFF3366),
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
              ],
            ),
          ),

          // APK List
          Expanded(
            child: _foundApks.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          _isScanning ? Icons.search_rounded : Icons.check_circle_outline_rounded,
                          size: 48,
                          color: Colors.grey,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          _isScanning
                              ? "Fayllar qidirilmoqda..."
                              : "Qurilmada hech qanday shubhali APK topilmadi.",
                          style: const TextStyle(color: Colors.grey, fontSize: 14),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    itemCount: _foundApks.length,
                    itemBuilder: (context, index) {
                      final apk = _foundApks[index];
                      return _buildApkTile(apk);
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildApkTile(ApkItem apk) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF1B1F2A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: apk.riskLevel == RiskLevel.critical
              ? const Color(0xFFFF3366).withOpacity(0.3)
              : Colors.white.withOpacity(0.04),
        ),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
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
        leading: Container(
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
                    errorBuilder: (_, __, ___) => Icon(Icons.android_rounded, color: apk.riskLevel.color),
                  ),
                )
              : Icon(Icons.android_rounded, color: apk.riskLevel.color),
        ),
        title: Text(
          apk.appName,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 15,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
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
                RiskBadge(riskLevel: apk.riskLevel, compact: true),
                const SizedBox(width: 8),
                Text(
                  apk.formattedSize,
                  style: const TextStyle(color: Colors.white38, fontSize: 11),
                ),
              ],
            ),
          ],
        ),
        trailing: const Icon(Icons.chevron_right_rounded, color: Colors.white38),
      ),
    );
  }
}
