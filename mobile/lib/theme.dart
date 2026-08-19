import 'package:flutter/material.dart';

/// Identidade visual do MOTIVA-FIELD, espelhando web/src/theme/tokens.
///
/// Regra igual a do web: nenhum widget escreve cor literal. Tudo sai daqui.
class Cores {
  const Cores._();

  // Marca
  static const Color roxo = Color(0xFF2E0854);
  static const Color roxoClaro = Color(0xFF4B1F80);
  static const Color roxoEscuro = Color(0xFF1C0435);
  static const Color ouro = Color(0xFFF2B705);
  static const Color ouroEscuro = Color(0xFFC99400);

  // Semantica de acao: vermelho so para o que exige acao agora.
  static const Color perigo = Color(0xFFD92D20);
  static const Color perigoForte = Color(0xFF912018);
  static const Color perigoSuave = Color(0xFFFEF3F2);
  static const Color perigoBorda = Color(0xFFFECDCA);

  static const Color atencao = Color(0xFFF97316);
  static const Color atencaoForte = Color(0xFF9A3412);
  static const Color atencaoSuave = Color(0xFFFFF7ED);

  // Escala de risco: codificacao de dado, igual a do painel web.
  static const Color riscoTranquilo = Color(0xFF22C55E);
  static const Color riscoAtencao = Color(0xFFF97316);
  static const Color riscoCritico = Color(0xFFF2B705);

  // Superficies
  static const Color fundo = Color(0xFFF6F4FA);
  static const Color superficie = Color(0xFFFFFFFF);
  static const Color borda = Color(0xFFE3DDEE);
  static const Color bordaForte = Color(0xFFCFC6E0);

  // Texto
  static const Color texto = Color(0xFF201A2B);
  static const Color textoSuave = Color(0xFF675E78);
  static const Color textoApagado = Color(0xFF8A8296);
  static const Color sobreEscuro = Color(0xFFFFFFFF);
  static const Color sobreRoxo = Color(0xFFD9C9F2);

  // Vidro sobre o roxo, para blocos na tela de login.
  static const Color roxoTranslucido = Color(0x1FFFFFFF);
}

class Espacos {
  const Espacos._();

  static const double x1 = 4;
  static const double x2 = 8;
  static const double x3 = 12;
  static const double x4 = 16;
  static const double x5 = 24;
  static const double x6 = 32;
  static const double x7 = 48;
}

class Raios {
  const Raios._();

  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double pill = 999;
}

/// Rotulo pequeno, apagado e em maiusculas discretas — mesma regra do web.
const TextStyle estiloRotulo = TextStyle(
  fontSize: 12,
  fontWeight: FontWeight.w600,
  letterSpacing: 0.8,
  color: Cores.textoApagado,
);

const TextStyle estiloNumero = TextStyle(
  fontSize: 32,
  fontWeight: FontWeight.w500,
  height: 1.05,
  color: Cores.texto,
);

ThemeData construirTema() {
  final ColorScheme esquema = ColorScheme.fromSeed(
    seedColor: Cores.roxo,
    primary: Cores.roxo,
    secondary: Cores.ouro,
    surface: Cores.superficie,
  );

  return ThemeData(
    useMaterial3: true,
    colorScheme: esquema,
    scaffoldBackgroundColor: Cores.fundo,
    appBarTheme: const AppBarTheme(
      backgroundColor: Cores.roxo,
      foregroundColor: Cores.sobreEscuro,
      elevation: 0,
      centerTitle: false,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: Cores.ouro,
        foregroundColor: Cores.roxoEscuro,
        disabledBackgroundColor: Cores.borda,
        disabledForegroundColor: Cores.textoApagado,
        minimumSize: const Size.fromHeight(52),
        elevation: 0,
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Raios.sm),
        ),
      ),
    ),
  );
}
