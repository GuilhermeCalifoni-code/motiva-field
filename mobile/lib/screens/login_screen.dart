import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../estado_operacao.dart';
import '../mock_data.dart';
import '../theme.dart';
import 'ordem_ativa_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _cpf = TextEditingController();
  final TextEditingController _senha = TextEditingController();
  bool _senhaVisivel = false;

  @override
  void dispose() {
    _cpf.dispose();
    _senha.dispose();
    super.dispose();
  }

  void _entrar() {
    // Ainda nao ha autenticacao: o login entra com o operador da sessao.
    final EstadoOperacao estado = EstadoOperacao(operador: operadorAtual);
    Navigator.of(context).pushReplacement(
      MaterialPageRoute<void>(
        builder: (BuildContext context) => OrdemAtivaScreen(estado: estado),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Cores.roxo,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(
            horizontal: Espacos.x6,
            vertical: Espacos.x7,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              const SizedBox(height: Espacos.x6),
              const _Logo(),
              const SizedBox(height: Espacos.x7),
              const Text('CPF', style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.8,
                color: Cores.sobreRoxo,
              )),
              const SizedBox(height: Espacos.x2),
              _Campo(
                controlador: _cpf,
                dica: '000.000.000-00',
                teclado: TextInputType.number,
                formatadores: <TextInputFormatter>[
                  FilteringTextInputFormatter.digitsOnly,
                  LengthLimitingTextInputFormatter(11),
                ],
              ),
              const SizedBox(height: Espacos.x5),
              const Text('SENHA', style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.8,
                color: Cores.sobreRoxo,
              )),
              const SizedBox(height: Espacos.x2),
              _Campo(
                controlador: _senha,
                dica: 'Sua senha',
                ocultar: !_senhaVisivel,
                sufixo: IconButton(
                  icon: Icon(
                    _senhaVisivel ? Icons.visibility_off : Icons.visibility,
                    color: Cores.sobreRoxo,
                    size: 20,
                  ),
                  onPressed: () => setState(() => _senhaVisivel = !_senhaVisivel),
                ),
              ),
              const SizedBox(height: Espacos.x6),
              ElevatedButton(onPressed: _entrar, child: const Text('Entrar')),
              const SizedBox(height: Espacos.x5),
              const _Separador(),
              const SizedBox(height: Espacos.x5),
              // Biometria e so visual nesta fase.
              OutlinedButton.icon(
                onPressed: _entrar,
                icon: const Icon(Icons.fingerprint, size: 26),
                label: const Text('Entrar com biometria'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: Cores.sobreEscuro,
                  side: const BorderSide(color: Cores.roxoClaro),
                  minimumSize: const Size.fromHeight(52),
                  textStyle: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(Raios.sm),
                  ),
                ),
              ),
              const SizedBox(height: Espacos.x6),
              const Text(
                'Motiva Field · versao de demonstracao',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 12, color: Cores.sobreRoxo),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Logo extends StatelessWidget {
  const _Logo();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: <Widget>[
        Container(
          width: 68,
          height: 68,
          decoration: BoxDecoration(
            color: Cores.ouro,
            borderRadius: BorderRadius.circular(Raios.lg),
          ),
          child: const Icon(Icons.grass, size: 38, color: Cores.roxoEscuro),
        ),
        const SizedBox(height: Espacos.x4),
        const Text(
          'MOTIVA FIELD',
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.6,
            color: Cores.sobreEscuro,
          ),
        ),
        const SizedBox(height: Espacos.x2),
        const Text(
          'Operacao de campo',
          style: TextStyle(fontSize: 14, color: Cores.sobreRoxo),
        ),
      ],
    );
  }
}

class _Campo extends StatelessWidget {
  const _Campo({
    required this.controlador,
    required this.dica,
    this.teclado,
    this.ocultar = false,
    this.sufixo,
    this.formatadores,
  });

  final TextEditingController controlador;
  final String dica;
  final TextInputType? teclado;
  final bool ocultar;
  final Widget? sufixo;
  final List<TextInputFormatter>? formatadores;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controlador,
      keyboardType: teclado,
      obscureText: ocultar,
      inputFormatters: formatadores,
      style: const TextStyle(fontSize: 16, color: Cores.sobreEscuro),
      decoration: InputDecoration(
        hintText: dica,
        hintStyle: const TextStyle(color: Cores.roxoClaro),
        suffixIcon: sufixo,
        filled: true,
        fillColor: Cores.roxoTranslucido,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: Espacos.x4,
          vertical: Espacos.x4,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(Raios.sm),
          borderSide: const BorderSide(color: Cores.roxoClaro),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(Raios.sm),
          borderSide: const BorderSide(color: Cores.ouro, width: 2),
        ),
      ),
    );
  }
}

class _Separador extends StatelessWidget {
  const _Separador();

  @override
  Widget build(BuildContext context) {
    return const Row(
      children: <Widget>[
        Expanded(child: Divider(color: Cores.roxoClaro)),
        Padding(
          padding: EdgeInsets.symmetric(horizontal: Espacos.x4),
          child: Text('ou', style: TextStyle(color: Cores.sobreRoxo, fontSize: 13)),
        ),
        Expanded(child: Divider(color: Cores.roxoClaro)),
      ],
    );
  }
}
