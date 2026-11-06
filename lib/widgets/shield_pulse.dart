import 'package:flutter/material.dart';

class ShieldPulse extends StatefulWidget {
  final bool isScanning;
  final bool isDangerous;
  final VoidCallback onTap;

  const ShieldPulse({
    super.key,
    required this.isScanning,
    required this.isDangerous,
    required this.onTap,
  });

  @override
  State<ShieldPulse> createState() => _ShieldPulseState();
}

class _ShieldPulseState extends State<ShieldPulse> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _scaleAnimation = Tween<double>(begin: 0.96, end: 1.05).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final themeColor = widget.isDangerous
        ? const Color(0xFFFF3366)
        : (widget.isScanning ? const Color(0xFF00E5FF) : const Color(0xFF00E676));

    return GestureDetector(
      onTap: widget.onTap,
      child: AnimatedBuilder(
        animation: _scaleAnimation,
        builder: (context, child) {
          return Transform.scale(
            scale: widget.isScanning ? _scaleAnimation.value : 1.0,
            child: Container(
              width: 170,
              height: 170,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    themeColor.withOpacity(0.25),
                    themeColor.withOpacity(0.08),
                    Colors.transparent,
                  ],
                  stops: const [0.4, 0.7, 1.0],
                ),
                boxShadow: [
                  BoxShadow(
                    color: themeColor.withOpacity(0.25),
                    blurRadius: 40,
                    spreadRadius: widget.isScanning ? 10 : 2,
                  ),
                ],
              ),
              child: Center(
                child: Container(
                  width: 110,
                  height: 110,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(0xFF1E222D),
                    border: Border.all(color: themeColor, width: 2.5),
                  ),
                  child: Icon(
                    widget.isDangerous
                        ? Icons.gpp_maybe_rounded
                        : (widget.isScanning ? Icons.radar_rounded : Icons.shield_rounded),
                    size: 56,
                    color: themeColor,
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
