/// Dado falso e unico desta frente, espelhando web/src/mockData.ts.
///
/// Nenhum widget inventa dado inline. Quando o backend Python existir, este
/// arquivo vira chamadas de API e mais nada muda. Se uma tela precisar de um
/// campo que nao existe aqui, o campo entra neste arquivo — nunca no widget.
library;

enum Sentido { capital, interior }

enum Margem { direita, esquerda }

enum NivelRisco { tranquilo, atencao, critico }

enum StatusOS { pendente, emDeslocamento, noLocal, concluida }

enum Prioridade { baixa, media, alta }

extension SentidoRotulo on Sentido {
  String get rotulo => this == Sentido.capital ? 'Capital' : 'Interior';
}

extension MargemRotulo on Margem {
  String get rotulo => this == Margem.direita ? 'direita' : 'esquerda';
}

extension NivelRiscoRotulo on NivelRisco {
  String get rotulo {
    switch (this) {
      case NivelRisco.tranquilo:
        return 'Tranquilo';
      case NivelRisco.atencao:
        return 'Atencao';
      case NivelRisco.critico:
        return 'Critico';
    }
  }
}

extension StatusOSRotulo on StatusOS {
  String get rotulo {
    switch (this) {
      case StatusOS.pendente:
        return 'Pendente';
      case StatusOS.emDeslocamento:
        return 'Em deslocamento';
      case StatusOS.noLocal:
        return 'No local';
      case StatusOS.concluida:
        return 'Concluida';
    }
  }
}

extension PrioridadeRotulo on Prioridade {
  String get rotulo {
    switch (this) {
      case Prioridade.baixa:
        return 'Baixa';
      case Prioridade.media:
        return 'Media';
      case Prioridade.alta:
        return 'Alta';
    }
  }
}

/// Altura, em cm, a partir da qual o ponto entra em cada nivel.
/// Mesmos limites do painel web.
const Map<NivelRisco, int> limiteAlturaCm = <NivelRisco, int>{
  NivelRisco.tranquilo: 0,
  NivelRisco.atencao: 25,
  NivelRisco.critico: 45,
};

const int alturaCriticaCm = 45;

/// Ordem das colunas do fluxo de OS. Cada transicao guarda horario.
const List<StatusOS> fluxoStatus = <StatusOS>[
  StatusOS.pendente,
  StatusOS.emDeslocamento,
  StatusOS.noLocal,
  StatusOS.concluida,
];

class Passagem {
  const Passagem({required this.data, required this.alturaCm});

  final DateTime data;
  final int alturaCm;
}

class PontoVegetacao {
  const PontoVegetacao({
    required this.id,
    required this.rodovia,
    required this.km,
    required this.sentido,
    required this.margem,
    required this.latitude,
    required this.longitude,
    required this.alturaAtualCm,
    required this.nivelRisco,
    required this.invadePista,
    required this.cobrePlaca,
    required this.historico,
  });

  final String id;
  final String rodovia;
  final double km;
  final Sentido sentido;
  final Margem margem;
  final double latitude;
  final double longitude;
  final int alturaAtualCm;
  final NivelRisco nivelRisco;
  final bool invadePista;
  final bool cobrePlaca;
  final List<Passagem> historico;

  /// km formatado no padrao brasileiro: "99,30".
  String get kmFormatado => km.toStringAsFixed(2).replaceAll('.', ',');
}

class Operador {
  const Operador({required this.id, required this.nome, required this.matricula});

  final String id;
  final String nome;
  final String matricula;

  /// Primeiro nome, para a saudacao.
  String get primeiroNome => nome.split(' ').first;
}

class TransicaoStatus {
  const TransicaoStatus({required this.status, required this.em});

  final StatusOS status;
  final DateTime em;
}

class OrdemServico {
  const OrdemServico({
    required this.id,
    required this.pontoId,
    required this.operadorId,
    required this.prioridade,
    required this.status,
    required this.criadaEm,
    required this.previsaoConclusao,
    required this.transicoes,
  });

  final String id;
  final String pontoId;
  final String operadorId;
  final Prioridade prioridade;
  final StatusOS status;
  final DateTime criadaEm;
  final DateTime previsaoConclusao;
  final List<TransicaoStatus> transicoes;

  bool get estaAberta => status != StatusOS.concluida;

  /// Copia com novo status e a transicao registrada — o estado em memoria das
  /// telas usa isto para avancar a OS sem perder o historico.
  OrdemServico avancarPara(StatusOS novo, DateTime quando) {
    return OrdemServico(
      id: id,
      pontoId: pontoId,
      operadorId: operadorId,
      prioridade: prioridade,
      status: novo,
      criadaEm: criadaEm,
      previsaoConclusao: previsaoConclusao,
      transicoes: <TransicaoStatus>[
        ...transicoes,
        TransicaoStatus(status: novo, em: quando),
      ],
    );
  }
}

/// Condicoes locais do trecho. Placeholder ate o app consumir a Open-Meteo
/// pelo backend, como o painel web ja faz.
class CondicoesLocais {
  const CondicoesLocais({
    required this.temperaturaC,
    required this.condicao,
    required this.chuva24hMm,
    required this.chuvaPrevista24hMm,
    required this.ventoKmh,
  });

  final double temperaturaC;
  final String condicao;
  final double chuva24hMm;
  final double chuvaPrevista24hMm;
  final int ventoKmh;

  /// Chuva acelera o crescimento da vegetacao — mesma regra do web.
  bool get aceleraCrescimento => chuva24hMm >= 1 || chuvaPrevista24hMm >= 1;
}

class Manobra {
  const Manobra({
    required this.instrucao,
    required this.complemento,
    required this.distanciaM,
  });

  final String instrucao;
  final String complemento;
  final int distanciaM;
}

/// Rota ate o ponto. Placeholder: quando houver navegacao real, isto vem do
/// servico de rotas.
class RotaNavegacao {
  const RotaNavegacao({
    required this.destino,
    required this.distanciaKm,
    required this.tempoMin,
    required this.manobras,
  });

  final String destino;
  final double distanciaKm;
  final int tempoMin;
  final List<Manobra> manobras;
}

/// Detalhamento do servico exibido na comprovacao.
class DetalheServico {
  const DetalheServico({
    required this.tipo,
    required this.faixa,
    required this.extensaoM,
    required this.equipamento,
  });

  final String tipo;
  final String faixa;
  final int extensaoM;
  final String equipamento;
}

// --- Dados -----------------------------------------------------------------

final List<PontoVegetacao> pontosVegetacao = <PontoVegetacao>[
  PontoVegetacao(
    id: 'sp270-pv-01',
    rodovia: 'SP-270',
    km: 98.20,
    sentido: Sentido.capital,
    margem: Margem.direita,
    latitude: -23.4692,
    longitude: -47.9581,
    alturaAtualCm: 32,
    nivelRisco: NivelRisco.atencao,
    invadePista: false,
    cobrePlaca: false,
    historico: <Passagem>[
      Passagem(data: DateTime(2026, 4, 10), alturaCm: 12),
      Passagem(data: DateTime(2026, 5, 8), alturaCm: 17),
      Passagem(data: DateTime(2026, 6, 5), alturaCm: 22),
      Passagem(data: DateTime(2026, 7, 3), alturaCm: 27),
      Passagem(data: DateTime(2026, 7, 31), alturaCm: 32),
    ],
  ),
  PontoVegetacao(
    id: 'sp270-pv-02',
    rodovia: 'SP-270',
    km: 98.45,
    sentido: Sentido.capital,
    margem: Margem.esquerda,
    latitude: -23.4695,
    longitude: -47.9553,
    alturaAtualCm: 61,
    nivelRisco: NivelRisco.critico,
    invadePista: true,
    cobrePlaca: false,
    historico: <Passagem>[
      Passagem(data: DateTime(2026, 4, 10), alturaCm: 25),
      Passagem(data: DateTime(2026, 5, 8), alturaCm: 34),
      Passagem(data: DateTime(2026, 6, 5), alturaCm: 43),
      Passagem(data: DateTime(2026, 7, 3), alturaCm: 52),
      Passagem(data: DateTime(2026, 7, 31), alturaCm: 61),
    ],
  ),
  PontoVegetacao(
    id: 'sp270-pv-03',
    rodovia: 'SP-270',
    km: 98.70,
    sentido: Sentido.interior,
    margem: Margem.direita,
    latitude: -23.4699,
    longitude: -47.9525,
    alturaAtualCm: 14,
    nivelRisco: NivelRisco.tranquilo,
    invadePista: false,
    cobrePlaca: false,
    historico: <Passagem>[
      Passagem(data: DateTime(2026, 4, 10), alturaCm: 6),
      Passagem(data: DateTime(2026, 5, 8), alturaCm: 8),
      Passagem(data: DateTime(2026, 6, 5), alturaCm: 10),
      Passagem(data: DateTime(2026, 7, 3), alturaCm: 12),
      Passagem(data: DateTime(2026, 7, 31), alturaCm: 14),
    ],
  ),
  PontoVegetacao(
    id: 'sp270-pv-04',
    rodovia: 'SP-270',
    km: 98.95,
    sentido: Sentido.interior,
    margem: Margem.esquerda,
    latitude: -23.4703,
    longitude: -47.9497,
    alturaAtualCm: 50,
    nivelRisco: NivelRisco.critico,
    invadePista: false,
    cobrePlaca: true,
    historico: <Passagem>[
      Passagem(data: DateTime(2026, 4, 10), alturaCm: 22),
      Passagem(data: DateTime(2026, 5, 8), alturaCm: 29),
      Passagem(data: DateTime(2026, 6, 5), alturaCm: 36),
      Passagem(data: DateTime(2026, 7, 3), alturaCm: 43),
      Passagem(data: DateTime(2026, 7, 31), alturaCm: 50),
    ],
  ),
  PontoVegetacao(
    id: 'sp270-pv-05',
    rodovia: 'SP-270',
    km: 99.30,
    sentido: Sentido.capital,
    margem: Margem.direita,
    latitude: -23.4708,
    longitude: -47.9460,
    alturaAtualCm: 70,
    nivelRisco: NivelRisco.critico,
    invadePista: true,
    cobrePlaca: true,
    historico: <Passagem>[
      Passagem(data: DateTime(2026, 4, 10), alturaCm: 30),
      Passagem(data: DateTime(2026, 5, 8), alturaCm: 40),
      Passagem(data: DateTime(2026, 6, 5), alturaCm: 50),
      Passagem(data: DateTime(2026, 7, 3), alturaCm: 60),
      Passagem(data: DateTime(2026, 7, 31), alturaCm: 70),
    ],
  ),
  PontoVegetacao(
    id: 'sp270-pv-06',
    rodovia: 'SP-270',
    km: 99.60,
    sentido: Sentido.capital,
    margem: Margem.esquerda,
    latitude: -23.4712,
    longitude: -47.9432,
    alturaAtualCm: 21,
    nivelRisco: NivelRisco.tranquilo,
    invadePista: false,
    cobrePlaca: false,
    historico: <Passagem>[
      Passagem(data: DateTime(2026, 4, 10), alturaCm: 9),
      Passagem(data: DateTime(2026, 5, 8), alturaCm: 12),
      Passagem(data: DateTime(2026, 6, 5), alturaCm: 15),
      Passagem(data: DateTime(2026, 7, 3), alturaCm: 18),
      Passagem(data: DateTime(2026, 7, 31), alturaCm: 21),
    ],
  ),
  PontoVegetacao(
    id: 'sp270-pv-07',
    rodovia: 'SP-270',
    km: 99.90,
    sentido: Sentido.interior,
    margem: Margem.direita,
    latitude: -23.4716,
    longitude: -47.9404,
    alturaAtualCm: 42,
    nivelRisco: NivelRisco.atencao,
    invadePista: false,
    cobrePlaca: false,
    historico: <Passagem>[
      Passagem(data: DateTime(2026, 4, 10), alturaCm: 19),
      Passagem(data: DateTime(2026, 5, 8), alturaCm: 25),
      Passagem(data: DateTime(2026, 6, 5), alturaCm: 31),
      Passagem(data: DateTime(2026, 7, 3), alturaCm: 37),
      Passagem(data: DateTime(2026, 7, 31), alturaCm: 42),
    ],
  ),
  PontoVegetacao(
    id: 'sp270-pv-08',
    rodovia: 'SP-270',
    km: 100.15,
    sentido: Sentido.interior,
    margem: Margem.esquerda,
    latitude: -23.4719,
    longitude: -47.9380,
    alturaAtualCm: 29,
    nivelRisco: NivelRisco.atencao,
    invadePista: false,
    cobrePlaca: false,
    historico: <Passagem>[
      Passagem(data: DateTime(2026, 4, 10), alturaCm: 13),
      Passagem(data: DateTime(2026, 5, 8), alturaCm: 17),
      Passagem(data: DateTime(2026, 6, 5), alturaCm: 21),
      Passagem(data: DateTime(2026, 7, 3), alturaCm: 25),
      Passagem(data: DateTime(2026, 7, 31), alturaCm: 29),
    ],
  ),
];

const List<Operador> operadores = <Operador>[
  Operador(id: 'op-01', nome: 'Rafael Nogueira', matricula: 'MTV-4471'),
  Operador(id: 'op-02', nome: 'Camila Duarte', matricula: 'MTV-4482'),
  Operador(id: 'op-03', nome: 'Anderson Prado', matricula: 'MTV-4495'),
  Operador(id: 'op-04', nome: 'Juliana Freitas', matricula: 'MTV-4508'),
];

/// Operador da sessao. Enquanto nao ha autenticacao real, a tela de login
/// entra sempre com este.
final Operador operadorAtual = operadores.first;

final List<OrdemServico> ordensServico = <OrdemServico>[
  OrdemServico(
    id: 'os-01',
    pontoId: 'sp270-pv-05',
    operadorId: 'op-01',
    prioridade: Prioridade.alta,
    status: StatusOS.pendente,
    criadaEm: DateTime(2026, 8, 2, 7, 40),
    previsaoConclusao: DateTime(2026, 8, 4, 16, 30),
    transicoes: <TransicaoStatus>[],
  ),
  OrdemServico(
    id: 'os-02',
    pontoId: 'sp270-pv-02',
    operadorId: 'op-02',
    prioridade: Prioridade.alta,
    status: StatusOS.pendente,
    criadaEm: DateTime(2026, 8, 1, 14, 10),
    previsaoConclusao: DateTime(2026, 8, 5, 12, 0),
    transicoes: <TransicaoStatus>[],
  ),
  OrdemServico(
    id: 'os-03',
    pontoId: 'sp270-pv-04',
    operadorId: 'op-03',
    prioridade: Prioridade.alta,
    status: StatusOS.emDeslocamento,
    criadaEm: DateTime(2026, 8, 3, 6, 20),
    previsaoConclusao: DateTime(2026, 8, 4, 11, 0),
    transicoes: <TransicaoStatus>[
      TransicaoStatus(status: StatusOS.emDeslocamento, em: DateTime(2026, 8, 3, 8, 5)),
    ],
  ),
  OrdemServico(
    id: 'os-04',
    pontoId: 'sp270-pv-07',
    operadorId: 'op-04',
    prioridade: Prioridade.media,
    status: StatusOS.noLocal,
    criadaEm: DateTime(2026, 8, 2, 9, 0),
    previsaoConclusao: DateTime(2026, 8, 4, 10, 30),
    transicoes: <TransicaoStatus>[
      TransicaoStatus(status: StatusOS.emDeslocamento, em: DateTime(2026, 8, 3, 7, 15)),
      TransicaoStatus(status: StatusOS.noLocal, em: DateTime(2026, 8, 3, 8, 40)),
    ],
  ),
  OrdemServico(
    id: 'os-05',
    pontoId: 'sp270-pv-01',
    operadorId: 'op-01',
    prioridade: Prioridade.media,
    status: StatusOS.concluida,
    criadaEm: DateTime(2026, 7, 20, 8, 0),
    previsaoConclusao: DateTime(2026, 7, 21, 12, 0),
    transicoes: <TransicaoStatus>[
      TransicaoStatus(status: StatusOS.emDeslocamento, em: DateTime(2026, 7, 21, 7, 10)),
      TransicaoStatus(status: StatusOS.noLocal, em: DateTime(2026, 7, 21, 8, 25)),
      TransicaoStatus(status: StatusOS.concluida, em: DateTime(2026, 7, 21, 11, 50)),
    ],
  ),
  OrdemServico(
    id: 'os-06',
    pontoId: 'sp270-pv-08',
    operadorId: 'op-02',
    prioridade: Prioridade.baixa,
    status: StatusOS.concluida,
    criadaEm: DateTime(2026, 7, 10, 10, 30),
    previsaoConclusao: DateTime(2026, 7, 13, 16, 0),
    transicoes: <TransicaoStatus>[
      TransicaoStatus(status: StatusOS.emDeslocamento, em: DateTime(2026, 7, 13, 9, 5)),
      TransicaoStatus(status: StatusOS.noLocal, em: DateTime(2026, 7, 13, 10, 40)),
      TransicaoStatus(status: StatusOS.concluida, em: DateTime(2026, 7, 13, 15, 20)),
    ],
  ),
];

const CondicoesLocais condicoesLocais = CondicoesLocais(
  temperaturaC: 21.4,
  condicao: 'Parcialmente nublado',
  chuva24hMm: 3.2,
  chuvaPrevista24hMm: 1.8,
  ventoKmh: 12,
);

const RotaNavegacao rotaAtiva = RotaNavegacao(
  destino: 'SP-270, km 99,30 — sentido Capital',
  distanciaKm: 4.7,
  tempoMin: 9,
  manobras: <Manobra>[
    Manobra(
      instrucao: 'Siga em frente',
      complemento: 'pela SP-270, sentido Capital',
      distanciaM: 1200,
    ),
    Manobra(
      instrucao: 'Mantenha-se a direita',
      complemento: 'acostamento do km 99',
      distanciaM: 350,
    ),
    Manobra(
      instrucao: 'Destino a direita',
      complemento: 'ponto de rocada sinalizado',
      distanciaM: 80,
    ),
  ],
);

const DetalheServico detalheServico = DetalheServico(
  tipo: 'Rocada mecanizada de faixa de dominio',
  faixa: 'Acostamento e talude',
  extensaoM: 120,
  equipamento: 'Rocadeira costal',
);

// --- Derivados -------------------------------------------------------------

/// Crescimento medio em cm/mes entre a primeira e a ultima passagem.
/// Mesma conta do painel web.
double crescimentoMensalCm(List<Passagem> historico) {
  final Passagem primeira = historico.first;
  final Passagem ultima = historico.last;
  final double dias = ultima.data.difference(primeira.data).inDays.toDouble();
  if (dias <= 0) return 0;
  return (ultima.alturaCm - primeira.alturaCm) / (dias / 30.44);
}

PontoVegetacao pontoPorId(String id) {
  return pontosVegetacao.firstWhere((PontoVegetacao p) => p.id == id);
}

Operador operadorPorId(String id) {
  return operadores.firstWhere((Operador o) => o.id == id);
}

/// OS aberta do operador — e a que a tela 2 mostra.
OrdemServico ordemAtivaDe(Operador operador) {
  return ordensServico.firstWhere(
    (OrdemServico os) => os.operadorId == operador.id && os.estaAberta,
    orElse: () => ordensServico.first,
  );
}

String duasCasas(int valor) => valor.toString().padLeft(2, '0');

String formatarDataHora(DateTime d) =>
    '${duasCasas(d.day)}/${duasCasas(d.month)} ${duasCasas(d.hour)}:${duasCasas(d.minute)}';

String formatarHora(DateTime d) => '${duasCasas(d.hour)}:${duasCasas(d.minute)}';

/// Coordenada como o operador ve no comprovante.
String formatarCoordenada(double latitude, double longitude) =>
    '${latitude.toStringAsFixed(5)}, ${longitude.toStringAsFixed(5)}';

String saudacaoPara(DateTime agora) {
  if (agora.hour < 12) return 'Bom dia';
  if (agora.hour < 18) return 'Boa tarde';
  return 'Boa noite';
}
