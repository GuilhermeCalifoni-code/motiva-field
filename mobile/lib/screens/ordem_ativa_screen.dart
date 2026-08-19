import 'package:flutter/material.dart';

import '../estado_operacao.dart';
import '../mock_data.dart';
import '../theme.dart';
import '../widgets/card_ordem.dart';
import '../widgets/cartao_secao.dart';
import 'navegacao_screen.dart';

class OrdemAtivaScreen extends StatelessWidget {
  const OrdemAtivaScreen({super.key, required this.estado});

  final EstadoOperacao estado;

  void _iniciarRota(BuildContext context) {
    estado.avancarPara(StatusOS.emDeslocamento);
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (BuildContext context) => NavegacaoScreen(estado: estado),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: estado,
      builder: (BuildContext context, Widget? _) {
        final OrdemServico ordem = estado.ordem;
        final PontoVegetacao ponto = estado.ponto;
        final bool concluida = ordem.status == StatusOS.concluida;

        return Scaffold(
          appBar: AppBar(
            title: const Text('Ordem ativa'),
            actions: <Widget>[
              Padding(
                padding: const EdgeInsets.only(right: Espacos.x4),
                child: Center(
                  child: Text(
                    ordem.status.rotulo,
                    style: const TextStyle(fontSize: 13, color: Cores.sobreRoxo),
                  ),
                ),
              ),
            ],
          ),
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(Espacos.x5),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  _Saudacao(operador: estado.operador),
                  const SizedBox(height: Espacos.x5),
                  CardOrdem(ordem: ordem, ponto: ponto),
                  const SizedBox(height: Espacos.x4),
                  const _CondicoesLocaisCard(),
                  const SizedBox(height: Espacos.x6),
                  if (concluida)
                    const _AvisoConcluida()
                  else
                    ElevatedButton.icon(
                      onPressed: () => _iniciarRota(context),
                      icon: const Icon(Icons.navigation, size: 20),
                      label: const Text('Iniciar rota'),
                    ),
                  const SizedBox(height: Espacos.x5),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _Saudacao extends StatelessWidget {
  const _Saudacao({required this.operador});

  final Operador operador;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          '${saudacaoPara(DateTime.now())}, ${operador.primeiroNome}',
          style: const TextStyle(
            fontSize: 26,
            fontWeight: FontWeight.w500,
            color: Cores.texto,
          ),
        ),
        const SizedBox(height: Espacos.x1),
        Text(
          'Matricula ${operador.matricula} · voce tem 1 ordem em aberto',
          style: const TextStyle(fontSize: 14, color: Cores.textoSuave),
        ),
      ],
    );
  }
}

class _CondicoesLocaisCard extends StatelessWidget {
  const _CondicoesLocaisCard();

  @override
  Widget build(BuildContext context) {
    const CondicoesLocais c = condicoesLocais;

    return CartaoSecao(
      rotulo: 'Condicoes locais',
      filho: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: <Widget>[
              Text(
                '${c.temperaturaC.toStringAsFixed(0)}°C',
                style: estiloNumero,
              ),
              const SizedBox(width: Espacos.x4),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      c.condicao,
                      style: const TextStyle(fontSize: 15, color: Cores.texto),
                    ),
                    const SizedBox(height: Espacos.x1),
                    Text(
                      'Vento ${c.ventoKmh} km/h · chuva ${c.chuva24hMm.toStringAsFixed(1)} mm em 24h',
                      style: const TextStyle(fontSize: 13, color: Cores.textoSuave),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (c.aceleraCrescimento) ...<Widget>[
            const SizedBox(height: Espacos.x4),
            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: Espacos.x3,
                vertical: Espacos.x2,
              ),
              decoration: BoxDecoration(
                color: Cores.atencaoSuave,
                borderRadius: BorderRadius.circular(Raios.sm),
              ),
              child: const Row(
                children: <Widget>[
                  Icon(Icons.water_drop_outlined, size: 16, color: Cores.atencaoForte),
                  SizedBox(width: Espacos.x2),
                  Expanded(
                    child: Text(
                      'Chuva no trecho — crescimento tende a acelerar',
                      style: TextStyle(fontSize: 12, color: Cores.atencaoForte),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _AvisoConcluida extends StatelessWidget {
  const _AvisoConcluida();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(Espacos.x4),
      decoration: BoxDecoration(
        color: Cores.superficie,
        border: Border.all(color: Cores.riscoTranquilo),
        borderRadius: BorderRadius.circular(Raios.md),
      ),
      child: const Row(
        children: <Widget>[
          Icon(Icons.verified, color: Cores.riscoTranquilo),
          SizedBox(width: Espacos.x3),
          Expanded(
            child: Text(
              'Servico comprovado e enviado. Nenhuma ordem em aberto.',
              style: TextStyle(fontSize: 14, color: Cores.texto),
            ),
          ),
        ],
      ),
    );
  }
}
