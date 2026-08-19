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
| `calibracao.py` | `medir_escala` (tres vias) e a calibracao persistida |
| `graduacao.py` | Le as marcas da trena e deriva a escala sem numero digitado |
| `classificacao.py` | `carregar_modelo`, `classificar` — Seguro / Atenção / Crítico |
| `conferir.py` | Compara as duas vias de escala na mesma cena |
| `teste_sintetico.py` | Cena gerada com resposta conhecida, prova a medicao |
| `teste_classificacao.py` | Prova o caminho do modelo; **pula** se o modelo faltar |
| `pipeline.py` | Foto real entra; contrato JSON e evidencias visuais saem |
| `app.py` | Servidor local com upload e webcam no Chrome |
| `teste_pipeline.py` | Contrato, recusa sem escala e as duas vias batendo |

## As duas vias de escala

Existem dois jeitos de converter pixel em centimetro, e o pipeline aceita os
dois — nesta precedencia:

1. **Calibracao salva** (`calibracao=`): mede **sem regua no quadro**. E o modo
   de producao, com a camera fixa no veiculo. Calibra-se uma vez.
2. **Regua no quadro** (`referencia_cm=`): detecta a regua na propria foto. E o
   modo de conferencia, e o unico que nao depende da geometria ter ficado igual.

Sem nenhuma das duas, o pipeline **levanta excecao**. Nao existe valor padrao.

Gerar a calibracao a partir de uma foto com trena:

```bash
python -m vision.calibracao --foto foto_trena.jpg --referencia-cm 50 \
    --altura-camera-cm 140 --distancia-cm 200
```

Provar que da para medir sem regua, com duas fotos do mesmo alvo na mesma pose:

```bash
python -m vision.conferir --com-trena a.jpg --sem-trena b.jpg \
    --calibracao calibracao.json --referencia-cm 50
```

Sai com 0 se as duas vias divergirem menos de 10%, 1 se divergirem mais.

## A escala vem da propria trena

O ponto mais fragil da medicao era humano: alguem digitava quantos centimetros
da fita estavam esticados. Na primeira medicao real foram informados ~50 cm
onde a fita mostrava ~13,5 cm, e a vegetacao saiu 38,5 cm em vez de ~10 cm. Um
comprimento errado escala TUDO na mesma proporcao, e o resultado continua
parecendo plausivel — nada no sistema percebia.

A trena ja carrega a resposta impressa. `graduacao.py` le as marcas:

1. Endireita a fita (`cv2.minAreaRect`), porque foto de campo nao sai a prumo.
2. Tira o perfil de intensidade por linha, numa faixa central da largura.
3. Remove o gradiente de iluminacao com um polinomio de grau 3.
4. Acha a periodicidade dominante por autocorrelacao **sem vies**.
5. Descobre se aquele periodo vale 1 mm, 5 mm ou 1 cm, testando harmonicos.

Por isso `medir_escala()` tem tres vias, nesta ordem:

1. **Graduacao** — preferida, nao precisa de numero nenhum.
2. **Comprimento informado** — usado so quando a graduacao falha.
3. Falha com excecao clara.

Quando as duas primeiras estao disponiveis, as duas sao calculadas e
COMPARADAS. Divergencia acima de 15% entra como aviso dizendo o que cada via
deu — e quase sempre significa que o numero foi digitado errado.

### Limites da leitura de graduacao

**Resolucao.** Na foto real a escala fica em torno de 29 px/cm, entao 1 mm
ocupa ~2,9 px — o limite do que da para resolver. O metodo NAO depende de
enxergar milimetro: ele acha a periodicidade dominante, seja de 1 mm, 5 mm ou
1 cm, e so entao descobre o que ela significa. Em foto de baixa resolucao o
normal e o fundamental ser 5 mm ou 1 cm, e a escala continua certa.

**Fita sem hierarquia.** A desambiguacao se apoia nas marcas de 5 mm e 1 cm
serem mais longas e escuras que as de 1 mm. Numa fita onde todas as marcas sao
iguais, o passo detectado e assumido como 1 cm — nao ha como distinguir.

**Sem contraste, sem leitura.** Se o perfil nao tiver amplitude minima
(6 niveis de cinza), a funcao devolve None em vez de arriscar. Barra lisa cai
aqui: sem essa guarda, o ruido de uma barra sem marcas chega a produzir
periodicidade aparente.

Devolver None e resultado legitimo — cair na via manual e melhor do que
devolver numero errado.

## Avisos no contrato

O JSON de saida traz um bloco `avisos`, lista de strings vazia quando esta tudo
bem. Eles **nao impedem** o resultado; acompanham, porque o erro de escala
produz um numero que parece normal. Sao gerados quando:

- a altura medida passa de 200 cm;
- a altura medida e mais de 3x o comprimento visivel da referencia;
- a confianca da leitura de graduacao fica abaixo de 0,5;
- as duas vias de escala divergem mais de 15%.

## Limites da calibracao

**A calibracao vale so para a geometria em que foi feita.** Ela guarda uma razao
pixel/cm que so e verdadeira naquela altura de camera e naquela distancia do
alvo. Fotografe de outra distancia e o numero sai errado — e **nada no
resultado denuncia isso**. A foto continua bonita, a mascara continua certa, o
JSON continua valido. So o centimetro esta mentindo.

Por isso:

- O dicionario de calibracao carrega a `geometria` (altura da camera, distancia
  do alvo), e ela **reaparece no JSON de saida**. Quem auditar o resultado
  depois consegue conferir em que condicoes aquele centimetro foi obtido.
- `carregar_calibracao()` **avisa** (`CalibracaoAntiga`) quando o arquivo tem
  mais de 7 dias. Nao bloqueia: uma calibracao velha ainda pode estar correta.
  Mas a camera sai do lugar — batida de porta, manutencao, troca de veiculo — e
  o aviso e a unica coisa que lembra disso.
- `calibracao.json` **nao e versionado**. Ele e especifico de cada maquina,
  camera e montagem. Versionar faria uma maquina medir com a escala de outra.

Refaca a calibracao quando: mudar a altura ou o angulo da camera, trocar de
veiculo, trocar de lente, ou depois de qualquer manutencao que mexa no suporte.
Na duvida, rode `python -m vision.conferir` — ele responde com numero.

**Limitacao conhecida da deteccao:** a referencia precisa aparecer **vertical**
no quadro. O detector procura o objeto alto e estreito fora da vegetacao; uma
trena deitada no chao nao e reconhecida.

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

Abra `http://127.0.0.1:8766`. A aba **Medir** deixa escolher a fonte da escala:
regua no quadro ou calibracao salva. A aba **Calibrar** gera a calibracao a
partir de uma foto com trena. O resultado sempre mostra por qual via a escala
veio. As saidas vao para `saidas/`, que nao entra no Git.

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
