# vision — Bloco 2

Deteccao e medicao de vegetacao a partir das fotos da rodovia.

Contrato com o Bloco 3: este modulo **nao conhece o Supabase**. Recebe imagem e
devolve numero. Ver `docs/contrato-json-deteccoes.md`.

## Estado

Fase 1: segmentacao e medicao classicas, sem modelo treinado e sem depender de
foto real. O Excess Green separa verde de marrom por aritmetica de canais, e a
haste de referencia converte pixels em centimetros.

Isso permite provar a matematica antes da captura em campo. Quando o modelo
entrar, ele substitui `mascara_vegetacao` sem mexer no resto.

## Modulos

| Arquivo | O que faz |
|---|---|
| `segmentacao.py` | `exg`, `mascara_vegetacao`, `maior_regiao` |
| `calibracao.py` | `pixels_por_cm` a partir da haste de altura conhecida |
| `classificacao.py` | `carregar_modelo`, `classificar` — Seguro / Atenção / Crítico |
| `teste_sintetico.py` | Cena gerada com resposta conhecida, prova a medicao |
| `teste_classificacao.py` | Prova o caminho do modelo; **pula** se o modelo faltar |

## Rodando

```bash
cd vision
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
.venv/bin/python -m pip install -r requirements.txt       # Linux e macOS
```

Depois:

```bash
.venv/Scripts/python teste_sintetico.py
.venv/Scripts/python teste_classificacao.py
```

Sai com codigo 0 se tudo passar. Nao abre janela — roda headless.

## O modelo

`teste_classificacao.py` **pula** a parte de classificacao enquanto
`modelos/mobilenet_motiva.keras` nao existir, em vez de falhar. Assim ele vale
no CI hoje e passa a cobrir o modelo sozinho quando o arquivo aparecer.

O arquivo nao e versionado. Ver `modelos/README.md` para exportar do Colab e
conferir a ordem das classes.

## A regra que nao se quebra

Se a haste de referencia nao aparecer na foto, `pixels_por_cm` levanta
`ReferenciaNaoEncontrada`. **Nunca** devolve um valor estimado: um
`pixels_por_cm` chutado contamina todo o historico de altura daquele ponto, e o
erro so apareceria meses depois, como uma projecao de rocada errada.

O teste sintetico cobre esse caso explicitamente.
