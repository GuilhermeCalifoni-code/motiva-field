import 'package:flutter/material.dart';

import '../theme.dart';

/// Bloco branco com rotulo pequeno em maiusculas, usado nas telas de conteudo.
/// Mantem o mesmo respiro do painel web.
class CartaoSecao extends StatelessWidget {
  const CartaoSecao({
    super.key,
    required this.rotulo,
    required this.filho,
    this.acaoTopo,
  });

  final String rotulo;
  final Widget filho;
  final Widget? acaoTopo;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(Espacos.x5),
      decoration: BoxDecoration(
        color: Cores.superficie,
        border: Border.all(color: Cores.borda),
        borderRadius: BorderRadius.circular(Raios.lg),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Expanded(child: Text(rotulo.toUpperCase(), style: estiloRotulo)),
              if (acaoTopo != null) acaoTopo!,
            ],
          ),
          const SizedBox(height: Espacos.x4),
          filho,
        ],
      ),
    );
  }
}
