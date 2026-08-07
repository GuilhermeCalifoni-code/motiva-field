import 'package:flutter/foundation.dart';

import 'mock_data.dart';

/// Estado da operacao em memoria. Sem persistencia: fechou o app, recomeca.
/// Quando o backend existir, cada avanco daqui vira uma chamada de API.
class EstadoOperacao extends ChangeNotifier {
  EstadoOperacao({required Operador operador})
      : _operador = operador,
        _ordem = ordemAtivaDe(operador);

  final Operador _operador;
  OrdemServico _ordem;

  bool _fotoAntes = false;
  bool _fotoDepois = false;
  DateTime? _fotoAntesEm;
  DateTime? _fotoDepoisEm;
  DateTime? _gpsCapturadoEm;

  Operador get operador => _operador;
  OrdemServico get ordem => _ordem;
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
