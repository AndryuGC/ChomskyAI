# visualizer.py
from typing import List
from grammar_parser import Grammar, Production


def grammar_to_dot(grammar: Grammar) -> str:
    """
    Versión muy sencilla: genera un grafo DOT donde cada no terminal es un nodo
    y cada producción A -> α genera aristas A -> X por cada no terminal X en α.
    Esto se puede usar con Graphviz (dot) para generar PNG/SVG.
    """
    lines: List[str] = ['digraph Grammar {', '  rankdir=LR;']

    # Crear nodos para no terminales
    for nt in grammar.nonterminals:
        if nt == grammar.start_symbol:
            lines.append(f'  "{nt}" [shape=doublecircle, label="{nt} (S)"];')
        else:
            lines.append(f'  "{nt}" [shape=circle];')

    # Crear aristas según apariciones de no terminales en RHS
    for p in grammar.productions:
        for ch in p.rhs:
            if ch in grammar.nonterminals:
                lines.append(f'  "{p.lhs}" -> "{ch}" [label="{p.rhs}"];')

    lines.append("}")
    return "\n".join(lines)
