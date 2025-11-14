# examples/sample_grammars.py
from typing import List, Tuple
from grammar_parser import Grammar, Production


def get_sample_grammars() -> List[Tuple[str, Grammar]]:
    """
    Regresa algunas gramáticas de ejemplo ya construidas
    para usar en la interfaz y en el modo tutor.
    """

    examples: List[Tuple[str, Grammar]] = []

    # Tipo 3 – Regular
    g3 = Grammar(
        nonterminals={"S", "A"},
        terminals={"a", "b"},
        productions=[
            Production("S", "aA"),
            Production("A", "b"),
        ],
        start_symbol="S",
    )
    examples.append(("Gramática Regular: S -> aA; A -> b", g3))

    # Tipo 2 – Libre de Contexto (no regular)
    g2 = Grammar(
        nonterminals={"S"},
        terminals={"a", "b"},
        productions=[
            Production("S", "aSb"),
            Production("S", "ab"),
        ],
        start_symbol="S",
    )
    examples.append(("Gramática GLC: S -> aSb | ab", g2))

    # Tipo 1 – Sensible al contexto (ejemplo sencillo)
    g1 = Grammar(
        nonterminals={"S", "A", "B"},
        terminals={"a", "b"},
        productions=[
            Production("S", "aSB"),
            Production("S", "ab"),
            Production("AB", "BA"),  # LHS de longitud 2, típico de GSC
        ],
        start_symbol="S",
    )
    examples.append(("Gramática GSC: incluye regla AB -> BA", g1))

    # Tipo 0 – Sin restricciones especiales (ejemplo forzado)
    g0 = Grammar(
        nonterminals={"S", "A"},
        terminals={"a", "b"},
        productions=[
            Production("S", "Aa"),
            Production("AA", "b"),  # viola longitud y forma GLC/GSC
        ],
        start_symbol="S",
    )
    examples.append(("Gramática Tipo 0: incluye regla AA -> b", g0))

    return examples
