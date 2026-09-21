import { useState } from "react";
import "./LoginWeb.css";

const USUARIO_DEMO = "gestor@motiva.demo";
const SENHA_DEMO = "MotivaGestao2026!";

export default function LoginWeb({ onEntrar }: { onEntrar: () => void }) {
  const [usuario, setUsuario] = useState(USUARIO_DEMO);
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState("");
  function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    if (usuario.trim().toLowerCase() !== USUARIO_DEMO || senha !== SENHA_DEMO) {
      setErro("Credenciais não reconhecidas. Confira o acesso demonstrativo.");
      return;
    }
    onEntrar();
  }
  return <main className="login-web"><section className="login-web__marca"><div className="login-web__sinal" /><p>MONITORAMENTO DE FAIXA DE DOMÍNIO</p><h1>MOTIVA<span>FIELD</span></h1><strong>Inteligência operacional para decisões de campo.</strong><ul><li>Risco priorizado por trecho</li><li>Evidências auditáveis por imagem</li><li>Execução monitorada em tempo real</li></ul></section><section className="login-web__painel"><form onSubmit={enviar}><p className="login-web__eyebrow">Acesso operacional</p><h2>Entrar no painel</h2><span>Use suas credenciais de gestão para continuar.</span><label>E-mail<input value={usuario} onChange={(e) => setUsuario(e.target.value)} type="email" autoComplete="username" /></label><label>Senha<input value={senha} onChange={(e) => setSenha(e.target.value)} type="password" autoComplete="current-password" autoFocus /></label>{erro && <p className="login-web__erro">{erro}</p>}<button type="submit">Acessar centro de operações</button><small>Ambiente local de demonstração · credenciais não são autenticação de produção.</small></form></section></main>;
}
