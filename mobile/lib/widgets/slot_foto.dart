import 'package:flutter/material.dart';

import '../theme.dart';

/// Slot de evidencia fotografica. Vazio, convida a capturar; preenchido, mostra
/// que a prova existe. A camera real entra depois — aqui o toque so marca o
/// slot como capturado.
class SlotFoto extends StatelessWidget {
  const SlotFoto({
    super.key,
    required this.titulo,
    required this.capturada,
    required this.horario,
    required this.aoTocar,
  });

  final String titulo;
  final bool capturada;
  final String? horario;
  final VoidCallback aoTocar;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: aoTocar,
      child: Container(
        height: 168,
        decoration: BoxDecoration(
          color: capturada ? Cores.atencaoSuave : Cores.fundo,
          border: Border.all(
            color: capturada ? Cores.ouro : Cores.bordaForte,
            width: capturada ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(Raios.md),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Icon(
              capturada ? Icons.check_circle : Icons.photo_camera_outlined,
              size: 34,
              color: capturada ? Cores.ouroEscuro : Cores.textoApagado,
            ),
            const SizedBox(height: Espacos.x3),
            Text(
              titulo.toUpperCase(),
              style: estiloRotulo.copyWith(
                color: capturada ? Cores.texto : Cores.textoApagado,
              ),
            ),
            const SizedBox(height: Espacos.x1),
            Text(
              capturada ? 'Registrada as ${horario ?? '--:--'}' : 'Tocar para capturar',
              style: const TextStyle(fontSize: 12, color: Cores.textoSuave),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
