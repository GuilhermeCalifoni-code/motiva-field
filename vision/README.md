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
| `teste_sintetico.py` | Cena gerada com resposta conhecida, prova a medicao |

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
```

Sai com codigo 0 se tudo passar. Nao abre janela — roda headless.

## A regra que nao se quebra

Se a haste de referencia nao aparecer na foto, `pixels_por_cm` levanta
`ReferenciaNaoEncontrada`. **Nunca** devolve um valor estimado: um
`pixels_por_cm` chutado contamina todo o historico de altura daquele ponto, e o
erro so apareceria meses depois, como uma projecao de rocada errada.

O teste sintetico cobre esse caso explicitamente.
