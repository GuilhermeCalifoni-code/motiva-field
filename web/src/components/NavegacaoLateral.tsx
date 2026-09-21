import { NavLink } from "react-router-dom";
import "./NavegacaoLateral.css";
import { Icon } from "./atoms/Icon";

const SECOES = [
  { para: "/", rotulo: "Visão geral", icone: "grid" as const, fim: true },
  { para: "/mapa", rotulo: "Mapa operacional", icone: "map" as const, fim: false },
  { para: "/ordens", rotulo: "Ordens de serviço", icone: "clipboard" as const, fim: false },
  { para: "/inteligencia", rotulo: "Central de inteligência", icone: "spark" as const, fim: false },
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
          <Icon name={secao.icone} />
          <span>{secao.rotulo}</span>
        </NavLink>
      ))}
    </nav>
  );
}
