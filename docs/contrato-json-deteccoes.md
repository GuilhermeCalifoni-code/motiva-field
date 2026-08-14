# Contrato — saída da visão computacional

> Contrato entre Bloco 2 (visão) e Bloco 3 (banco e pipeline).
> Enquanto este formato não mudar, os dois blocos trabalham em paralelo.
> Contexto: [[MOTIVA-FIELD-HUB]] | Decisão: [[ADR-0002-visao-computacional]]

---

## Princípio

O `vision/` recebe imagem e devolve JSON. Ele **não conhece** o Supabase, o
painel nem o mobile. Quem lê o JSON, casa com ponto e grava no banco é o
Bloco 3.

Isso significa que o Bloco 2 pode ser testado sozinho, com imagem e um
arquivo de saída, sem banco nenhum rodando.

## Formato

Uma foto produz um objeto. Um lote produz um array desses objetos.

```json
{
  "arquivo": "IMG_0042.jpg",
  "capturado_em": "2026-08-15T09:14:22-03:00",
  "coordenadas": { "lat": -23.5891, "lon": -47.6412 },
  "modelo_versao": "mobilenet_motiva_v1+exg",
  "calibracao": {
    "referencia": "haste_1m",
    "pixels_por_cm": 3.42
  },
  "deteccoes": [
    {
      "classe": "vegetacao_alta",
      "confianca": 0.87,
      "metrica": 62.4,
      "unidade": "cm",
      "bbox": [412, 380, 690, 1002],
      "cobertura_pct": 18.3
    }
  ]
}
```

## Campos

| Campo | Tipo | Regra |
|---|---|---|
| `arquivo` | string | Nome do arquivo original, sem caminho |
| `capturado_em` | string | ISO 8601 com fuso. Do EXIF se houver; senão, da modificação do arquivo |
| `coordenadas` | objeto ou null | Do EXIF quando a foto tiver GPS. `null` é válido |
| `modelo_versao` | string | Identifica o que produziu o resultado. Muda quando o modelo muda |
| `calibracao.referencia` | string | O que serviu de régua. `haste_1m` no piloto |
| `calibracao.pixels_por_cm` | número | Razão derivada da referência nesta imagem |
| `deteccoes` | array | Pode ser vazio — imagem sem vegetação relevante é resultado válido |

Dentro de cada detecção:

| Campo | Tipo | Regra |
|---|---|---|
| `classe` | string | `vegetacao_alta`, `invade_pista` ou `cobre_placa` |
| `confianca` | número | 0 a 1 |
| `metrica` | número | O valor medido. O significado depende da classe |
| `unidade` | string | `cm` para altura, `m` para invasão, `pct` para placa encoberta |
| `bbox` | array de 4 inteiros | `[x1, y1, x2, y2]` em pixels da imagem original |
| `cobertura_pct` | número | Percentual do quadro ocupado pela vegetação detectada |

## Por que `metrica` + `unidade` em vez de `altura_cm`

As três classes medem coisas diferentes: altura em centímetros, invasão de
pista em metros, placa encoberta em percentual. Um par genérico evita três
colunas onde só uma é preenchida por vez. É o mesmo desenho já adotado na
tabela `deteccoes` do schema.

## Regras que não podem ser quebradas

- Se a referência de calibração não for encontrada, o pipeline **falha com
  erro claro**. Nunca chuta um `pixels_por_cm`.
- `deteccoes: []` é sucesso, não erro.
- O JSON nunca contém `ponto_id`. A detecção nasce órfã; casar com ponto é
  trabalho do Bloco 3, por proximidade.
- Nenhum caminho absoluto de máquina dentro do JSON.

## Como testar sem o outro bloco

Bloco 2: roda o pipeline numa pasta de fotos e confere o JSON gerado.

Bloco 3: escreve um JSON à mão seguindo este formato e constrói o consumo em
cima dele. Quando o Bloco 2 entregar o real, encaixa.

---
Voltar: [[MOTIVA-FIELD-HUB]] | [[🧠 Cerebro 2]]
