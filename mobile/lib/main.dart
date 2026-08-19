import 'package:flutter/material.dart';

import 'screens/login_screen.dart';
import 'theme.dart';

void main() {
  runApp(const MotivaFieldApp());
}

class MotivaFieldApp extends StatelessWidget {
  const MotivaFieldApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Motiva Field',
      debugShowCheckedModeBanner: false,
      theme: construirTema(),
      home: const LoginScreen(),
    );
  }
}
