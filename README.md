# 🛡 APK Qo'riqchi Pro (Flutter & Kotlin Native)

Android qurilmalari xavfsizligini ta'minlash, xotira va messenjerlardagi shubhali APK fayllarni o'rnatilishidan oldin tahlil qilish hamda kiberfiribgarlikdan himoya qilish uchun yaratilgan to'liq mobil ilova.

---

## 🚀 Asosiy Imkoniyatlari (1 ga 1 funksionallik)

1. **Chuqur APK Tahlilchi (Deep Analyzer):**
   * Qurilma xotirasi (`Downloads`, `Telegram`, `WhatsApp` va boshqalar)dagi barcha `.apk` fayllarni avtomatik qidirib topadi.
   * `AndroidManifest.xml` tarkibidan paket nomi, versiyasi, ilova belgisi (icon) va barcha so'ralgan ruxsatlarni chiqaradi.

2. **Xavf Skoringi (Risk Engine):**
   * **O'ta xavfli (Critical / 90-100%):** Bank SMS kodlarini o'g'irlovchi (`RECEIVE_SMS`, `READ_SMS`), ekran boshqaruvi (`BIND_ACCESSIBILITY_SERVICE`), soxta to'lov oynasi chiqaruvchi (`SYSTEM_ALERT_WINDOW`).
   * **Yuqori xavf (High):** Kontaktlar, mikrofon, kamera va joylashuv ruxsatlari.
   * **Toza / Xavfsiz (Safe):** Hech qanday shubhali ruxsatga ega bo'lmagan xavfsiz ilovalar.

3. **Real-vaqt Himoyasi (Background Watcher Service):**
   * `FileObserver` yordamida yuklamalar papkasi doimiy kuzatiladi. Yangi APK tushgan soniyadayoq bosh ekranda ogohlantirish xabarnomasi (Push Notification) paydo bo'ladi.

4. **O'rnatish Nazorati (Accessibility Service):**
   * Foydalanuvchi noma'lum dasturni o'rnatmoqchi bo'lganida `PackageInstaller` oynasini aniqlaydi va xavfdan ogohlantiradi.

5. **O'rnatilgan Ilovalar Auditi:**
   * Telefonda allaqachon mavjud bo'lgan dasturlarning qaysi biri SMS yoki Maxsus imkoniyatlarga ega ekanligini fosh qiladi.

6. **Kiberxavfsizlik Maslahatlari (Cyber Tips):**
   * O'zbek tilidagi amaliy xavfsizlik qo'llanmasi (soxta bank ilovalari, firibgar botlar va fishingdan himoyalanish).

---

## 📂 Loyiha Strukturasi

```
apk_qoriqchi_flutter/
├── android/
│   └── app/src/main/
│       ├── AndroidManifest.xml          # Tizim ruxsatlari va xizmatlari
│       ├── kotlin/uz/qoriqchi/apkguard/
│       │   ├── MainActivity.kt          # Flutter <-> Kotlin MethodChannel ko'prigi
│       │   ├── ApkAnalyzer.kt           # APK manifest va ruxsatlar skaneri
│       │   ├── FileWatcherService.kt    # Real-vaqt fon kuzatuv xizmati
│       │   └── GuardAccessibilityService.kt # O'rnatish oynasi nazoratchisi
│       └── res/
│           ├── xml/accessibility_service_config.xml
│           └── xml/file_paths.xml       # Xavfsiz FileProvider
├── lib/
│   ├── main.dart                        # Dark Cyberpunk mavzusi va ishga tushirish
│   ├── models/
│   │   └── apk_item.dart                # ApkItem, RiskLevel va Audit modellari
│   ├── services/
│   │   ├── apk_scanner_service.dart     # Native MethodChannel boshqaruvi
│   │   └── risk_evaluator.dart          # Ruxsatlar tahlili va o'zbekcha izohlar
│   ├── screens/
│   │   ├── home_screen.dart             # Asosiy xavfsizlik paneli va statistika
│   │   ├── scan_screen.dart             # Radar skanerlash animatsiyasi va ro'yxat
│   │   ├── apk_detail_screen.dart       # To'liq xavf tahlili, o'chirish va o'rnatish
│   │   ├── installed_apps_screen.dart   # O'rnatilgan ilovalar auditi
│   │   └── cyber_tips_screen.dart       # Kiberxavfsizlik bo'yicha maslahatlar
│   └── widgets/
│       ├── risk_badge.dart              # Xavf darajasi nishoni
│       ├── shield_pulse.dart            # Pulsatsiyalanuvchi xavfsizlik qalqoni
│       └── stat_card.dart               # Statistika kartochkasi
└── pubspec.yaml
```

---

## 🛠 Ilovani Yig'ish (Build APK)

Ushbu loyihani kompyuterda (Android Studio / VS Code) yoki Flutter o'rnatilgan har qanday muhitda APK formatida yig'ish mumkin:

```bash
# 1. Bog'liqliklarni yuklab olish
flutter pub get

# 2. Release APK yaratish
flutter build apk --release

# Tayyor APK fayli quyidagi manzilda hosil bo'ladi:
# build/app/outputs/flutter-apk/app-release.apk
```

---

## ⚖️ Mualliflik va Maxfiylik

Ushbu ilova mustaqil ravishda kiberxavfsizlik va o'zini himoya qilish maqsadida noldan ishlab chiqilgan bo'lib, ochiq kodli va xavfsiz arxitekturaga ega.
