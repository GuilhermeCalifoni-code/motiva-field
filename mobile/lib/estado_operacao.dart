import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import 'mock_data.dart';

const String _apiBase = String.fromEnvironment(
  'MOTIVA_API_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

/// Estado da operacao em memoria. Sem persistencia: fechou o app, recomeca.
/// Quando o backend existir, cada avanco daqui vira uma chamada de API.
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

  bool _fotoAntes = false;
  bool _fotoDepois = false;
  DateTime? _fotoAntesEm;
  DateTime? _fotoDepoisEm;
  DateTime? _gpsCapturadoEm;

  Operador get operador => _operador;
  OrdemServico get ordem => _ordem;
  String get sincronizacao => _sincronizacao;
  bool get conectadoAoBanco => _ordemRemotaId != null;
  PontoVegetacao get ponto => pontoPorId(_ordem.pontoId);

  bool get fotoAntes => _fotoAntes;
  bool get fotoDepois => _fotoDepois;
  DateTime? get fotoAntesEm => _fotoAntesEm;
  DateTime? get fotoDepoisEm => _fotoDepoisEm;
  DateTime? get gpsCapturadoEm => _gpsCapturadoEm;
  bool get gpsCapturado => _gpsCapturadoEm != null;

  /// Sem as duas fotos e a coordenada nao ha prova de que o servico foi feito.
  bool get comprovacaoCompleta => _fotoAntes && _fotoDepois && gpsCapturado;

  int get evidenciasReunidas =>
      (_fotoAntes ? 1 : 0) + (_fotoDepois ? 1 : 0) + (gpsCapturado ? 1 : 0);

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

  void registrarFotoAntes() {
    _fotoAntes = true;
    _fotoAntesEm = DateTime.now();
    notifyListeners();
  }

  void registrarFotoDepois() {
    _fotoDepois = true;
    _fotoDepoisEm = DateTime.now();
    notifyListeners();
  }

  void capturarGps() {
    _gpsCapturadoEm = DateTime.now();
    notifyListeners();
  }
}
