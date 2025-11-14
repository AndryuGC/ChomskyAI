# grammar_parser.py
from dataclasses import dataclass
from typing import List, Set


@dataclass
class Production:
    lhs: str
    rhs: str  # cadena completa del lado derecho


@dataclass
class Grammar:
    nonterminals: Set[str]
    terminals: Set[str]
    productions: List[Production]
    start_symbol: str


class GrammarParser:

    ARROWS = ["->", "→", "⇒"]

    @classmethod
    def parse(cls, text: str) -> Grammar:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            raise ValueError("No se encontraron reglas de gramática.")

        productions: List[Production] = []
        nonterminals: Set[str] = set()
        terminals: Set[str] = set()

        # Detectar símbolo inicial como el LHS de la primera producción
        start_symbol = None

        for line in lines:
            arrow_used = None
            for arrow in cls.ARROWS:
                if arrow in line:
                    arrow_used = arrow
                    break

            if arrow_used is None:
                raise ValueError(
                    f"Línea inválida (falta '->' o flecha): {line}"
                )

            lhs_part, rhs_part = line.split(arrow_used, 1)
            lhs_part = lhs_part.strip()
            rhs_part = rhs_part.strip()

            if not lhs_part or len(lhs_part) != 1 or not lhs_part.isupper():
                raise ValueError(
                    f"Lado izquierdo inválido '{lhs_part}'. "
                    "Debe ser un único no terminal en MAYÚSCULA (ej. S, A)."
                )

            lhs = lhs_part
            if start_symbol is None:
                start_symbol = lhs

            nonterminals.add(lhs)

            alternatives = [alt.strip() for alt in rhs_part.split("|")]

            for alt in alternatives:
                if alt in ("ε", "epsilon", "EPS", "λ"):
                    rhs = ""  # representamos epsilon como cadena vacía
                else:
                    rhs = alt.replace(" ", "")

                productions.append(Production(lhs=lhs, rhs=rhs))

                # Clasificar símbolos en terminales / no terminales
                for ch in rhs:
                    if ch.isupper():
                        nonterminals.add(ch)
                    else:
                        terminals.add(ch)

        if start_symbol is None:
            raise ValueError("No se pudo determinar el símbolo inicial.")

        terminals.discard("")

        return Grammar(
            nonterminals=nonterminals,
            terminals=terminals,
            productions=productions,
            start_symbol=start_symbol,
        )
