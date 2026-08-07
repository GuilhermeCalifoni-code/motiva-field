import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:motiva_field/main.dart';
import 'package:motiva_field/mock_data.dart';

/// Botao de concluir da tela de comprovacao.
ElevatedButton _botaoConcluir(WidgetTester tester) {
  return tester.widget<ElevatedButton>(
    find.ancestor(
      of: find.text('Servico concluido'),
      matching: find.byType(ElevatedButton),
    ),
  );
}

void main() {
  testWidgets('login leva para a ordem ativa do operador', (WidgetTester tester) async {
    await tester.pumpWidget(const MotivaFieldApp());

    expect(find.text('MOTIVA FIELD'), findsOneWidget);

    await tester.tap(find.text('Entrar'));
    await tester.pumpAndSettle();

    final PontoVegetacao ponto = pontoPorId(ordemAtivaDe(operadorAtual).pontoId);
    expect(find.text('Ordem ativa'), findsOneWidget);
    expect(find.text('${ponto.rodovia} · km ${ponto.kmFormatado}'), findsOneWidget);
  });

  testWidgets('fluxo 1-2-3-4 e a trava da comprovacao', (WidgetTester tester) async {
    // Tela alta o bastante para a comprovacao caber sem rolagem.
    tester.view.physicalSize = const Size(1200, 3000);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(const MotivaFieldApp());

    // 1 -> 2
    await tester.tap(find.text('Entrar'));
    await tester.pumpAndSettle();
    expect(find.text('Ordem ativa'), findsOneWidget);

    // 2 -> 3
    await tester.tap(find.text('Iniciar rota'));
    await tester.pumpAndSettle();
    expect(find.text('Navegacao'), findsOneWidget);
    expect(find.text('DESTINO'), findsOneWidget);

    // 3 -> 4
    await tester.tap(find.text('Cheguei ao local'));
    await tester.pumpAndSettle();
    expect(find.text('Comprovacao de execucao'), findsOneWidget);

    // Sem evidencia nenhuma, concluir esta travado.
    expect(find.text('Evidencias: 0 de 3'), findsOneWidget);
    expect(_botaoConcluir(tester).onPressed, isNull);

    await tester.tap(find.text('ANTES'));
    await tester.pumpAndSettle();
    expect(find.text('Evidencias: 1 de 3'), findsOneWidget);
    expect(_botaoConcluir(tester).onPressed, isNull);

    await tester.tap(find.text('DEPOIS'));
    await tester.pumpAndSettle();
    expect(find.text('Evidencias: 2 de 3'), findsOneWidget);
    // Duas fotos ainda nao bastam: falta a coordenada.
    expect(_botaoConcluir(tester).onPressed, isNull);

    await tester.tap(find.text('Capturar coordenada'));
    await tester.pumpAndSettle();
    expect(find.text('Comprovacao completa. Pode concluir.'), findsOneWidget);
    expect(_botaoConcluir(tester).onPressed, isNotNull);

    // 4 -> volta para a ordem, agora comprovada.
    await tester.tap(find.text('Servico concluido'));
    await tester.pumpAndSettle();
    expect(find.text('Ordem ativa'), findsOneWidget);
    expect(
      find.text('Servico comprovado e enviado. Nenhuma ordem em aberto.'),
      findsOneWidget,
    );
  });

  test('mock espelha o do painel web', () {
    expect(pontosVegetacao.length, 8);
    expect(operadores.length, 4);
    expect(ordensServico.length, 6);

    // Os quatro estagios de OS existem no mock.
    for (final StatusOS status in fluxoStatus) {
      expect(
        ordensServico.any((OrdemServico os) => os.status == status),
        isTrue,
        reason: 'faltou OS no estagio ${status.rotulo}',
      );
    }

    // Historico de 5 passagens com altura crescente, como no web.
    for (final PontoVegetacao p in pontosVegetacao) {
      expect(p.historico.length, 5);
      for (int i = 1; i < p.historico.length; i++) {
        expect(p.historico[i].alturaCm, greaterThan(p.historico[i - 1].alturaCm));
      }
      expect(p.alturaAtualCm, p.historico.last.alturaCm);
      expect(crescimentoMensalCm(p.historico), greaterThan(0));
    }
  });
}
