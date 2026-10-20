# Plano de Negócio — Motiva Field

## 1. Resumo executivo

O **Motiva Field** é uma solução B2B para apoiar a conservação de vegetação em rodovias. A plataforma transforma imagens e registros de campo em uma fila operacional priorizada, conecta alertas a ordens de serviço e registra evidências da execução.

A proposta não é substituir equipes de inspeção, conservação ou engenharia. O produto atua como **camada de inteligência, priorização e rastreabilidade**, reduzindo decisões baseadas apenas em rondas manuais e registros fragmentados.

O contexto da Motiva é compatível com essa abordagem. Em 2026, a companhia informa administrar 5.044 km de rodovias, 13 concessionárias e 3.356 câmeras de monitoramento. A empresa também divulga iniciativas de IA para monitoramento de áreas verdes e investimentos em equipamentos de roçada, o que reduz a barreira cultural para adoção de tecnologia no processo de conservação.

---

## 2. Proposta de valor

### Para a Motiva

**Transformar conservação de vegetação de uma rotina predominantemente reativa em uma operação orientada por prioridade, histórico e evidência.**

O sistema busca entregar:

- identificação de pontos que exigem atenção;
- histórico de evolução da vegetação;
- apoio à previsão de necessidade de roçada;
- abertura e acompanhamento de ordens;
- registro de foto antes/depois;
- comprovação de campo;
- visão centralizada para gestores;
- base para auditoria e melhoria de planejamento.

---

## 3. Público-alvo

### Cliente comprador

Concessionárias de rodovias, começando por operações da própria Motiva.

### Áreas que capturam valor

- Operações;
- Conservação;
- Engenharia;
- Segurança viária;
- Gestão de contratos e fornecedores;
- Inovação / transformação digital.

### Usuários

**Gestor de conservação**  
Precisa enxergar prioridades, risco, fila de trabalho e evidências.

**Supervisor operacional**  
Distribui ordens, acompanha execução e valida serviços.

**Inspetor / operador de campo**  
Recebe o destino, executa a tarefa e envia comprovação.

**Analista de engenharia/dados**  
Acompanha histórico e identifica padrões por trecho.

**Gestor executivo**  
Precisa de indicadores consolidados, rastreabilidade e justificativa das ações.

---

## 4. Modelo de receita

Modelo recomendado: **B2B SaaS com implantação assistida**.

### Etapa 1 — piloto

Projeto de 60 a 90 dias em um trecho controlado.

**Faixa proposta:** R$ 20 mil a R$ 35 mil pelo piloto.

Inclui:

- configuração do trecho;
- preparação da operação;
- parametrização de riscos;
- treinamento;
- acompanhamento;
- relatório de resultados e próximos passos.

### Etapa 2 — assinatura

Após validação do piloto:

**R$ 12 mil a R$ 25 mil/mês por concessão**, variando conforme:

- extensão monitorada;
- volume de imagens;
- integrações;
- armazenamento;
- SLA;
- suporte;
- quantidade de usuários.

Para uma contratação corporativa em múltiplas concessões, o modelo pode migrar para contrato anual com desconto por escala.

### Serviços opcionais

- integração com sistemas corporativos;
- implantação de novas concessões;
- calibração de novas câmeras;
- treinamento;
- dashboards personalizados;
- suporte com SLA ampliado.

---

## 5. Custos operacionais estimados

Os valores abaixo são **estimativas para um piloto**, e devem ser refinados após volume real de imagens e arquitetura de produção.

| Item | Estimativa mensal |
|---|---:|
| Backend / computação | R$ 500 – R$ 1.500 |
| Banco, storage e backups | R$ 300 – R$ 1.000 |
| Processamento/IA por imagem | R$ 500 – R$ 3.000 |
| Logs, monitoramento e serviços auxiliares | R$ 200 – R$ 800 |
| Suporte técnico alocado | R$ 3.500 – R$ 6.000 |
| **Total estimado** | **R$ 5.000 – R$ 12.300/mês** |

O custo de processamento depende fortemente de frequência de captura, resolução e política de retenção.

Um diferencial econômico importante é a possibilidade de **reaproveitar infraestrutura de captura já existente**. A Motiva informa possuir milhares de câmeras de monitoramento; a integração real dependeria de autorização, qualidade e posicionamento dessas fontes.

---

## 6. Viabilidade comercial

Com uma assinatura entre R$ 12 mil e R$ 25 mil/mês e custos operacionais diluídos entre clientes, a solução pode alcançar margem saudável depois da fase de validação.

No início, o principal custo não é nuvem: é engenharia, calibração, integração e suporte. Por isso o piloto deve ser pago e ter escopo controlado.

A escala melhora quando:

- o mesmo backend atende múltiplas concessões;
- modelos e regras são reutilizados;
- a operação passa a trabalhar com captura já existente;
- onboarding e parametrização se tornam padronizados.

---

## 7. Concorrência e alternativas

O concorrente não é apenas outro software.

As alternativas atuais incluem:

- inspeção visual manual;
- planilhas;
- sistemas genéricos de manutenção;
- vistorias por veículo;
- imagem de satélite;
- drones;
- equipamentos de roçada com inteligência própria;
- soluções internas de geoprocessamento.

A própria Motiva já divulgou IA/georreferenciamento para áreas verdes no Rodoanel. Isso valida o problema e também eleva o nível esperado da solução.

### Diferencial do Motiva Field

O diferencial não é “usar IA”.

É **fechar o ciclo operacional**:

```text
detectar → priorizar → gerar ordem → executar → comprovar → validar → criar histórico
```

A solução também combina painel gerencial e aplicativo de campo no mesmo fluxo.

---

## 8. Riscos

### Risco técnico — medição incorreta

Perspectiva, distância, terreno e qualidade da imagem podem distorcer medições.

**Mitigação:** calibração, referências físicas, intervalos de confiança, bloqueio de medições não confiáveis e validação humana.

### Risco operacional — captura inadequada

Fotos podem estar fora de padrão.

**Mitigação:** protocolo de captura, treinamento e feedback imediato no aplicativo.

### Risco de integração

Sistemas corporativos, redes internas e APIs podem impor restrições.

**Mitigação:** arquitetura desacoplada por API e piloto isolado antes da integração completa.

### Risco de adoção

Equipes podem enxergar a ferramenta como fiscalização individual.

**Mitigação:** apresentar o produto como ferramenta de priorização e prova do serviço, não de vigilância de trabalhadores.

### Risco financeiro

Volume de imagens pode aumentar custo de processamento e armazenamento.

**Mitigação:** compressão, políticas de retenção, processamento por evento e limites de uso por plano.

### Risco de segurança e LGPD

Imagens podem conter pessoas, veículos e placas.

**Mitigação:** minimização, retenção controlada, acesso por perfil, criptografia e política de tratamento antes da produção.

---

## 9. Impacto esperado

### Para a Motiva

- melhor priorização de equipes;
- menos rondas sem direcionamento;
- redução de retrabalho;
- histórico operacional estruturado;
- evidências de execução;
- melhor planejamento por trecho;
- suporte a auditoria de fornecedores;
- capacidade de comparar concessões.

### Para a rodovia

- atuação mais previsível;
- redução de vegetação interferindo em visibilidade e sinalização;
- apoio a ações preventivas;
- melhor uso das janelas de manutenção.

### Para equipes

- ordem clara;
- localização objetiva;
- menos comunicação informal;
- evidência organizada em um único fluxo.

---

## 10. KPIs do piloto

Os indicadores abaixo são **metas de validação**, não resultados já comprovados.

| KPI | Meta de piloto |
|---|---:|
| Ordens concluídas com evidência completa | ≥ 90% |
| Disponibilidade do sistema durante o piloto | ≥ 99% em horário operacional |
| Pontos críticos com prioridade definida | 100% |
| Tempo entre alerta e geração de ordem | redução ≥ 30% |
| Redução de inspeções manuais sem direcionamento | ≥ 20% |
| Usuários treinados que concluem fluxo sem suporte | ≥ 80% |
| Falsos alertas | acompanhar e reduzir a cada ciclo |

---

## 11. Estratégia de implantação

### Fase 1 — piloto

- escolher um trecho;
- levantar regras de conservação;
- cadastrar pontos;
- rodar com uma equipe reduzida;
- comparar sistema × avaliação humana.

### Fase 2 — validação

- medir precisão;
- ajustar classificação;
- avaliar aderência do app;
- medir tempo operacional;
- documentar economia e ganhos.

### Fase 3 — produção controlada

- autenticação corporativa;
- integração com sistemas;
- observabilidade;
- políticas de dados;
- assinatura corporativa do app;
- SLA.

### Fase 4 — escala

- ampliar para novas rodovias;
- reaproveitar infraestrutura de captura;
- comparar concessionárias;
- criar benchmarks e planejamento preditivo.

---

## 12. Conclusão

O Motiva Field possui uma tese comercial clara: **o valor não está na imagem analisada isoladamente, mas na transformação da imagem em decisão operacional comprovável**.

O produto se encaixa em uma organização que já opera em grande escala, já investe em tecnologia para rodovias e mantém atividades recorrentes de conservação. A recomendação comercial é começar com piloto curto, métricas objetivas e escopo limitado, provando valor antes de expandir.
