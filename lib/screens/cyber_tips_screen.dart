import 'package:flutter/material.dart';

class CyberTipsScreen extends StatelessWidget {
  const CyberTipsScreen({super.key});

  final List<Map<String, dynamic>> _tips = const [
    {
      'title': 'Telegram orqali kelgan APK fayllar',
      'icon': Icons.telegram_rounded,
      'color': Color(0xFF0088CC),
      'body':
          'Firibgarlar ko\'pincha "Foto.apk", "Telegram_Premium.apk", "Online_Kredit.apk" yoki "Bank_Bonus.apk" kabi soxta nomlar bilan virus yuborishadi. Hech qachon shubhali guruh yoki tanish bo\'lmaganlardan kelgan faylni o\'rnatmang!',
    },
    {
      'title': 'Maxsus imkoniyatlar (Accessibility) hiylasi',
      'icon': Icons.accessibility_new_rounded,
      'color': Color(0xFFFF3366),
      'body':
          'Zararli ilova o\'rnatilgach darhol "Maxsus imkoniyatlar" (Спец. возможности)ni yoqishni so\'raydi. Agar bu ruxsat berilsa, virus siz bilmagan holda ekranda xohlagan tugmani bosa oladi va bank parollarini o\'g\'irlaydi.',
    },
    {
      'title': 'SMS kodlarni hech kimga bermang',
      'icon': Icons.sms_failed_rounded,
      'color': Color(0xFFFF9900),
      'body':
          'Bank yoki to\'lov tizimi xodimlari HECH QACHON sizdan SMS orqali kelgan 4-6 xonali tasdiqlash kodini so\'ramaydi. Ushbu kod faqat sizning hisobingizdan pul yechish uchun kerak.',
    },
    {
      'title': 'Faqat rasmiy Google Play dan yuklang',
      'icon': Icons.shop_rounded,
      'color': Color(0xFF00E676),
      'body':
          'Ilovalarni faqat Google Play do\'konidan yoki rasmiy bank saytlaridan yuklab oling. Tizim sozlamalarida "Noma\'lum manbalardan o\'rnatish" imkoniyatini doim o\'chiq holatda saqlang.',
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161922),
        elevation: 0,
        title: const Text('Kiberxavfsizlik Maslahatlari', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF0052D4), Color(0xFF4364F7), Color(0xFF6FB1FC)],
              ),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.security_rounded, color: Colors.white, size: 26),
                    SizedBox(width: 8),
                    Text(
                      'O\'zingizni himoya qiling!',
                      style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                  ],
                ),
                SizedBox(height: 8),
                Text(
                  'Kiberfiribgarlikning 90% holatlari foydalanuvchilarning bilmasdan soxta APK fayllarni o\'rnatishi orqali sodir bo\'ladi.',
                  style: TextStyle(color: Colors.white, fontSize: 13, height: 1.4),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          ..._tips.map((tip) {
            final color = tip['color'] as Color;
            return Container(
              margin: const EdgeInsets.only(bottom: 14),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF1B1F2A),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white.withOpacity(0.05)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: color.withOpacity(0.12),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Icon(tip['icon'] as IconData, color: color, size: 22),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          tip['title'] as String,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Text(
                    tip['body'] as String,
                    style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
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
