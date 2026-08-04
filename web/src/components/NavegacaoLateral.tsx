import { NavLink } from "react-router-dom";
import "./NavegacaoLateral.css";

const SECOES = [
  { para: "/", rotulo: "Visão geral", fim: true },
  { para: "/mapa", rotulo: "Mapa", fim: false },
  { para: "/ordens", rotulo: "Ordens de serviço", fim: false },
];

export default function NavegacaoLateral() {
  return (
    <nav className="navegacao-lateral">
      {SECOES.map((secao) => (
        <NavLink
          key={secao.para}
          to={secao.para}
          end={secao.fim}
          className={({ isActive }) =>
            `navegacao-lateral__link${isActive ? " navegacao-lateral__link--ativo" : ""}`
          }
        >
          {secao.rotulo}
        </NavLink>
      ))}
    </nav>
  );
}
