import 'package:flutter/material.dart';

import '../estado_operacao.dart';
import '../mock_data.dart';
import '../theme.dart';
import 'comprovacao_screen.dart';

class NavegacaoScreen extends StatelessWidget {
  const NavegacaoScreen({super.key, required this.estado});

  final EstadoOperacao estado;

  void _cheguei(BuildContext context) {
    estado.avancarPara(StatusOS.noLocal);
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (BuildContext context) => ComprovacaoScreen(estado: estado),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    const RotaNavegacao rota = rotaAtiva;
    final Manobra proxima = rota.manobras.first;

    return Scaffold(
      appBar: AppBar(title: const Text('Navegacao')),
      body: SafeArea(
        child: Column(
          children: <Widget>[
            _InstrucaoManobra(manobra: proxima),
            Expanded(
              child: Stack(
                children: <Widget>[
                  const Positioned.fill(child: _MapaPlaceholder()),
                  Positioned(
                    left: Espacos.x4,
                    right: Espacos.x4,
                    bottom: Espacos.x4,
                    child: _ProximasManobras(
                      manobras: rota.manobras.skip(1).toList(),
                    ),
                  ),
                ],
              ),
            ),
            _RodapeRota(rota: rota, aoChegar: () => _cheguei(context)),
          ],
        ),
      ),
    );
  }
}

class _InstrucaoManobra extends StatelessWidget {
  const _InstrucaoManobra({required this.manobra});

  final Manobra manobra;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      color: Cores.roxo,
      padding: const EdgeInsets.fromLTRB(
        Espacos.x5,
        Espacos.x4,
        Espacos.x5,
        Espacos.x5,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              color: Cores.ouro,
              borderRadius: BorderRadius.circular(Raios.md),
            ),
            child: const Icon(Icons.arrow_upward, size: 30, color: Cores.roxoEscuro),
          ),
          const SizedBox(width: Espacos.x4),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  '${manobra.distanciaM} m',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.8,
                    color: Cores.ouro,
                  ),
                ),
                const SizedBox(height: Espacos.x1),
                Text(
                  manobra.instrucao,
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w500,
                    color: Cores.sobreEscuro,
                  ),
                ),
                const SizedBox(height: Espacos.x1),
                Text(
                  manobra.complemento,
                  style: const TextStyle(fontSize: 14, color: Cores.sobreRoxo),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Placeholder do mapa. Desenhado a mao para nao depender de pacote de mapa
/// nesta fase — entra flutter_map quando a rota for real.
class _MapaPlaceholder extends StatelessWidget {
  const _MapaPlaceholder();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFFEDE9F3),
      child: CustomPaint(
        painter: _PintorRota(),
        child: const Center(
          child: Padding(
            padding: EdgeInsets.only(top: Espacos.x7),
            child: Text(
              'Mapa da rota',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.8,
                color: Cores.textoApagado,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _PintorRota extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final Paint via = Paint()
      ..color = Cores.bordaForte
      ..strokeWidth = 14
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final Paint rota = Paint()
      ..color = Cores.roxo
      ..strokeWidth = 6
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final Path caminho = Path()
      ..moveTo(size.width * 0.18, size.height * 0.92)
      ..lineTo(size.width * 0.30, size.height * 0.62)
      ..lineTo(size.width * 0.58, size.height * 0.50)
      ..lineTo(size.width * 0.68, size.height * 0.24);

    canvas.drawPath(caminho, via);
    canvas.drawPath(caminho, rota);

    // Posicao atual do operador.
    canvas.drawCircle(
      Offset(size.width * 0.18, size.height * 0.92),
      10,
      Paint()..color = Cores.roxo,
    );
    canvas.drawCircle(
      Offset(size.width * 0.18, size.height * 0.92),
      5,
      Paint()..color = Cores.sobreEscuro,
    );

    // Destino.
    canvas.drawCircle(
      Offset(size.width * 0.68, size.height * 0.24),
      11,
      Paint()..color = Cores.ouro,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _ProximasManobras extends StatelessWidget {
  const _ProximasManobras({required this.manobras});

  final List<Manobra> manobras;

  @override
  Widget build(BuildContext context) {
    if (manobras.isEmpty) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.all(Espacos.x4),
      decoration: BoxDecoration(
        color: Cores.superficie,
        border: Border.all(color: Cores.borda),
        borderRadius: BorderRadius.circular(Raios.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Text('A SEGUIR', style: estiloRotulo),
          const SizedBox(height: Espacos.x3),
          for (final Manobra m in manobras)
            Padding(
              padding: const EdgeInsets.only(bottom: Espacos.x2),
              child: Row(
                children: <Widget>[
                  const Icon(Icons.turn_right, size: 18, color: Cores.textoSuave),
                  const SizedBox(width: Espacos.x3),
                  Expanded(
                    child: Text(
                      m.instrucao,
                      style: const TextStyle(fontSize: 14, color: Cores.texto),
                    ),
                  ),
                  Text(
                    '${m.distanciaM} m',
                    style: const TextStyle(fontSize: 13, color: Cores.textoSuave),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _RodapeRota extends StatelessWidget {
  const _RodapeRota({required this.rota, required this.aoChegar});

  final RotaNavegacao rota;
  final VoidCallback aoChegar;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(Espacos.x5),
      decoration: const BoxDecoration(
        color: Cores.superficie,
        border: Border(top: BorderSide(color: Cores.borda)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Text('DESTINO', style: estiloRotulo),
          const SizedBox(height: Espacos.x1),
          Text(
            rota.destino,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: Cores.texto,
            ),
          ),
          const SizedBox(height: Espacos.x4),
          Row(
            children: <Widget>[
              Expanded(
                child: _Metrica(
                  valor: '${rota.tempoMin} min',
                  rotulo: 'tempo estimado',
                ),
              ),
              Expanded(
                child: _Metrica(
                  valor: '${rota.distanciaKm.toStringAsFixed(1).replaceAll('.', ',')} km',
                  rotulo: 'distancia',
                ),
              ),
            ],
          ),
          const SizedBox(height: Espacos.x5),
          ElevatedButton.icon(
            onPressed: aoChegar,
            icon: const Icon(Icons.place, size: 20),
            label: const Text('Cheguei ao local'),
          ),
        ],
      ),
    );
  }
}

class _Metrica extends StatelessWidget {
  const _Metrica({required this.valor, required this.rotulo});

  final String valor;
  final String rotulo;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(valor, style: estiloNumero.copyWith(fontSize: 24)),
        const SizedBox(height: Espacos.x1),
        Text(rotulo.toUpperCase(), style: estiloRotulo),
      ],
    );
  }
}
