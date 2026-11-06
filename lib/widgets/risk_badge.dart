import 'package:flutter/material.dart';
import '../models/apk_item.dart';

class RiskBadge extends StatelessWidget {
  final ApkCategory category;
  final bool compact;

  const RiskBadge({
    super.key,
    required this.category,
    this.compact = false,
  });

  factory RiskBadge.fromRiskLevel({
    Key? key,
    required RiskLevel riskLevel,
    bool compact = false,
  }) {
    return RiskBadge(
      key: key,
      category: ApkCategory.fromRiskLevel(riskLevel),
      compact: compact,
    );
  }

  @override
  Widget build(BuildContext context) {
    final color = category.color;

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 8 : 12,
        vertical: compact ? 4 : 6,
      ),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.5), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(category.icon, size: compact ? 13 : 16, color: color),
          const SizedBox(width: 5),
          Text(
            category.labelUz.toUpperCase(),
            style: TextStyle(
              color: color,
              fontSize: compact ? 10 : 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }
}
