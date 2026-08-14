# Protocolo de captura — SP-270

> Para quem for a campo. Leia antes de sair.
> A captura não se repete antes da entrega — o que voltar errado, volta errado.
> Contexto: [[MOTIVA-FIELD-HUB]] | Decisão: [[ADR-0002-visao-computacional]]

---

## Por que isso importa

O sistema mede a altura da vegetação em centímetros. Para o número ser real e
não estimado, cada foto precisa de um objeto de tamanho conhecido dentro do
quadro. Sem isso, o software só consegue dizer "tem mato", não "tem 62 cm de
mato" — e é o número que vende.

## O que levar

- Haste de 1 metro (cabo de vassoura serve), pintada com marcas a cada 10 cm
  em cor que contraste com verde e marrom — branco ou laranja
- Celular com GPS ligado e **geolocalização nas fotos ativada**
- Caderno ou bloco de notas do celular para registrar o km de cada ponto
- Carro

## Antes de sair

- [ ] Confirmar que a câmera está salvando GPS nas fotos (tirar uma foto de
      teste e checar as propriedades)
- [ ] Bateria cheia e espaço livre no celular
- [ ] Combinar quem segura a haste e quem fotografa

## Como fotografar cada ponto

1. Parar em local seguro, fora da faixa de rolamento, com pisca ligado
2. Encostar a haste **verticalmente no chão**, ao lado da vegetação, na mesma
   distância da câmera que o mato
3. Enquadrar de forma que a haste inteira e a vegetação apareçam no quadro
4. Fotografar **de frente**, com a câmera aproximadamente na altura do peito.
   Evitar ângulo de cima ou muito de baixo
5. Tirar **três fotos** do mesmo ponto — se uma sair tremida ou com sombra
   ruim, ainda sobram duas
6. Anotar o km e o sentido (Capital ou Interior)

## Quantos pontos

Mínimo **8 pontos**, para bater com os 8 do painel. Se der tempo, 12.

Variar de propósito: alguns com mato baixo, alguns com mato alto, alguns perto
de placa. Diversidade importa mais que quantidade — oito pontos diferentes
valem mais que trinta iguais.

## Segurança acima de tudo

Rodovia é lugar perigoso. Nenhuma foto vale um susto:

- Nunca parar em curva, em subida sem visibilidade ou no acostamento estreito
- Colete refletivo se houver
- Ninguém pisa na faixa de rolamento
- Se o ponto parecer arriscado, **pula o ponto**. Existe outro mato adiante

## Ao voltar

- [ ] Copiar todas as fotos para `Motiva-Field/vision/fotos/`
- [ ] Não renomear os arquivos — o nome original ajuda a rastrear
- [ ] Criar um arquivo `fotos/registro.txt` com uma linha por foto:
      `nome_do_arquivo | km | sentido | observação`
- [ ] Avisar o grupo que as fotos estão no lugar

## Erros que estragam a captura

| Erro | Consequência |
|---|---|
| Haste fora do quadro | A foto não serve para medir — só para ilustrar |
| Haste inclinada | A altura calculada sai errada |
| Haste longe do mato | A perspectiva distorce a razão pixel/cm |
| GPS desligado | Perde a coordenada, o ponto vira genérico |
| Não anotar o km | Não dá para casar a foto com o ponto no painel |

---
Voltar: [[MOTIVA-FIELD-HUB]] | [[🧠 Cerebro 2]]
