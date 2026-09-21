# Visão computacional — Motiva Field

O módulo separa três responsabilidades:

1. **Gemini:** percepção auditável da cena — alvo, ROI, base, topo, solo, referências e limitações.
2. **OpenCV/geometria:** segmentação, escala, raios 3D, plano local e propagação de incerteza.
3. **Validação:** decide se uma altura pode ser liberada. Evidência insuficiente sempre produz `altura_cm: null`.

## Estado atual

- Triagem semântica: operacional.
- Medição com escala explícita: experimental, exige consenso entre detectores.
- Medição monocular sem referência: implementada, mas bloqueada até calibrar o POCO X7 Pro e fornecer orientação/plano confiáveis.
- Ground truth: restaurado em `fotos/validacao-poco-x7-pro/ground_truth.json` e nunca usado como entrada da inferência.

## Pipeline V3

```text
foto
  → auditoria Gemini versionada
  → ROI explícita
  → segmentação determinística dentro da ROI
  → 20 faixas de amostragem
  → remoção de outliers por IQR
  → envelope p85
  → escala explícita OU geometria calibrada
  → Monte Carlo/consenso
  → altura + intervalo OU null + motivos
```

### Altura operacional

Para faixa contínua/touceira, “altura” significa **p85 do envelope local após IQR**. Isso evita que uma folha isolada represente toda a vegetação. O contrato deve registrar as amostras usadas.

### Liberação de centímetros

Uma medida só é válida quando:

- alvo e ROI estão definidos;
- base e topo são compatíveis;
- há ao menos 8 amostras para vegetação contínua;
- confiança global ≥ 0,80;
- escala/referência e profundidade são utilizáveis;
- Gemini e OpenCV concordam em até 10% na escala e 15% na altura; ou
- câmera, orientação e plano local estão calibrados e o Monte Carlo é estável.

Pneu, meio-fio, canaleta e dimensões “típicas” não liberam centímetros sozinhos.

## Arquivos principais

| Arquivo | Função |
|---|---|
| `pipeline.py` | Orquestra foto, auditoria, segmentação e medição |
| `auditoria_atencao.py` | Valida ROI/base/topo antes da geometria |
| `segmentacao.py` | ExG, componentes e envelope robusto p85 |
| `geometria.py` | Pixel → raio → plano → altura |
| `validacao_geometrica.py` | Guardas e confiança composta |
| `calibrar_camera.py` | Intrínsecos e distorção por tabuleiro |
| `validar_ground_truth.py` | Inferência cega e cálculo posterior de erro |
| `calibracao.py` / `graduacao.py` | Escala explícita para conferência |

## Calibrar o POCO X7 Pro

O kit está em `calibracao-poco-x7-pro/`.

1. Imprima `tabuleiro-9x6-20mm-a4.pdf` em 100%.
2. Capture 15–20 fotos conforme `calibracao-poco-x7-pro/README.md`.
3. Rode:

```bash
vision/.venv/Scripts/python.exe vision/calibrar_camera.py \
  --pasta vision/calibracao-poco-x7-pro/fotos-tabuleiro \
  --colunas 9 --linhas 6 --quadrado-mm 20
```

## Validar

```bash
vision/.venv/Scripts/python.exe vision/teste_sintetico.py
vision/.venv/Scripts/python.exe vision/teste_pipeline.py
vision/.venv/Scripts/python.exe vision/validar_ground_truth.py
```

O último comando grava `fotos/validacao-poco-x7-pro/resultado-validacao.json` com altura real, estimada, erro, confiança e motivo de bloqueio. O ground truth é aberto apenas depois das inferências.

## Regra invariável

Rastreabilidade > consistência geométrica > precisão > estimativa.

Se a origem métrica, o plano, a orientação ou a correspondência base–topo não forem sustentados, a saída correta é `altura_cm: null`.
