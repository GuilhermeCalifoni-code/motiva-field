import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:motiva_field/main.dart';
import 'package:motiva_field/mock_data.dart';
import 'package:motiva_field/services/evidencias.dart';

class _FakeEvidenciasGateway implements EvidenciasGateway {
  int _foto = 0;

  @override
  Future<String?> capturarFoto() async {
    _foto += 1;
    return '/tmp/evidencia-$_foto.jpg';
  }

  @override
  Future<RegistroLocalizacao> obterLocalizacao() async {
    return const RegistroLocalizacao(
      latitude: -23.5505,
      longitude: -46.6333,
      precisaoM: 4,
    );
  }
}

ElevatedButton _botaoEnviar(WidgetTester tester) {
  return tester.widget<ElevatedButton>(
    find.ancestor(
      of: find.text('Enviar para validação'),
      matching: find.byType(ElevatedButton),
    ),
  );
}

Future<void> _entrarComBiometria(WidgetTester tester) async {
  final Finder botao = find.text('Entrar com biometria');
  await tester.ensureVisible(botao);
  await tester.pumpAndSettle();
  await tester.tap(botao);
  await tester.pumpAndSettle();
}

void main() {
  setUp(() {
    evidenciasGateway = _FakeEvidenciasGateway();
  });

  tearDown(() {
    evidenciasGateway = EvidenciasPluginGateway();
  });

  testWidgets('login leva para o centro operacional mobile',
      (WidgetTester tester) async {
    await tester.pumpWidget(const MotivaFieldApp());

    expect(find.text('MOTIVA FIELD'), findsOneWidget);

    await _entrarComBiometria(tester);

    expect(find.text('Visão geral'), findsOneWidget);
    expect(find.text('MONITORAMENTO ATIVO'), findsOneWidget);
    expect(find.text('Resumo'), findsOneWidget);
    expect(find.text('IA'), findsOneWidget);

    await tester.tap(find.text('IA'));
    await tester.pumpAndSettle();
    expect(find.text('Medição por imagem'), findsOneWidget);
    expect(find.text('Câmera'), findsOneWidget);
    expect(find.text('Galeria'), findsOneWidget);
  });

  testWidgets('fluxo de seis etapas envia evidencias para validacao',
      (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1200, 3000);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(const MotivaFieldApp());
    await _entrarComBiometria(tester);

    await tester.tap(find.text('Ordem'));
    await tester.pumpAndSettle();
    expect(find.text('Ordem ativa'), findsOneWidget);

    await tester.tap(find.text('Programar ordem'));
    await tester.pumpAndSettle();
    expect(find.text('Iniciar deslocamento'), findsOneWidget);

    await tester.tap(find.text('Iniciar deslocamento'));
    await tester.pumpAndSettle();
    expect(find.text('Navegação'), findsOneWidget);
    expect(find.text('DESTINO'), findsOneWidget);

    await tester.tap(find.text('Cheguei ao local'));
    await tester.pumpAndSettle();
    expect(find.text('Comprovação de execução'), findsOneWidget);

    expect(find.text('Evidências: 0 de 3'), findsOneWidget);
    expect(_botaoEnviar(tester).onPressed, isNull);

    await tester.tap(find.text('ANTES'));
    await tester.pumpAndSettle();
    expect(find.text('Evidências: 1 de 3'), findsOneWidget);

    await tester.tap(find.text('DEPOIS'));
    await tester.pumpAndSettle();
    expect(find.text('Evidências: 2 de 3'), findsOneWidget);

    await tester.tap(find.text('Capturar coordenada'));
    await tester.pumpAndSettle();
    expect(find.text('Comprovação completa. Pode enviar.'), findsOneWidget);
    expect(find.textContaining('-23.55050'), findsOneWidget);
    expect(_botaoEnviar(tester).onPressed, isNotNull);

    await tester.tap(find.text('Enviar para validação'));
    await tester.pumpAndSettle();
    expect(find.text('Ordem ativa'), findsOneWidget);
    expect(find.text('Aguardando validação do gestor'), findsOneWidget);
  });

  test('mock espelha os seis estagios do painel web', () {
    expect(pontosVegetacao.length, 8);
    expect(operadores.length, 4);
    expect(ordensServico.length, 6);
    expect(fluxoStatus.length, 6);

    for (final StatusOS status in fluxoStatus) {
      expect(
        ordensServico.any((OrdemServico os) => os.status == status),
        isTrue,
        reason: 'faltou OS no estagio ${status.rotulo}',
      );
    }

    for (final PontoVegetacao p in pontosVegetacao) {
      expect(p.historico.length, 5);
      for (int i = 1; i < p.historico.length; i++) {
        expect(
          p.historico[i].alturaCm,
          greaterThan(p.historico[i - 1].alturaCm),
        );
      }
      expect(p.alturaAtualCm, p.historico.last.alturaCm);
      expect(crescimentoMensalCm(p.historico), greaterThan(0));
    }
  });
}
