import 'package:flutter/material.dart';

class PermissionDetail {
  final String permission;
  final String titleUz;
  final String descriptionUz;
  final String severity; // CRITICAL, HIGH, MEDIUM, LOW
  final IconData icon;

  PermissionDetail({
    required this.permission,
    required this.titleUz,
    required this.descriptionUz,
    required this.severity,
    required this.icon,
  });
}

class RiskEvaluator {
  static final Map<String, PermissionDetail> _knownPermissions = {
    'android.permission.RECEIVE_SMS': PermissionDetail(
      permission: 'android.permission.RECEIVE_SMS',
      titleUz: 'SMS xabarlarni tutib olish',
      descriptionUz:
          'O\'ta xavfli: Bank, Click, Payme va Uzum ilovalaridan kelgan bir martalik maxfiy kodlarni yashirincha ushlab olib, o\'g\'irlashi mumkin.',
      severity: 'CRITICAL',
      icon: Icons.sms_failed_rounded,
    ),
    'android.permission.READ_SMS': PermissionDetail(
      permission: 'android.permission.READ_SMS',
      titleUz: 'SMS xabarlarni o\'qish',
      descriptionUz:
          'O\'ta xavfli: Telefonga kelgan barcha shaxsiy yozishmalar va moliyaviy SMS xabarlarni o\'qish imkoniyati.',
      severity: 'CRITICAL',
      icon: Icons.mark_email_read_rounded,
    ),
    'android.permission.SEND_SMS': PermissionDetail(
      permission: 'android.permission.SEND_SMS',
      titleUz: 'Yashirincha SMS yuborish',
      descriptionUz:
          'Sizning hisobingizdan qimmat pullik xizmatlarga yoki firibgarlarga ruxsatsiz SMS xabarlar yuborishi mumkin.',
      severity: 'CRITICAL',
      icon: Icons.send_and_archive_rounded,
    ),
    'android.permission.BIND_ACCESSIBILITY_SERVICE': PermissionDetail(
      permission: 'android.permission.BIND_ACCESSIBILITY_SERVICE',
      titleUz: 'Maxsus imkoniyatlar (Ekran nazorati)',
      descriptionUz:
          'O\'ta yuqori xavf: Ekranda ko\'rilgan har qanday ma\'lumotni o\'qiydi, parollarni ushlaydi va sizning o\'rningizga tugmalarni bosa oladi.',
      severity: 'CRITICAL',
      icon: Icons.accessibility_new_rounded,
    ),
    'android.permission.SYSTEM_ALERT_WINDOW': PermissionDetail(
      permission: 'android.permission.SYSTEM_ALERT_WINDOW',
      titleUz: 'Boshqa ilovalar ustida oyna ochish',
      descriptionUz:
          'Bank yoki to\'lov ilovasi ochilganda uning ustiga o\'zining soxta login/karta oynasini chiqarib, ma\'lumotlarni o\'g\'irlash xavfi mavjud.',
      severity: 'CRITICAL',
      icon: Icons.layers_outlined,
    ),
    'android.permission.REQUEST_INSTALL_PACKAGES': PermissionDetail(
      permission: 'android.permission.REQUEST_INSTALL_PACKAGES',
      titleUz: 'Yashirin ilovalar o\'rnatish',
      descriptionUz:
          'Foydalanuvchiga bildirmasdan internetdan boshqa zararli dasturlarni yuklab olib o\'rnatishga ruxsat beradi.',
      severity: 'CRITICAL',
      icon: Icons.system_update_rounded,
    ),
    'android.permission.READ_CONTACTS': PermissionDetail(
      permission: 'android.permission.READ_CONTACTS',
      titleUz: 'Kontaktlar ro\'yxatini o\'qish',
      descriptionUz:
          'Telefon daftarchasidagi barcha tanishlaringiz va ularning raqamlarini tashqi serverga uzatishi mumkin.',
      severity: 'HIGH',
      icon: Icons.contacts_rounded,
    ),
    'android.permission.CAMERA': PermissionDetail(
      permission: 'android.permission.CAMERA',
      titleUz: 'Kameradan foydalanish',
      descriptionUz:
          'Yashirincha rasm yoki video olish xavfi mavjud.',
      severity: 'HIGH',
      icon: Icons.camera_alt_rounded,
    ),
    'android.permission.RECORD_AUDIO': PermissionDetail(
      permission: 'android.permission.RECORD_AUDIO',
      titleUz: 'Mikrofon orqali yozib olish',
      descriptionUz:
          'Atrofdagi tovushlar va qo\'ng\'iroqlarni yashirincha tinglash/yozib olish xavfi.',
      severity: 'HIGH',
      icon: Icons.mic_rounded,
    ),
    'android.permission.ACCESS_FINE_LOCATION': PermissionDetail(
      permission: 'android.permission.ACCESS_FINE_LOCATION',
      titleUz: 'Aniq GPS joylashuvni kuzatish',
      descriptionUz:
          'Qurilmaning aniq geografik koordinatalarini real vaqtda kuzatish.',
      severity: 'HIGH',
      icon: Icons.location_on_rounded,
    ),
  };

  static PermissionDetail getDetail(String permission) {
    if (_knownPermissions.containsKey(permission)) {
      return _knownPermissions[permission]!;
    }

    final simpleName = permission.split('.').last;
    return PermissionDetail(
      permission: permission,
      titleUz: simpleName,
      descriptionUz: 'Standart tizim ruxsati.',
      severity: 'LOW',
      icon: Icons.security_rounded,
    );
  }
}
