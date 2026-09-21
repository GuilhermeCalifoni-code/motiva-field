# Calibração do POCO X7 Pro

Esta etapa libera a geometria sem referência visível na foto. Não altera resultados para fazê-los coincidir com ground truth.

## 1. Preparar o tabuleiro

1. Imprima `tabuleiro-9x6-20mm-a4.pdf` em A4, **escala 100%** e sem “ajustar à página”.
2. Confira com régua que cada quadrado mede 20 mm.
3. Cole a folha em uma superfície rígida e plana.

O padrão possui 10 × 7 quadrados, equivalentes a **9 × 6 cantos internos**.

## 2. Capturar

Use sempre:

- POCO X7 Pro;
- câmera traseira principal;
- zoom 1×;
- mesma resolução/orientação que será usada no Motiva Field;
- sem modo retrato, grande-angular ou zoom digital.

Tire de 15 a 20 fotos nítidas:

- 3 de frente;
- 3 inclinadas para a esquerda;
- 3 inclinadas para a direita;
- 3 inclinadas para cima/baixo;
- 3 próximas e 3 afastadas;
- o tabuleiro deve aparecer inteiro e ocupar partes diferentes do quadro.

Coloque os arquivos em `fotos-tabuleiro/`.

## 3. Calibrar

Na raiz do projeto:

```bash
vision/.venv/Scripts/python.exe vision/calibrar_camera.py --pasta vision/calibracao-poco-x7-pro/fotos-tabuleiro --colunas 9 --linhas 6 --quadrado-mm 20
```

A rotina exige ao menos 12 imagens aproveitáveis e grava os intrínsecos no perfil da câmera.

## 4. Critérios de liberação

A câmera calibrada sozinha não basta. Uma medição sem referência só é liberada quando também houver:

- resolução idêntica à calibração;
- orientação disponível/validada;
- plano local do solo confirmado;
- auditoria visual aprovada;
- solução Monte Carlo estável;
- intervalo relativo dentro do limite.

## 5. Validar sem contaminar a inferência

Execute:

```bash
vision/.venv/Scripts/python.exe vision/validar_ground_truth.py
```

O script faz a inferência primeiro e só depois lê `ground_truth.json` para calcular erro. Não use os valores reais para ajustar pitch, foco ou intrínsecos.
