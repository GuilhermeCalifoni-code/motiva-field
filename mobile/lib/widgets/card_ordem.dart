import 'package:flutter/material.dart';

import '../mock_data.dart';
import '../theme.dart';
import 'selo_prioridade.dart';
import 'selo_risco.dart';

/// Card da OS ativa: onde e, quao grave, quanto cresce e ate quando.
class CardOrdem extends StatelessWidget {
  const CardOrdem({
    super.key,
    required this.ordem,
    required this.ponto,
  });

  final OrdemServico ordem;
  final PontoVegetacao ponto;

  @override
  Widget build(BuildContext context) {
    final double crescimento = crescimentoMensalCm(ponto.historico);

    return Container(
      decoration: BoxDecoration(
        color: Cores.superficie,
        border: Border.all(color: Cores.borda),
        borderRadius: BorderRadius.circular(Raios.lg),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Padding(
            padding: const EdgeInsets.all(Espacos.x5),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: <Widget>[
                    Text('ORDEM ${ordem.id.toUpperCase()}', style: estiloRotulo),
                    SeloRisco(nivelRisco: ponto.nivelRisco),
                  ],
                ),
                const SizedBox(height: Espacos.x3),
                Text(
                  '${ponto.rodovia} · km ${ponto.kmFormatado}',
                  style: const TextStyle(
                    fontSize: 26,
                    fontWeight: FontWeight.w500,
                    height: 1.1,
                    color: Cores.texto,
                  ),
                ),
                const SizedBox(height: Espacos.x1),
                Text(
                  'Sentido ${ponto.sentido.rotulo} · margem ${ponto.margem.rotulo}',
                  style: const TextStyle(fontSize: 14, color: Cores.textoSuave),
                ),
                const SizedBox(height: Espacos.x4),
                Row(
                  children: <Widget>[
                    Expanded(
                      child: _Medida(
                        valor: '${ponto.alturaAtualCm} cm',
                        rotulo: 'altura atual',
                      ),
                    ),
                    Expanded(
                      child: _Medida(
                        valor: '+${crescimento.toStringAsFixed(1)} cm',
                        rotulo: 'por mes',
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: Espacos.x4),
                Wrap(
                  spacing: Espacos.x2,
                  runSpacing: Espacos.x2,
                  children: <Widget>[
                    SeloPrioridade(prioridade: ordem.prioridade),
                    if (ponto.invadePista) const _SeloAlerta(texto: 'Invade a pista'),
                    if (ponto.cobrePlaca) const _SeloAlerta(texto: 'Cobre placa'),
                  ],
                ),
              ],
            ),
          ),
          const _FotoDoPonto(),
          Padding(
            padding: const EdgeInsets.all(Espacos.x5),
            child: Row(
              children: <Widget>[
                const Icon(Icons.schedule, size: 18, color: Cores.textoSuave),
                const SizedBox(width: Espacos.x2),
                Expanded(
                  child: Text(
                    'Previsao de conclusao: ${formatarDataHora(ordem.previsaoConclusao)}',
                    style: const TextStyle(fontSize: 14, color: Cores.textoSuave),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Medida extends StatelessWidget {
  const _Medida({required this.valor, required this.rotulo});

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

class _SeloAlerta extends StatelessWidget {
  const _SeloAlerta({required this.texto});

  final String texto;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: Espacos.x3,
        vertical: Espacos.x1,
      ),
      decoration: BoxDecoration(
        color: Cores.perigoSuave,
        border: Border.all(color: Cores.perigoBorda),
        borderRadius: BorderRadius.circular(Raios.pill),
      ),
      child: Text(
        texto,
        style: const TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: Cores.perigoForte,
        ),
      ),
    );
  }
}

/// Placeholder da foto do ponto. Entra a imagem real da passagem quando o
/// backend servir os frames.
class _FotoDoPonto extends StatelessWidget {
  const _FotoDoPonto();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 150,
      width: double.infinity,
      decoration: const BoxDecoration(
        color: Cores.fundo,
        border: Border.symmetric(horizontal: BorderSide(color: Cores.borda)),
      ),
      child: const Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          Icon(Icons.image_outlined, size: 32, color: Cores.textoApagado),
          SizedBox(height: Espacos.x2),
          Text(
            'Foto da ultima passagem',
            style: TextStyle(fontSize: 13, color: Cores.textoApagado),
          ),
        ],
      ),
    );
  }
}
