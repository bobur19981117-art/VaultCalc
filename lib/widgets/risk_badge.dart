import 'package:flutter/material.dart';
import '../models/apk_item.dart';

class RiskBadge extends StatelessWidget {
  final RiskLevel riskLevel;
  final bool compact;

  const RiskBadge({
    super.key,
    required this.riskLevel,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = riskLevel.color;

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
          Icon(riskLevel.icon, size: compact ? 13 : 16, color: color),
          const SizedBox(width: 5),
          Text(
            riskLevel.labelUz,
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
