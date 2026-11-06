import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'screens/home_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: Color(0xFF0F1117),
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );
  runApp(const ApkQoriqchiApp());
}

class ApkQoriqchiApp extends StatelessWidget {
  const ApkQoriqchiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "APK Qo'riqchi Pro",
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0F1117),
        primaryColor: const Color(0xFF00E5FF),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00E5FF),
          secondary: Color(0xFF00E676),
          error: Color(0xFFFF3366),
          surface: Color(0xFF161922),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF161922),
          elevation: 0,
          centerTitle: false,
          titleTextStyle: TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        fontFamily: 'Roboto',
      ),
      home: const HomeScreen(),
    );
  }
}
