import 'package:flutter/material.dart';

import '../estado_operacao.dart';
import '../mock_data.dart';
import '../services/evidencias.dart';
import '../services/evidencias.dart';
import '../theme.dart';
import '../widgets/cartao_secao.dart';
import '../widgets/slot_foto.dart';

/// Comprovação de execução. O envio só é liberado depois de duas fotos
/// capturadas pela câmera e uma posição obtida do aparelho.
class ComprovacaoScreen extends StatelessWidget {
  const ComprovacaoScreen({super.key, required this.estado});

  final EstadoOperacao estado;

  Future<void> _capturarFoto(BuildContext context, {required bool antes}) async {
    try {
      final String? caminho = await evidenciasGateway.capturarFoto();
      if (caminho == null) return;
      if (antes) {
        estado.registrarFotoAntes(caminho);
      } else {
        estado.registrarFotoDepois(caminho);
      }
    } catch (erro) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Não foi possível abrir a câmera: $erro')),
      );
    }
  }

  Future<void> _capturarGps(BuildContext context) async {
    try {
      final RegistroLocalizacao registro =
          await evidenciasGateway.obterLocalizacao();
      estado.registrarGps(
        latitude: registro.latitude,
        longitude: registro.longitude,
        precisaoM: registro.precisaoM,
      );
    } catch (erro) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Não foi possível obter a localização: $erro')),
      );
    }
  }

  void _concluir(BuildContext context) {
    estado.avancarPara(StatusOS.validacao);
    Navigator.of(context).popUntil((Route<void> rota) => rota.isFirst);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: estado,
      builder: (BuildContext context, Widget? _) {
        final PontoVegetacao ponto = estado.ponto;

        return Scaffold(
          appBar: AppBar(title: const Text('Comprovação de execução')),
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(Espacos.x5),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  _Progresso(reunidas: estado.evidenciasReunidas),
                  const SizedBox(height: Espacos.x5),
                  CartaoSecao(
                    rotulo: 'Evidência fotográfica',
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
                                aoTocar: () =>
                                    _capturarFoto(context, antes: true),
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
                                aoTocar: () =>
                                    _capturarFoto(context, antes: false),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: Espacos.x3),
                        const Text(
                          'As duas fotos são capturadas pela câmera do aparelho.',
                          style:
                              TextStyle(fontSize: 12, color: Cores.textoSuave),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: Espacos.x4),
                  _CartaoGps(
                    estado: estado,
                    ponto: ponto,
                    aoCapturar: () => _capturarGps(context),
                  ),
                  const SizedBox(height: Espacos.x4),
                  CartaoSecao(
                    rotulo: 'Detalhamento do serviço',
                    filho: Column(
                      children: <Widget>[
                        _Linha(rotulo: 'Tipo', valor: detalheServico.tipo),
                        _Linha(rotulo: 'Faixa', valor: detalheServico.faixa),
                        _Linha(
                          rotulo: 'Extensão',
                          valor: '${detalheServico.extensaoM} m',
                        ),
                        _Linha(
                          rotulo: 'Equipamento',
                          valor: detalheServico.equipamento,
                        ),
                        _Linha(
                          rotulo: 'Ordem',
                          valor: estado.ordem.id.toUpperCase(),
                        ),
                        _Linha(rotulo: 'Operador', valor: estado.operador.nome),
                      ],
                    ),
                  ),
                  const SizedBox(height: Espacos.x4),
                  CartaoSecao(
                    rotulo: 'Ponto da ordem',
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
                    label: const Text('Enviar para validação'),
                  ),
                  const SizedBox(height: Espacos.x3),
                  if (!estado.comprovacaoCompleta)
                    const Text(
                      'Faltam evidências para enviar a validação.',
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
                  ? 'Comprovação completa. Pode enviar.'
                  : 'Evidências: $reunidas de $total',
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
  const _CartaoGps({
    required this.estado,
    required this.ponto,
    required this.aoCapturar,
  });

  final EstadoOperacao estado;
  final PontoVegetacao ponto;
  final VoidCallback aoCapturar;

  @override
  Widget build(BuildContext context) {
    final bool capturado = estado.gpsCapturado;
    final double latitude = estado.gpsLatitude ?? ponto.latitude;
    final double longitude = estado.gpsLongitude ?? ponto.longitude;
    final double precisaoM = estado.gpsPrecisaoM ?? 0;

    return CartaoSecao(
      rotulo: 'Coordenada do registro',
      filho: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          if (capturado) ...<Widget>[
            Row(
              children: <Widget>[
                const Icon(
                  Icons.my_location,
                  size: 20,
                  color: Cores.riscoTranquilo,
                ),
                const SizedBox(width: Espacos.x3),
                Expanded(
                  child: Text(
                    formatarCoordenada(latitude, longitude),
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
              'Capturada às ${formatarHora(estado.gpsCapturadoEm!)} · precisão ${precisaoM.toStringAsFixed(0)} m',
              style: const TextStyle(fontSize: 12, color: Cores.textoSuave),
            ),
          ] else ...<Widget>[
            const Text(
              'A localização do aparelho registra onde a evidência foi coletada.',
              style: TextStyle(fontSize: 13, color: Cores.textoSuave),
            ),
            const SizedBox(height: Espacos.x4),
            OutlinedButton.icon(
              onPressed: aoCapturar,
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
