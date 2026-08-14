# vision — Bloco 2

Deteccao e medicao de vegetacao a partir das fotos da rodovia.

Contrato com o Bloco 3: este modulo **nao conhece o Supabase**. Recebe imagem e
devolve numero. Ver `docs/contrato-json-deteccoes.md`.

## Estado

Fase 1: segmentacao e medicao classicas. O Excess Green separa verde de
marrom por aritmetica de canais, e a haste de referencia converte pixels em
centimetros.

O modulo ja aceita foto real pelo servidor local: recebe upload ou captura da
webcam, gera imagem anotada, mascara e o JSON do contrato. Ainda nao ha modelo
`.keras` treinado; portanto a classificacao Seguro / Atencao / Critico fica
desativada ate o modelo ser exportado e validado.

## Modulos

| Arquivo | O que faz |
|---|---|
| `segmentacao.py` | `exg`, `mascara_vegetacao`, `maior_regiao` |
| `calibracao.py` | `pixels_por_cm` a partir da haste de altura conhecida |
| `classificacao.py` | `carregar_modelo`, `classificar` — Seguro / Atenção / Crítico |
| `teste_sintetico.py` | Cena gerada com resposta conhecida, prova a medicao |
| `teste_classificacao.py` | Prova o caminho do modelo; **pula** se o modelo faltar |
| `pipeline.py` | Foto real entra; contrato JSON e evidencias visuais saem |
| `app.py` | Servidor local com upload e webcam no Chrome |
| `teste_pipeline.py` | Confere contrato/evidencias e recusa foto sem haste |

## Rodando

```bash
cd vision
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
.venv/bin/python -m pip install -r requirements.txt       # Linux e macOS
```

Depois, execute os testes:

```bash
.venv/Scripts/python teste_sintetico.py
.venv/Scripts/python teste_classificacao.py
.venv/Scripts/python teste_pipeline.py
```

Para testar foto real no Chrome:

```bash
.venv/Scripts/python app.py
```

Abra `http://127.0.0.1:8766`. Use upload ou webcam, informe a altura da haste
(padrao: 100 cm) e processe. A foto precisa conter a haste inteira, vertical e
no mesmo plano da vegetacao. O resultado e salvo em `saidas/`, que nao entra no
Git.

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
