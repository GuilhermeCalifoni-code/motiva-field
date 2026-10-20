import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import 'mock_data.dart';

const String _apiBase = String.fromEnvironment(
  'MOTIVA_API_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

/// Estado da operação em memória. O fluxo funciona localmente e sincroniza a
/// ordem compartilhada com o backend quando ele está disponível.
class EstadoOperacao extends ChangeNotifier {
  EstadoOperacao({required Operador operador})
      : _operador = operador,
        _ordem = ordemAtivaDe(operador) {
    unawaited(_conectarOrdemCompartilhada());
  }

  final Operador _operador;
  OrdemServico _ordem;
  String? _ordemRemotaId;
  String _sincronizacao = 'Conectando ao banco compartilhado...';

  String? _fotoAntesPath;
  String? _fotoDepoisPath;
  DateTime? _fotoAntesEm;
  DateTime? _fotoDepoisEm;
  DateTime? _gpsCapturadoEm;
  double? _gpsLatitude;
  double? _gpsLongitude;
  double? _gpsPrecisaoM;

  Operador get operador => _operador;
  OrdemServico get ordem => _ordem;
  String get sincronizacao => _sincronizacao;
  bool get conectadoAoBanco => _ordemRemotaId != null;
  PontoVegetacao get ponto => pontoPorId(_ordem.pontoId);

  bool get fotoAntes => _fotoAntesPath != null;
  bool get fotoDepois => _fotoDepoisPath != null;
  String? get fotoAntesPath => _fotoAntesPath;
  String? get fotoDepoisPath => _fotoDepoisPath;
  DateTime? get fotoAntesEm => _fotoAntesEm;
  DateTime? get fotoDepoisEm => _fotoDepoisEm;
  DateTime? get gpsCapturadoEm => _gpsCapturadoEm;
  double? get gpsLatitude => _gpsLatitude;
  double? get gpsLongitude => _gpsLongitude;
  double? get gpsPrecisaoM => _gpsPrecisaoM;
  bool get gpsCapturado =>
      _gpsCapturadoEm != null && _gpsLatitude != null && _gpsLongitude != null;

  /// Sem as duas fotos reais e a coordenada do aparelho, a evidência permanece
  /// incompleta e não pode ser enviada para validação.
  bool get comprovacaoCompleta => fotoAntes && fotoDepois && gpsCapturado;

  int get evidenciasReunidas =>
      (fotoAntes ? 1 : 0) + (fotoDepois ? 1 : 0) + (gpsCapturado ? 1 : 0);

  void avancarPara(StatusOS novo) {
    _ordem = _ordem.avancarPara(novo, DateTime.now());
    notifyListeners();
    if (_ordemRemotaId != null) {
      unawaited(_sincronizarStatus(novo));
    }
  }

  Future<void> _conectarOrdemCompartilhada() async {
    try {
      final http.Response resposta = await http
          .get(Uri.parse('$_apiBase/api/operacao/ordens'))
          .timeout(const Duration(seconds: 8));
      if (resposta.statusCode != 200) throw StateError('API indisponível');
      final List<dynamic> ordens = jsonDecode(resposta.body) as List<dynamic>;
      final Map<String, dynamic>? remota = ordens
          .cast<Map<String, dynamic>>()
          .where((Map<String, dynamic> item) => item['status'] != 'concluida')
          .cast<Map<String, dynamic>?>()
          .firstOrNull;
      if (remota == null) throw StateError('Sem ordem aberta');
      _ordemRemotaId = remota['id']?.toString();
      _sincronizacao = 'Supabase conectado · ordem compartilhada';
    } catch (_) {
      _sincronizacao = 'Modo local de contingência · banco indisponível';
    }
    notifyListeners();
  }

  Future<void> _sincronizarStatus(StatusOS status) async {
    final String? id = _ordemRemotaId;
    if (id == null) return;
    try {
      final http.Response resposta = await http
          .patch(
            Uri.parse('$_apiBase/api/operacao/ordens/$id/status'),
            headers: const <String, String>{'Content-Type': 'application/json'},
            body: jsonEncode(<String, String>{'status': status.name}),
          )
          .timeout(const Duration(seconds: 8));
      if (resposta.statusCode != 200) {
        throw StateError('Falha de sincronização');
      }
      _sincronizacao = 'Supabase sincronizado agora';
    } catch (_) {
      _sincronizacao = 'Alteração local pendente de sincronização';
    }
    notifyListeners();
  }

  void registrarFotoAntes(String caminho) {
    _fotoAntesPath = caminho;
    _fotoAntesEm = DateTime.now();
    notifyListeners();
  }

  void registrarFotoDepois(String caminho) {
    _fotoDepoisPath = caminho;
    _fotoDepoisEm = DateTime.now();
    notifyListeners();
  }

  void registrarGps({
    required double latitude,
    required double longitude,
    required double precisaoM,
  }) {
    _gpsLatitude = latitude;
    _gpsLongitude = longitude;
    _gpsPrecisaoM = precisaoM;
    _gpsCapturadoEm = DateTime.now();
    notifyListeners();
  }
}
