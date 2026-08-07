import 'package:flutter/material.dart';

import '../estado_operacao.dart';
import '../mock_data.dart';
import '../theme.dart';
import '../widgets/cartao_secao.dart';
import '../widgets/slot_foto.dart';

/// Comprovacao de execucao. Sem foto do antes, foto do depois e coordenada do
/// momento do registro, nao ha prova de que o servico foi feito — por isso o
/// botao de concluir so acende quando as tres evidencias existem.
class ComprovacaoScreen extends StatelessWidget {
  const ComprovacaoScreen({super.key, required this.estado});

  final EstadoOperacao estado;

  void _concluir(BuildContext context) {
    estado.avancarPara(StatusOS.concluida);
    // Volta para a ordem ativa, que agora mostra o servico comprovado.
    Navigator.of(context).popUntil((Route<void> rota) => rota.isFirst);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: estado,
      builder: (BuildContext context, Widget? _) {
        final PontoVegetacao ponto = estado.ponto;

        return Scaffold(
          appBar: AppBar(title: const Text('Comprovacao de execucao')),
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(Espacos.x5),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  _Progresso(reunidas: estado.evidenciasReunidas),
                  const SizedBox(height: Espacos.x5),

                  CartaoSecao(
                    rotulo: 'Evidencia fotografica',
                    filho: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Row(
                          children: <Widget>[
                            Expanded(
                              child: SlotFoto(
                                titulo: 'Antes',
                                capturada: estado.fotoAntes,
                                horario: estado.fotoAntesEm == null
                                    ? null
                                    : formatarHora(estado.fotoAntesEm!),
                                aoTocar: estado.registrarFotoAntes,
                              ),
                            ),
                            const SizedBox(width: Espacos.x3),
                            Expanded(
                              child: SlotFoto(
                                titulo: 'Depois',
                                capturada: estado.fotoDepois,
                                horario: estado.fotoDepoisEm == null
                                    ? null
                                    : formatarHora(estado.fotoDepoisEm!),
                                aoTocar: estado.registrarFotoDepois,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: Espacos.x3),
                        const Text(
                          'As duas fotos sao obrigatorias e ficam anexadas a ordem.',
                          style: TextStyle(fontSize: 12, color: Cores.textoSuave),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: Espacos.x4),

                  _CartaoGps(estado: estado, ponto: ponto),
                  const SizedBox(height: Espacos.x4),

                  CartaoSecao(
                    rotulo: 'Detalhamento do servico',
                    filho: Column(
                      children: <Widget>[
                        _Linha(rotulo: 'Tipo', valor: detalheServico.tipo),
                        _Linha(rotulo: 'Faixa', valor: detalheServico.faixa),
                        _Linha(
                          rotulo: 'Extensao',
                          valor: '${detalheServico.extensaoM} m',
                        ),
                        _Linha(
                          rotulo: 'Equipamento',
                          valor: detalheServico.equipamento,
                        ),
                        _Linha(rotulo: 'Ordem', valor: estado.ordem.id.toUpperCase()),
                        _Linha(rotulo: 'Operador', valor: estado.operador.nome),
                      ],
                    ),
                  ),
                  const SizedBox(height: Espacos.x4),

                  CartaoSecao(
                    rotulo: 'Localizacao',
                    filho: Column(
                      children: <Widget>[
                        _Linha(
                          rotulo: 'Rodovia',
                          valor: '${ponto.rodovia} · km ${ponto.kmFormatado}',
                        ),
                        _Linha(rotulo: 'Sentido', valor: ponto.sentido.rotulo),
                        _Linha(rotulo: 'Margem', valor: ponto.margem.rotulo),
                        _Linha(
                          rotulo: 'Altura registrada',
                          valor: '${ponto.alturaAtualCm} cm',
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: Espacos.x6),

                  ElevatedButton.icon(
                    onPressed: estado.comprovacaoCompleta
                        ? () => _concluir(context)
                        : null,
                    icon: const Icon(Icons.check_circle_outline, size: 20),
                    label: const Text('Servico concluido'),
                  ),
                  const SizedBox(height: Espacos.x3),
                  if (!estado.comprovacaoCompleta)
                    const Text(
                      'Faltam evidencias para comprovar a execucao.',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 12, color: Cores.textoSuave),
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

/// Mostra ao operador exatamente o que falta — 3 evidencias, nem uma a menos.
class _Progresso extends StatelessWidget {
  const _Progresso({required this.reunidas});

  final int reunidas;

  @override
  Widget build(BuildContext context) {
    const int total = 3;
    final bool completo = reunidas == total;

    return Container(
      padding: const EdgeInsets.all(Espacos.x4),
      decoration: BoxDecoration(
        color: completo ? Cores.superficie : Cores.perigoSuave,
        border: Border.all(
          color: completo ? Cores.riscoTranquilo : Cores.perigoBorda,
        ),
        borderRadius: BorderRadius.circular(Raios.md),
      ),
      child: Row(
        children: <Widget>[
          Icon(
            completo ? Icons.verified : Icons.pending_actions,
            color: completo ? Cores.riscoTranquilo : Cores.perigo,
          ),
          const SizedBox(width: Espacos.x3),
          Expanded(
            child: Text(
              completo
                  ? 'Comprovacao completa. Pode concluir.'
                  : 'Evidencias: $reunidas de $total',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: completo ? Cores.texto : Cores.perigoForte,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CartaoGps extends StatelessWidget {
  const _CartaoGps({required this.estado, required this.ponto});

  final EstadoOperacao estado;
  final PontoVegetacao ponto;

  @override
  Widget build(BuildContext context) {
    final bool capturado = estado.gpsCapturado;

    return CartaoSecao(
      rotulo: 'Coordenada do registro',
      filho: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          if (capturado) ...<Widget>[
            Row(
              children: <Widget>[
                const Icon(Icons.my_location, size: 20, color: Cores.riscoTranquilo),
                const SizedBox(width: Espacos.x3),
                Expanded(
                  child: Text(
                    formatarCoordenada(ponto.latitude, ponto.longitude),
                    style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w600,
                      color: Cores.texto,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: Espacos.x2),
            Text(
              'Capturada as ${formatarHora(estado.gpsCapturadoEm!)} · precisao 4 m',
              style: const TextStyle(fontSize: 12, color: Cores.textoSuave),
            ),
          ] else ...<Widget>[
            const Text(
              'A coordenada do momento do registro prova que o operador esteve no ponto.',
              style: TextStyle(fontSize: 13, color: Cores.textoSuave),
            ),
            const SizedBox(height: Espacos.x4),
            OutlinedButton.icon(
              onPressed: estado.capturarGps,
              icon: const Icon(Icons.my_location, size: 18),
              label: const Text('Capturar coordenada'),
              style: OutlinedButton.styleFrom(
                foregroundColor: Cores.roxo,
                side: const BorderSide(color: Cores.bordaForte),
                minimumSize: const Size.fromHeight(48),
                textStyle: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(Raios.sm),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _Linha extends StatelessWidget {
  const _Linha({required this.rotulo, required this.valor});

  final String rotulo;
  final String valor;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: Espacos.x3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          SizedBox(
            width: 132,
            child: Text(
              rotulo,
              style: const TextStyle(fontSize: 13, color: Cores.textoSuave),
            ),
          ),
          Expanded(
            child: Text(
              valor,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: Cores.texto,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
