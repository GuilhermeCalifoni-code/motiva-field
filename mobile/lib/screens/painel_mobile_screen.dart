import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:image_picker/image_picker.dart';

import '../estado_operacao.dart';
import '../mock_data.dart';
import '../theme.dart';
import '../widgets/card_ordem.dart';
import '../widgets/cartao_secao.dart';
import '../widgets/selo_risco.dart';
import 'comprovacao_screen.dart';
import 'navegacao_screen.dart';

const String _apiBase = String.fromEnvironment(
  'MOTIVA_API_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

class PainelMobileScreen extends StatefulWidget {
  const PainelMobileScreen({super.key, required this.estado});

  final EstadoOperacao estado;

  @override
  State<PainelMobileScreen> createState() => _PainelMobileScreenState();
}

class _PainelMobileScreenState extends State<PainelMobileScreen> {
  int _indice = 0;

  static const List<String> _titulos = <String>[
    'Visão geral',
    'Ordem ativa',
    'Mapa operacional',
    'Inteligência',
  ];

  void _abrirAba(int indice) => setState(() => _indice = indice);

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.estado,
      builder: (BuildContext context, Widget? _) {
        return Scaffold(
          appBar: AppBar(
            titleSpacing: Espacos.x4,
            title: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Text(
                  'MOTIVA FIELD',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.2,
                  ),
                ),
                Text(
                  _titulos[_indice],
                  style: const TextStyle(fontSize: 11, color: Cores.sobreRoxo),
                ),
              ],
            ),
            actions: <Widget>[
              IconButton(
                tooltip: 'Notificações',
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text(
                        '3 pontos críticos e uma validação aguardando decisão.',
                      ),
                    ),
                  );
                },
                icon: const Badge(
                  smallSize: 7,
                  child: Icon(Icons.notifications_none_rounded),
                ),
              ),
              Padding(
                padding: const EdgeInsets.only(right: Espacos.x3),
                child: CircleAvatar(
                  radius: 16,
                  backgroundColor: Cores.ouro,
                  child: Text(
                    widget.estado.operador.primeiroNome.substring(0, 1),
                    style: const TextStyle(
                      color: Cores.roxoEscuro,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ),
            ],
          ),
          body: IndexedStack(
            index: _indice,
            children: <Widget>[
              _ResumoTab(
                estado: widget.estado,
                abrirOrdem: () => _abrirAba(1),
                abrirInteligencia: () => _abrirAba(3),
              ),
              _OrdemTab(estado: widget.estado),
              _MapaTab(abrirOrdem: () => _abrirAba(1)),
              const _InteligenciaTab(),
            ],
          ),
          bottomNavigationBar: NavigationBar(
            selectedIndex: _indice,
            onDestinationSelected: _abrirAba,
            destinations: const <NavigationDestination>[
              NavigationDestination(
                icon: Icon(Icons.grid_view_outlined),
                selectedIcon: Icon(Icons.grid_view_rounded),
                label: 'Resumo',
              ),
              NavigationDestination(
                icon: Icon(Icons.assignment_outlined),
                selectedIcon: Icon(Icons.assignment_rounded),
                label: 'Ordem',
              ),
              NavigationDestination(
                icon: Icon(Icons.map_outlined),
                selectedIcon: Icon(Icons.map_rounded),
                label: 'Mapa',
              ),
              NavigationDestination(
                icon: Icon(Icons.auto_awesome_outlined),
                selectedIcon: Icon(Icons.auto_awesome_rounded),
                label: 'IA',
              ),
            ],
          ),
        );
      },
    );
  }
}

class _ResumoTab extends StatelessWidget {
  const _ResumoTab({
    required this.estado,
    required this.abrirOrdem,
    required this.abrirInteligencia,
  });

  final EstadoOperacao estado;
  final VoidCallback abrirOrdem;
  final VoidCallback abrirInteligencia;

  @override
  Widget build(BuildContext context) {
    final int criticos = pontosVegetacao
        .where((PontoVegetacao ponto) => ponto.nivelRisco == NivelRisco.critico)
        .length;
    final int abertas =
        ordensServico.where((OrdemServico ordem) => ordem.estaAberta).length;
    final PontoVegetacao prioridade = pontosVegetacao
        .where((PontoVegetacao ponto) => ponto.nivelRisco == NivelRisco.critico)
        .reduce((PontoVegetacao a, PontoVegetacao b) =>
            a.alturaAtualCm >= b.alturaAtualCm ? a : b);

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(Espacos.x4),
        children: <Widget>[
          Container(
            padding: const EdgeInsets.all(Espacos.x5),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: <Color>[Cores.roxoEscuro, Cores.roxo],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(Raios.lg),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Row(
                  children: <Widget>[
                    _PontoAoVivo(),
                    SizedBox(width: Espacos.x2),
                    Text(
                      'MONITORAMENTO ATIVO',
                      style: TextStyle(
                        fontSize: 10,
                        letterSpacing: 1,
                        fontWeight: FontWeight.w800,
                        color: Cores.sobreRoxo,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: Espacos.x4),
                Text(
                  '${saudacaoPara(DateTime.now())}, ${estado.operador.primeiroNome}',
                  style: const TextStyle(
                    fontSize: 26,
                    height: 1.08,
                    fontWeight: FontWeight.w600,
                    color: Cores.sobreEscuro,
                  ),
                ),
                const SizedBox(height: Espacos.x2),
                const Text(
                  'SP-270 · km 98 a 100 · operação de faixa de domínio',
                  style: TextStyle(fontSize: 13, color: Cores.sobreRoxo),
                ),
              ],
            ),
          ),
          const SizedBox(height: Espacos.x4),
          Row(
            children: <Widget>[
              Expanded(
                child: _Kpi(
                  valor: '$criticos',
                  rotulo: 'Críticos',
                  detalhe: 'agir agora',
                  cor: Cores.perigo,
                ),
              ),
              const SizedBox(width: Espacos.x2),
              Expanded(
                child: _Kpi(
                  valor: '$abertas',
                  rotulo: 'No ciclo',
                  detalhe: estado.ordem.status.rotulo,
                  cor: Cores.roxo,
                ),
              ),
              const SizedBox(width: Espacos.x2),
              const Expanded(
                child: _Kpi(
                  valor: '24°',
                  rotulo: 'Clima',
                  detalhe: 'Parcialmente nublado',
                  cor: Color(0xFF3B82F6),
                ),
              ),
            ],
          ),
          const SizedBox(height: Espacos.x4),
          CartaoSecao(
            rotulo: 'Decisão recomendada',
            filho: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Row(
                  children: <Widget>[
                    Expanded(
                      child: Text(
                        'Atuar no km ${prioridade.kmFormatado}',
                        style: const TextStyle(
                          fontSize: 21,
                          fontWeight: FontWeight.w700,
                          color: Cores.texto,
                        ),
                      ),
                    ),
                    SeloRisco(nivelRisco: prioridade.nivelRisco),
                  ],
                ),
                const SizedBox(height: Espacos.x2),
                Text(
                  'Vegetação registrada em ${prioridade.alturaAtualCm} cm, com invasão de pista e placa em risco.',
                  style: const TextStyle(
                    fontSize: 13,
                    height: 1.45,
                    color: Cores.textoSuave,
                  ),
                ),
                const SizedBox(height: Espacos.x4),
                ElevatedButton.icon(
                  onPressed: abrirOrdem,
                  icon: const Icon(Icons.assignment_outlined),
                  label: const Text('Abrir ordem ativa'),
                ),
              ],
            ),
          ),
          const SizedBox(height: Espacos.x4),
          const _ClimaCard(),
          const SizedBox(height: Espacos.x4),
          _FluxoOperacional(status: estado.ordem.status),
          const SizedBox(height: Espacos.x4),
          CartaoSecao(
            rotulo: 'Visão computacional',
            filho: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Text(
                  'Medição com régua transparente liberada',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: Cores.texto,
                  ),
                ),
                const SizedBox(height: Espacos.x2),
                const Text(
                  'Sem escala ou calibração, o aplicativo preserva altura_cm = null e encaminha a foto somente para triagem.',
                  style: TextStyle(
                    fontSize: 13,
                    height: 1.45,
                    color: Cores.textoSuave,
                  ),
                ),
                const SizedBox(height: Espacos.x4),
                OutlinedButton.icon(
                  onPressed: abrirInteligencia,
                  icon: const Icon(Icons.camera_alt_outlined),
                  label: const Text('Testar uma foto'),
                ),
              ],
            ),
          ),
          const SizedBox(height: Espacos.x6),
        ],
      ),
    );
  }
}

class _Kpi extends StatelessWidget {
  const _Kpi({
    required this.valor,
    required this.rotulo,
    required this.detalhe,
    required this.cor,
  });

  final String valor;
  final String rotulo;
  final String detalhe;
  final Color cor;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 112),
      padding: const EdgeInsets.all(Espacos.x3),
      decoration: BoxDecoration(
        color: Cores.superficie,
        border: Border.all(color: Cores.borda),
        borderRadius: BorderRadius.circular(Raios.md),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Container(width: 24, height: 3, color: cor),
          const SizedBox(height: Espacos.x3),
          Text(valor, style: estiloNumero.copyWith(fontSize: 27)),
          Text(rotulo,
              style:
                  const TextStyle(fontSize: 11, fontWeight: FontWeight.w700)),
          const SizedBox(height: Espacos.x1),
          Text(detalhe,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 9, color: Cores.textoApagado)),
        ],
      ),
    );
  }
}

class _PontoAoVivo extends StatelessWidget {
  const _PontoAoVivo();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 8,
      height: 8,
      decoration: const BoxDecoration(
          color: Cores.riscoTranquilo, shape: BoxShape.circle),
    );
  }
}

class _ClimaCard extends StatelessWidget {
  const _ClimaCard();

  @override
  Widget build(BuildContext context) {
    const CondicoesLocais c = condicoesLocais;
    return CartaoSecao(
      rotulo: 'Clima e tendência de crescimento',
      filho: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: Cores.atencaoSuave,
              borderRadius: BorderRadius.circular(Raios.md),
            ),
            child: const Icon(Icons.water_drop_outlined, color: Cores.atencao),
          ),
          const SizedBox(width: Espacos.x3),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  '${c.temperaturaC.toStringAsFixed(0)}°C · ${c.condicao}',
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: Espacos.x1),
                Text(
                  '${c.chuva24hMm.toStringAsFixed(1)} mm em 24h · vento ${c.ventoKmh} km/h',
                  style: const TextStyle(fontSize: 12, color: Cores.textoSuave),
                ),
                if (c.aceleraCrescimento) ...<Widget>[
                  const SizedBox(height: Espacos.x2),
                  const Text(
                    'Chuva pode acelerar o crescimento; revise os prazos.',
                    style: TextStyle(
                        fontSize: 12,
                        color: Cores.atencaoForte,
                        fontWeight: FontWeight.w600),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _FluxoOperacional extends StatelessWidget {
  const _FluxoOperacional({required this.status});

  final StatusOS status;

  @override
  Widget build(BuildContext context) {
    final int atual = fluxoStatus.indexOf(status);
    return CartaoSecao(
      rotulo: 'Fluxo da ordem',
      filho: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children:
              fluxoStatus.asMap().entries.map((MapEntry<int, StatusOS> item) {
            final bool concluida = item.key < atual;
            final bool ativa = item.key == atual;
            return Row(
              children: <Widget>[
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  decoration: BoxDecoration(
                    color: ativa
                        ? Cores.roxo
                        : concluida
                            ? const Color(0xFFE6F4EA)
                            : Cores.fundo,
                    borderRadius: BorderRadius.circular(Raios.pill),
                    border: Border.all(color: ativa ? Cores.roxo : Cores.borda),
                  ),
                  child: Text(
                    item.value.rotulo,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: ativa
                          ? Cores.sobreEscuro
                          : concluida
                              ? Cores.riscoTranquilo
                              : Cores.textoSuave,
                    ),
                  ),
                ),
                if (item.key < fluxoStatus.length - 1)
                  Container(width: 14, height: 1, color: Cores.bordaForte),
              ],
            );
          }).toList(),
        ),
      ),
    );
  }
}

class _OrdemTab extends StatelessWidget {
  const _OrdemTab({required this.estado});

  final EstadoOperacao estado;

  void _abrirRota(BuildContext context) {
    if (estado.ordem.status == StatusOS.pendente) {
      estado.avancarPara(StatusOS.programada);
      return;
    }
    if (estado.ordem.status == StatusOS.programada) {
      estado.avancarPara(StatusOS.emDeslocamento);
    }
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (BuildContext context) => NavegacaoScreen(estado: estado),
      ),
    );
  }

  void _abrirComprovacao(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (BuildContext context) => ComprovacaoScreen(estado: estado),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final StatusOS status = estado.ordem.status;
    String acao = 'Programar ordem';
    VoidCallback? executar = () => _abrirRota(context);
    IconData icone = Icons.calendar_month_outlined;
    if (status == StatusOS.programada) {
      acao = 'Iniciar deslocamento';
      icone = Icons.navigation_outlined;
    } else if (status == StatusOS.emDeslocamento) {
      acao = 'Continuar navegacao';
      icone = Icons.navigation_rounded;
    } else if (status == StatusOS.noLocal) {
      acao = 'Registrar evidências';
      icone = Icons.camera_alt_outlined;
      executar = () => _abrirComprovacao(context);
    } else if (status == StatusOS.validacao) {
      acao = 'Aguardando validação do gestor';
      icone = Icons.fact_check_outlined;
      executar = null;
    } else if (status == StatusOS.concluida) {
      acao = 'Serviço concluído';
      icone = Icons.verified_outlined;
      executar = null;
    }

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(Espacos.x4),
        children: <Widget>[
          _FluxoOperacional(status: status),
          const SizedBox(height: Espacos.x4),
          CardOrdem(ordem: estado.ordem, ponto: estado.ponto),
          const SizedBox(height: Espacos.x4),
          const _ClimaCard(),
          const SizedBox(height: Espacos.x4),
          ElevatedButton.icon(
            onPressed: executar,
            icon: Icon(icone),
            label: Text(acao),
          ),
          if (status == StatusOS.validacao) ...<Widget>[
            const SizedBox(height: Espacos.x3),
            const Text(
              'As evidências já foram enviadas. A etapa Concluída é controlada pelo gestor no web.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: Cores.textoSuave),
            ),
          ],
          const SizedBox(height: Espacos.x6),
        ],
      ),
    );
  }
}

class _MapaTab extends StatelessWidget {
  const _MapaTab({required this.abrirOrdem});

  final VoidCallback abrirOrdem;

  @override
  Widget build(BuildContext context) {
    final List<PontoVegetacao> fila = <PontoVegetacao>[...pontosVegetacao]
      ..sort((PontoVegetacao a, PontoVegetacao b) =>
          b.alturaAtualCm.compareTo(a.alturaAtualCm));
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(Espacos.x4),
        children: <Widget>[
          Container(
            height: 280,
            decoration: BoxDecoration(
              color: const Color(0xFFEDE9F3),
              border: Border.all(color: Cores.borda),
              borderRadius: BorderRadius.circular(Raios.lg),
            ),
            clipBehavior: Clip.antiAlias,
            child: Stack(
              children: <Widget>[
                const Positioned.fill(
                    child: CustomPaint(painter: _PintorTrecho())),
                Positioned(
                  left: Espacos.x3,
                  top: Espacos.x3,
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
                    decoration: BoxDecoration(
                        color: Cores.superficie,
                        borderRadius: BorderRadius.circular(Raios.pill)),
                    child: const Text('MALHA DEMONSTRATIVA',
                        style: TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.w800,
                            color: Cores.textoSuave)),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: Espacos.x4),
          const Text('Fila no trecho',
              style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                  color: Cores.texto)),
          const SizedBox(height: Espacos.x2),
          for (final PontoVegetacao ponto in fila.take(5))
            Container(
              margin: const EdgeInsets.only(bottom: Espacos.x2),
              padding: const EdgeInsets.all(Espacos.x3),
              decoration: BoxDecoration(
                  color: Cores.superficie,
                  border: Border.all(color: Cores.borda),
                  borderRadius: BorderRadius.circular(Raios.md)),
              child: Row(
                children: <Widget>[
                  Container(
                      width: 4,
                      height: 42,
                      decoration: BoxDecoration(
                          color: _corRisco(ponto.nivelRisco),
                          borderRadius: BorderRadius.circular(4))),
                  const SizedBox(width: Espacos.x3),
                  Expanded(
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                        Text('${ponto.rodovia} · km ${ponto.kmFormatado}',
                            style: const TextStyle(
                                fontSize: 14, fontWeight: FontWeight.w700)),
                        Text(
                            '${ponto.alturaAtualCm} cm · sentido ${ponto.sentido.rotulo}',
                            style: const TextStyle(
                                fontSize: 11, color: Cores.textoSuave))
                      ])),
                  SeloRisco(nivelRisco: ponto.nivelRisco),
                ],
              ),
            ),
          const SizedBox(height: Espacos.x2),
          OutlinedButton.icon(
              onPressed: abrirOrdem,
              icon: const Icon(Icons.assignment_outlined),
              label: const Text('Abrir ordem prioritaria')),
          const SizedBox(height: Espacos.x6),
        ],
      ),
    );
  }

  static Color _corRisco(NivelRisco risco) {
    switch (risco) {
      case NivelRisco.critico:
        return Cores.perigo;
      case NivelRisco.atencao:
        return Cores.atencao;
      case NivelRisco.tranquilo:
        return Cores.riscoTranquilo;
    }
  }
}

class _PintorTrecho extends CustomPainter {
  const _PintorTrecho();

  @override
  void paint(Canvas canvas, Size size) {
    final Paint base = Paint()
      ..color = Cores.bordaForte
      ..strokeWidth = 18
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    final Paint eixo = Paint()
      ..color = Cores.roxo
      ..strokeWidth = 7
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    final Path caminho = Path()
      ..moveTo(size.width * .08, size.height * .78)
      ..cubicTo(size.width * .28, size.height * .52, size.width * .53,
          size.height * .72, size.width * .92, size.height * .22);
    canvas.drawPath(caminho, base);
    canvas.drawPath(caminho, eixo);
    const List<Offset> pontos = <Offset>[
      Offset(.16, .69),
      Offset(.32, .59),
      Offset(.50, .57),
      Offset(.68, .46),
      Offset(.84, .29)
    ];
    for (int i = 0; i < pontos.length; i++) {
      final Offset p =
          Offset(size.width * pontos[i].dx, size.height * pontos[i].dy);
      canvas.drawCircle(
          p, 10, Paint()..color = i < 3 ? Cores.perigo : Cores.atencao);
      canvas.drawCircle(p, 4, Paint()..color = Cores.superficie);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _InteligenciaTab extends StatefulWidget {
  const _InteligenciaTab();

  @override
  State<_InteligenciaTab> createState() => _InteligenciaTabState();
}

class _InteligenciaTabState extends State<_InteligenciaTab> {
  final ImagePicker _picker = ImagePicker();
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _referenciaController =
      TextEditingController(text: '20');
  XFile? _foto;
  bool _exemploValidado = false;
  bool _assistidoAtivo = false;
  bool _coplanarConfirmado = false;
  double _aspectoImagem = 4 / 3;
  final List<Offset> _pontosAssistidos = <Offset>[];
  Map<String, dynamic>? _resultado;
  bool _carregando = false;
  String? _erro;

  @override
  void dispose() {
    _scrollController.dispose();
    _referenciaController.dispose();
    super.dispose();
  }

  Future<void> _selecionar(ImageSource origem) async {
    final XFile? foto = await _picker.pickImage(
      source: origem,
      preferredCameraDevice: CameraDevice.rear,
    );
    if (foto == null || !mounted) return;
    final Uint8List bytes = await foto.readAsBytes();
    final ui.Codec codec = await ui.instantiateImageCodec(bytes);
    final ui.FrameInfo frame = await codec.getNextFrame();
    final double aspecto = frame.image.width / frame.image.height;
    frame.image.dispose();
    codec.dispose();
    if (!mounted) return;
    setState(() {
      _foto = foto;
      _aspectoImagem = aspecto;
      _exemploValidado = false;
      _assistidoAtivo = false;
      _coplanarConfirmado = false;
      _pontosAssistidos.clear();
      _resultado = null;
      _erro = null;
    });
  }

  Future<void> _executarExemplo() async {
    setState(() {
      _foto = null;
      _exemploValidado = true;
      _assistidoAtivo = false;
      _coplanarConfirmado = false;
      _pontosAssistidos.clear();
      _resultado = null;
      _erro = null;
    });
    await _analisar();
  }

  Future<void> _analisar() async {
    if (_foto == null && !_exemploValidado) return;
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final http.MultipartRequest pedido = http.MultipartRequest(
        'POST',
        Uri.parse('$_apiBase/api/medicoes-altura'),
      );
      if (_exemploValidado) {
        final ByteData dados =
            await rootBundle.load('assets/demo/foto-regua-validada.png');
        pedido.files.add(
          http.MultipartFile.fromBytes(
            'imagem',
            dados.buffer.asUint8List(),
            filename: 'foto-regua-validada.png',
            contentType: MediaType('image', 'png'),
          ),
        );
      } else {
        pedido.files.add(
          await http.MultipartFile.fromPath(
            'imagem',
            _foto!.path,
            contentType: MediaType.parse(_foto!.mimeType ?? 'image/jpeg'),
          ),
        );
      }
      final http.StreamedResponse resposta =
          await pedido.send().timeout(const Duration(seconds: 90));
      final String corpo = await resposta.stream.bytesToString();
      final dynamic decodificado = jsonDecode(corpo);
      if (resposta.statusCode < 200 || resposta.statusCode >= 300) {
        final String detalhe = decodificado is Map<String, dynamic>
            ? (decodificado['detail']?.toString() ?? 'Falha na analise')
            : 'Falha na analise';
        throw Exception(detalhe);
      }
      if (!mounted) return;
      setState(
          () => _resultado = Map<String, dynamic>.from(decodificado as Map));
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted || !_scrollController.hasClients) return;
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 500),
          curve: Curves.easeOutCubic,
        );
      });
    } catch (erro) {
      if (!mounted) return;
      setState(() => _erro = 'Não foi possível acessar a API local: $erro');
    } finally {
      if (mounted) setState(() => _carregando = false);
    }
  }

  void _alternarAssistido() {
    if (_foto == null) {
      setState(() => _erro = 'Selecione uma foto antes de marcar os pontos.');
      return;
    }
    setState(() {
      _assistidoAtivo = !_assistidoAtivo;
      _pontosAssistidos.clear();
      _coplanarConfirmado = false;
      _resultado = null;
      _erro = null;
    });
  }

  Future<void> _calcularAssistido() async {
    final double? referenciaCm =
        double.tryParse(_referenciaController.text.replaceAll(',', '.'));
    if (_foto == null ||
        _pontosAssistidos.length != 4 ||
        !_coplanarConfirmado ||
        referenciaCm == null ||
        referenciaCm <= 0) {
      setState(() => _erro =
          'Confirme a referência, os quatro pontos e o mesmo plano físico.');
      return;
    }
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final http.MultipartRequest pedido = http.MultipartRequest(
        'POST',
        Uri.parse('$_apiBase/api/medicoes-assistidas'),
      );
      pedido.files.add(
        await http.MultipartFile.fromPath(
          'imagem',
          _foto!.path,
          contentType: MediaType.parse(_foto!.mimeType ?? 'image/jpeg'),
        ),
      );
      const List<String> campos = <String>[
        'referencia_inicio',
        'referencia_fim',
        'base',
        'topo'
      ];
      pedido.fields['comprimento_referencia_cm'] = referenciaCm.toString();
      for (int i = 0; i < _pontosAssistidos.length; i++) {
        pedido.fields['${campos[i]}_x'] =
            _pontosAssistidos[i].dx.toStringAsFixed(7);
        pedido.fields['${campos[i]}_y'] =
            _pontosAssistidos[i].dy.toStringAsFixed(7);
      }
      pedido.fields['coplanar_confirmado'] = 'true';
      pedido.fields['coordenadas_normalizadas'] = 'true';
      final http.StreamedResponse resposta =
          await pedido.send().timeout(const Duration(seconds: 90));
      final String corpo = await resposta.stream.bytesToString();
      final dynamic decodificado = jsonDecode(corpo);
      if (resposta.statusCode < 200 || resposta.statusCode >= 300) {
        final String detalhe = decodificado is Map<String, dynamic>
            ? (decodificado['detail']?.toString() ?? 'Geometria inválida')
            : 'Geometria inválida';
        throw Exception(detalhe);
      }
      if (!mounted) return;
      setState(
          () => _resultado = Map<String, dynamic>.from(decodificado as Map));
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted || !_scrollController.hasClients) return;
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 500),
          curve: Curves.easeOutCubic,
        );
      });
    } catch (erro) {
      if (!mounted) return;
      setState(() => _erro = 'Medição assistida não concluída: $erro');
    } finally {
      if (mounted) setState(() => _carregando = false);
    }
  }

  Widget _construirPreview() {
    if (_assistidoAtivo && _foto != null) {
      return LayoutBuilder(
          builder: (BuildContext context, BoxConstraints constraints) {
        final double largura = constraints.maxWidth;
        final double altura = largura / _aspectoImagem;
        return Container(
          height: altura,
          decoration: BoxDecoration(
            color: const Color(0xFF17131F),
            border: Border.all(color: Cores.roxo, width: 2),
            borderRadius: BorderRadius.circular(Raios.lg),
          ),
          clipBehavior: Clip.antiAlias,
          child: GestureDetector(
            onTapDown: (TapDownDetails detalhe) {
              if (_pontosAssistidos.length >= 4) return;
              setState(() {
                _pontosAssistidos.add(Offset(
                  (detalhe.localPosition.dx / largura).clamp(0, 1),
                  (detalhe.localPosition.dy / altura).clamp(0, 1),
                ));
                _resultado = null;
              });
            },
            child: Stack(
              fit: StackFit.expand,
              children: <Widget>[
                Image.file(File(_foto!.path), fit: BoxFit.fill),
                CustomPaint(
                    painter: _PintorMedicaoAssistida(_pontosAssistidos)),
              ],
            ),
          ),
        );
      });
    }
    return Container(
      height: 230,
      decoration: BoxDecoration(
          color: Cores.superficie,
          border: Border.all(color: Cores.bordaForte),
          borderRadius: BorderRadius.circular(Raios.lg)),
      clipBehavior: Clip.antiAlias,
      child: _exemploValidado
          ? Image.asset('assets/demo/foto-regua-validada.png',
              fit: BoxFit.cover, width: double.infinity)
          : _foto == null
              ? const Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: <Widget>[
                    Icon(Icons.add_a_photo_outlined,
                        size: 42, color: Cores.textoApagado),
                    SizedBox(height: Espacos.x2),
                    Text('Capture ou selecione uma foto',
                        style: TextStyle(color: Cores.textoSuave))
                  ],
                )
              : Image.file(File(_foto!.path),
                  fit: BoxFit.cover, width: double.infinity),
    );
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: ListView(
        controller: _scrollController,
        padding: const EdgeInsets.all(Espacos.x4),
        children: <Widget>[
          const Text('Medição por imagem',
              style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w700,
                  color: Cores.texto)),
          const SizedBox(height: Espacos.x2),
          const Text(
              'Gemini localiza a evidência; o código determinístico calcula e bloqueia centímetros sem consenso.',
              style: TextStyle(
                  fontSize: 13, height: 1.45, color: Cores.textoSuave)),
          const SizedBox(height: Espacos.x4),
          _construirPreview(),
          const SizedBox(height: Espacos.x3),
          Row(
            children: <Widget>[
              Expanded(
                  child: OutlinedButton.icon(
                      onPressed: () => _selecionar(ImageSource.camera),
                      icon: const Icon(Icons.camera_alt_outlined),
                      label: const Text('Câmera'))),
              const SizedBox(width: Espacos.x2),
              Expanded(
                  child: OutlinedButton.icon(
                      onPressed: () => _selecionar(ImageSource.gallery),
                      icon: const Icon(Icons.photo_library_outlined),
                      label: const Text('Galeria'))),
            ],
          ),
          const SizedBox(height: Espacos.x2),
          OutlinedButton.icon(
            onPressed: _carregando ? null : _alternarAssistido,
            icon: const Icon(Icons.straighten_outlined),
            label: Text(_assistidoAtivo
                ? 'Fechar medição assistida'
                : 'Medir com referência + 4 pontos'),
          ),
          if (_assistidoAtivo) ...<Widget>[
            const SizedBox(height: Espacos.x3),
            Container(
              padding: const EdgeInsets.all(Espacos.x3),
              decoration: BoxDecoration(
                color: const Color(0xFFFFF8ED),
                border: Border.all(color: Cores.atencao),
                borderRadius: BorderRadius.circular(Raios.md),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Row(children: <Widget>[
                    const Expanded(
                      child: Text('FALLBACK MATEMÁTICO',
                          style: TextStyle(
                              fontSize: 10,
                              letterSpacing: 1,
                              fontWeight: FontWeight.w900,
                              color: Cores.atencaoForte)),
                    ),
                    Text('${_pontosAssistidos.length}/4 pontos',
                        style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            color: Cores.atencaoForte)),
                  ]),
                  const SizedBox(height: Espacos.x3),
                  TextField(
                    controller: _referenciaController,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                      labelText: 'Intervalo físico da régua (cm)',
                      suffixText: 'cm',
                    ),
                  ),
                  const SizedBox(height: Espacos.x3),
                  for (final MapEntry<int, String> item in const <String>[
                    'Início da referência',
                    'Fim da referência',
                    'Base da vegetação',
                    'Topo da vegetação'
                  ].asMap().entries)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Row(children: <Widget>[
                        Icon(
                          _pontosAssistidos.length > item.key
                              ? Icons.check_circle
                              : Icons.radio_button_unchecked,
                          size: 18,
                          color: _pontosAssistidos.length > item.key
                              ? Cores.riscoTranquilo
                              : Cores.textoApagado,
                        ),
                        const SizedBox(width: Espacos.x2),
                        Text('${item.key + 1}. ${item.value}',
                            style: const TextStyle(
                                fontSize: 12, color: Cores.texto)),
                      ]),
                    ),
                  CheckboxListTile(
                    value: _coplanarConfirmado,
                    contentPadding: EdgeInsets.zero,
                    dense: true,
                    controlAffinity: ListTileControlAffinity.leading,
                    title: const Text(
                      'Régua e vegetação estão lado a lado no mesmo plano físico.',
                      style: TextStyle(fontSize: 11, color: Cores.textoSuave),
                    ),
                    onChanged: (bool? valor) =>
                        setState(() => _coplanarConfirmado = valor ?? false),
                  ),
                  Row(children: <Widget>[
                    Expanded(
                      child: TextButton(
                        onPressed: _pontosAssistidos.isEmpty
                            ? null
                            : () => setState(() {
                                  _pontosAssistidos.removeLast();
                                  _resultado = null;
                                }),
                        child: const Text('Desfazer'),
                      ),
                    ),
                    Expanded(
                      child: TextButton(
                        onPressed: () => setState(() {
                          _pontosAssistidos.clear();
                          _resultado = null;
                        }),
                        child: const Text('Recomeçar'),
                      ),
                    ),
                  ]),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _carregando ||
                              _pontosAssistidos.length != 4 ||
                              !_coplanarConfirmado
                          ? null
                          : _calcularAssistido,
                      icon: const Icon(Icons.calculate_outlined),
                      label: Text(_carregando
                          ? 'Calculando geometria...'
                          : 'Calcular medida assistida'),
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: Espacos.x2),
          OutlinedButton.icon(
            onPressed: _carregando ? null : _executarExemplo,
            icon: const Icon(Icons.verified_outlined),
            label: const Text('Executar exemplo validado'),
          ),
          const SizedBox(height: Espacos.x3),
          ElevatedButton.icon(
              onPressed: (_foto == null && !_exemploValidado) || _carregando
                  ? null
                  : _analisar,
              icon: const Icon(Icons.auto_awesome),
              label: Text(_carregando
                  ? 'Validando evidência...'
                  : 'Analisar e validar altura')),
          if (_erro != null) ...<Widget>[
            const SizedBox(height: Espacos.x3),
            _Aviso(
                tipo: _TipoAviso.erro,
                titulo: 'API indisponível',
                mensagem: _erro!)
          ],
          if (_resultado != null) ...<Widget>[
            const SizedBox(height: Espacos.x4),
            _ResultadoInteligencia(resultado: _resultado!)
          ],
          const SizedBox(height: Espacos.x3),
          const _Aviso(
              tipo: _TipoAviso.info,
              titulo: 'Protocolo de captura',
              mensagem:
                  'Use a câmera principal 1×, sem zoom, e preserve a imagem original. Posicione a régua no mesmo plano da vegetação; se a automação falhar, confirme os quatro pontos.'),
          const SizedBox(height: Espacos.x6),
        ],
      ),
    );
  }
}

class _PintorMedicaoAssistida extends CustomPainter {
  const _PintorMedicaoAssistida(this.pontos);

  final List<Offset> pontos;

  @override
  void paint(Canvas canvas, Size size) {
    Offset real(Offset ponto) =>
        Offset(ponto.dx * size.width, ponto.dy * size.height);
    final Paint referencia = Paint()
      ..color = Cores.atencao
      ..strokeWidth = 4
      ..strokeCap = StrokeCap.round;
    final Paint alvo = Paint()
      ..color = Cores.riscoTranquilo
      ..strokeWidth = 4
      ..strokeCap = StrokeCap.round;
    if (pontos.length >= 2) {
      canvas.drawLine(real(pontos[0]), real(pontos[1]), referencia);
    }
    if (pontos.length >= 4) {
      canvas.drawLine(real(pontos[2]), real(pontos[3]), alvo);
    }
    for (int i = 0; i < pontos.length; i++) {
      final Offset centro = real(pontos[i]);
      canvas.drawCircle(centro, 11, Paint()..color = Colors.white);
      canvas.drawCircle(centro, 8, i < 2 ? referencia : alvo);
      final TextPainter numero = TextPainter(
        text: TextSpan(
          text: '${i + 1}',
          style: const TextStyle(
              color: Colors.white, fontSize: 10, fontWeight: FontWeight.w900),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      numero.paint(
          canvas, centro - Offset(numero.width / 2, numero.height / 2));
    }
  }

  @override
  bool shouldRepaint(covariant _PintorMedicaoAssistida oldDelegate) => true;
}

class _ResultadoInteligencia extends StatelessWidget {
  const _ResultadoInteligencia({required this.resultado});

  final Map<String, dynamic> resultado;

  @override
  Widget build(BuildContext context) {
    final bool valido = resultado['valido'] == true;
    final bool assistido =
        resultado['nivel_validacao']?.toString() == 'assistido_operador';
    final num? altura = resultado['altura_cm'] as num?;
    final Map<String, dynamic>? estimativa = resultado['estimativa_assistida']
            is Map
        ? Map<String, dynamic>.from(resultado['estimativa_assistida'] as Map)
        : null;
    final num confianca = resultado['confianca'] as num? ?? 0;
    final String metodo =
        (resultado['metodo']?.toString() ?? 'Sem método métrico liberado')
            .replaceAll('_', ' ');
    final List<dynamic>? intervalo =
        resultado['intervalo_cm'] as List<dynamic>?;
    final Map<String, dynamic>? auditoria = resultado['auditoria'] is Map
        ? Map<String, dynamic>.from(resultado['auditoria'] as Map)
        : null;
    final Map<String, dynamic>? baseTopo = auditoria?['base_topo'] is Map
        ? Map<String, dynamic>.from(auditoria!['base_topo'] as Map)
        : null;
    final Map<String, dynamic>? alvo = auditoria?['alvo'] is Map
        ? Map<String, dynamic>.from(auditoria!['alvo'] as Map)
        : null;
    final num? confiancaVisual = alvo?['confianca'] as num?;
    final List<dynamic> referencias =
        auditoria?['referencias'] as List<dynamic>? ?? <dynamic>[];
    final Map<String, dynamic>? consenso = resultado['consenso'] is Map
        ? Map<String, dynamic>.from(resultado['consenso'] as Map)
        : null;
    final bool referencia = referencias
        .any((dynamic item) => item is Map && item['utilizavel'] == true);
    final List<MapEntry<String, bool>> checklist = assistido
        ? <MapEntry<String, bool>>[
            const MapEntry<String, bool>('Referência física informada', true),
            const MapEntry<String, bool>('Quatro pontos confirmados', true),
            const MapEntry<String, bool>('Coplanaridade confirmada', true),
            const MapEntry<String, bool>('Geometria calculada', true),
            const MapEntry<String, bool>('Revisão para histórico', false),
          ]
        : <MapEntry<String, bool>>[
            MapEntry<String, bool>('Auditoria visual', auditoria != null),
            MapEntry<String, bool>(
                'Base e topo compatíveis',
                baseTopo?['compativeis'] == true &&
                    baseTopo?['base_visivel'] == true &&
                    baseTopo?['topo_visivel'] == true),
            MapEntry<String, bool>('Referência métrica', referencia || valido),
            MapEntry<String, bool>('Consenso independente', valido),
            MapEntry<String, bool>('Centímetros autorizados', valido),
          ];

    return Container(
      padding: const EdgeInsets.all(Espacos.x4),
      decoration: BoxDecoration(
          color: Cores.superficie,
          border: Border.all(
              color: assistido
                  ? Cores.atencao
                  : valido
                      ? Cores.riscoTranquilo
                      : Cores.atencao),
          borderRadius: BorderRadius.circular(Raios.lg)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
              assistido
                  ? 'MEDIÇÃO MATEMÁTICA ASSISTIDA'
                  : valido
                      ? 'ALTURA VALIDADA'
                      : 'MEDIÇÃO BLOQUEADA',
              style: TextStyle(
                  fontSize: 10,
                  letterSpacing: 1,
                  fontWeight: FontWeight.w800,
                  color: assistido
                      ? Cores.atencaoForte
                      : valido
                          ? Cores.riscoTranquilo
                          : Cores.atencaoForte)),
          const SizedBox(height: Espacos.x2),
          if (altura != null)
            Row(crossAxisAlignment: CrossAxisAlignment.end, children: <Widget>[
              Text(altura.toStringAsFixed(1),
                  style: estiloNumero.copyWith(
                      fontSize: 52,
                      color: assistido
                          ? Cores.atencaoForte
                          : Cores.riscoTranquilo)),
              Padding(
                  padding: const EdgeInsets.only(bottom: 7, left: 5),
                  child: Text('cm',
                      style: TextStyle(
                          fontWeight: FontWeight.w800,
                          color: assistido
                              ? Cores.atencaoForte
                              : Cores.riscoTranquilo)))
            ])
          else if (estimativa != null) ...<Widget>[
            const Text('ESTIMATIVA ASSISTIDA · NÃO VALIDADA',
                style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w900,
                    color: Cores.atencaoForte)),
            Row(crossAxisAlignment: CrossAxisAlignment.end, children: <Widget>[
              Text((estimativa['altura_cm'] as num).toStringAsFixed(1),
                  style: estiloNumero.copyWith(
                      fontSize: 48, color: Cores.atencaoForte)),
              const Padding(
                  padding: EdgeInsets.only(bottom: 7, left: 5),
                  child: Text('cm',
                      style: TextStyle(
                          fontWeight: FontWeight.w800,
                          color: Cores.atencaoForte)))
            ]),
            Text(
                'Faixa ${estimativa['intervalo_cm'][0]}–${estimativa['intervalo_cm'][1]} cm · confiança ${((estimativa['confianca'] as num) * 100).round()}%',
                style:
                    const TextStyle(fontSize: 11, color: Cores.atencaoForte)),
            const Text('Valor oficial: altura_cm = null até consenso.',
                style: TextStyle(fontSize: 10, color: Cores.textoApagado)),
          ] else
            const Text('altura_cm = null',
                style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w800,
                    color: Cores.atencaoForte)),
          if (intervalo != null && intervalo.length >= 2)
            Text('Intervalo ${intervalo[0]}–${intervalo[1]} cm',
                style: const TextStyle(fontSize: 12, color: Cores.textoSuave)),
          const SizedBox(height: Espacos.x2),
          Text(
              assistido
                  ? 'Confiança geométrica ${(confianca * 100).round()}% · pontos humanos confirmados'
                  : 'Confiança métrica ${(confianca * 100).round()}% · visual ${confiancaVisual == null ? 'indisponível' : '${(confiancaVisual * 100).round()}%'}',
              style: const TextStyle(fontSize: 12, color: Cores.textoSuave)),
          Text(metodo,
              style: const TextStyle(fontSize: 11, color: Cores.textoApagado)),
          if (assistido) ...<Widget>[
            const SizedBox(height: Espacos.x2),
            Text(
                resultado['mensagem']?.toString() ??
                    'Medição calculada por referência física e pontos confirmados.',
                style: const TextStyle(
                    fontSize: 11, height: 1.4, color: Cores.atencaoForte)),
            const Text('Ainda não alimenta o histórico oficial.',
                style: TextStyle(fontSize: 10, color: Cores.textoApagado)),
          ],
          if (consenso != null) ...<Widget>[
            const SizedBox(height: Espacos.x1),
            Text(
              'Consenso validado\nEscala ${consenso['divergencia_escala_pct']}% · altura ${consenso['divergencia_altura_pct']}%',
              style: const TextStyle(
                  fontSize: 12,
                  color: Cores.riscoTranquilo,
                  fontWeight: FontWeight.w700),
            ),
          ],
          const Divider(height: Espacos.x6),
          const Text('CHECKLIST DE APROVAÇÃO', style: estiloRotulo),
          const SizedBox(height: Espacos.x2),
          for (final MapEntry<String, bool> item in checklist)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 5),
              child: Row(children: <Widget>[
                Icon(
                    item.value
                        ? Icons.check_circle
                        : Icons.radio_button_unchecked,
                    size: 18,
                    color:
                        item.value ? Cores.riscoTranquilo : Cores.textoApagado),
                const SizedBox(width: Espacos.x2),
                Expanded(
                    child: Text(item.key,
                        style:
                            const TextStyle(fontSize: 12, color: Cores.texto)))
              ]),
            ),
          if (!valido && resultado['pendencias'] is List) ...<Widget>[
            const Divider(height: Espacos.x6),
            for (final dynamic item in resultado['pendencias'] as List<dynamic>)
              Padding(
                  padding: const EdgeInsets.only(bottom: Espacos.x1),
                  child: Text('• $item',
                      style: const TextStyle(
                          fontSize: 11,
                          height: 1.4,
                          color: Cores.atencaoForte))),
          ],
        ],
      ),
    );
  }
}

enum _TipoAviso { info, erro }

class _Aviso extends StatelessWidget {
  const _Aviso(
      {required this.tipo, required this.titulo, required this.mensagem});

  final _TipoAviso tipo;
  final String titulo;
  final String mensagem;

  @override
  Widget build(BuildContext context) {
    final bool erro = tipo == _TipoAviso.erro;
    return Container(
      padding: const EdgeInsets.all(Espacos.x3),
      decoration: BoxDecoration(
          color: erro ? Cores.perigoSuave : const Color(0xFFF3EEFA),
          border: Border.all(color: erro ? Cores.perigoBorda : Cores.borda),
          borderRadius: BorderRadius.circular(Raios.md)),
      child:
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: <Widget>[
        Icon(erro ? Icons.error_outline : Icons.info_outline,
            size: 20, color: erro ? Cores.perigo : Cores.roxo),
        const SizedBox(width: Espacos.x2),
        Expanded(
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
              Text(titulo,
                  style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      color: erro ? Cores.perigoForte : Cores.roxo)),
              const SizedBox(height: 3),
              Text(mensagem,
                  style: const TextStyle(
                      fontSize: 11, height: 1.4, color: Cores.textoSuave))
            ]))
      ]),
    );
  }
}
