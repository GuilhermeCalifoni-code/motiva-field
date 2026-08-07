import 'package:flutter/material.dart';

import '../mock_data.dart';
import '../theme.dart';

/// Escala de risco do produto, igual a do painel web: verde tranquilo,
/// laranja atencao, ouro critico.
Color corDoRisco(NivelRisco nivel) {
  switch (nivel) {
    case NivelRisco.tranquilo:
      return Cores.riscoTranquilo;
    case NivelRisco.atencao:
      return Cores.riscoAtencao;
    case NivelRisco.critico:
      return Cores.riscoCritico;
  }
}

class SeloRisco extends StatelessWidget {
  const SeloRisco({super.key, required this.nivelRisco});

  final NivelRisco nivelRisco;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: Espacos.x3,
        vertical: Espacos.x1,
      ),
      decoration: BoxDecoration(
        color: corDoRisco(nivelRisco),
        borderRadius: BorderRadius.circular(Raios.pill),
      ),
      child: Text(
        nivelRisco.rotulo,
        style: const TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w700,
          color: Cores.texto,
        ),
      ),
    );
  }
}
