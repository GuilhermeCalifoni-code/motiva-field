import 'package:flutter/material.dart';

import '../mock_data.dart';
import '../theme.dart';

Color _corDaPrioridade(Prioridade prioridade) {
  switch (prioridade) {
    case Prioridade.baixa:
      return Cores.riscoTranquilo;
    case Prioridade.media:
      return Cores.atencao;
    case Prioridade.alta:
      return Cores.perigo;
  }
}

class SeloPrioridade extends StatelessWidget {
  const SeloPrioridade({super.key, required this.prioridade});

  final Prioridade prioridade;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: Espacos.x3,
        vertical: Espacos.x1,
      ),
      decoration: BoxDecoration(
        color: _corDaPrioridade(prioridade),
        borderRadius: BorderRadius.circular(Raios.pill),
      ),
      child: Text(
        'Prioridade ${prioridade.rotulo.toLowerCase()}',
        style: const TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w700,
          color: Cores.sobreEscuro,
        ),
      ),
    );
  }
}
