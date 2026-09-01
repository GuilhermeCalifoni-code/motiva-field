# S2-CP01 — Tema 2: Sensoriamento da vegetação e qualidade da medição

Entrega do CP1 de Sprint 2. Dois arquivos vão para o professor:

| Arquivo | O que é |
|---|---|
| `S2-CP1-Motiva-Tema2-Sensoriamento.pdf` | Documentação técnica (11 páginas, capa + índice + 7 seções) |
| `S2-CP1-Motiva-Tema2-Aula.pptx` | Aula de 10 min (11 slides, com notas de orador cronometradas) |

Os dois são **gerados por script**. Edite o script, regere o arquivo — não
edite o PDF nem o PPTX à mão, senão a próxima geração apaga a alteração.

## ANTES DE ENTREGAR: preencher identificação

A capa e o slide 2 estão com marcadores. Substitua nos dois scripts:

- `gerar_documentacao.py` → constantes `TURMA` e `INTEGRANTES`
- `gerar_apresentacao.js` → constantes `TURMA` e `INTEGRANTES`

No `.js`, cada integrante tem também um campo `papel`, que é o que o enunciado
exige (“informar qual sua participação no projeto”). Ajuste para a divisão real.

## Regerando

```bash
cd docs/S2-CP1

# PDF (usa o venv da visão, que já tem reportlab)
../../vision/.venv/Scripts/python gerar_documentacao.py

# Slides (precisa de pptxgenjs: npm install pptxgenjs)
node gerar_apresentacao.js
```

O PDF é montado em duas passagens: a primeira descobre em que página cada seção
caiu, a segunda escreve o índice com os números certos.

## Como o conteúdo responde ao enunciado

| Exigência do CP | Onde está |
|---|---|
| Capa, índice, conteúdo | PDF, páginas 1–2 |
| Introdução ligada ao Motiva | PDF §1 |
| Fundamentação técnica | PDF §2 (as 4 tecnologias + cálculo de footprint) |
| Comparação de alternativas | PDF §3 (Tabela 2 + critérios de escolha) |
| Aplicação ao projeto | PDF §4 (limiares reais, os dois erros de campo) |
| Proposta com diagrama/cálculo | PDF §5 (arquitetura + fluxo em 6 etapas) |
| Conclusão | PDF §6 |
| Referências | PDF §7 (datasheets + artigo revisado por pares) |
| Aula começa pelo problema | Slide 3 (caso real dos 38,5 cm) |
| Exemplo aplicado à Motiva | Slides 3, 6 e 7 |
| Cálculo / comparação | Slides 5 (footprint) e 6 (gráfico de RMSE) |
| Todos se apresentam | Slide 2 |

## Fontes usadas

Datasheets de fabricante (ST, Benewake, Sharp, Handson) e um artigo revisado por
pares — Zheng *et al.* (2024), *Frontiers in Plant Science*,
DOI 10.3389/fpls.2024.1354359 — que traz o RMSE de medição ultrassônica de
dossel que sustenta a recomendação.

## Limitação declarada no próprio material

O grupo **não ensaiou LiDAR nem ultrassom**. As recomendações vêm de datasheets,
literatura e dos ensaios próprios com medição por imagem. Isso está dito no PDF
(§6) e no último slide, de propósito: antecipa a pergunta óbvia e é mais
defensável que omitir.
