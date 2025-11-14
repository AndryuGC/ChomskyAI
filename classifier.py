# classifier.py
from typing import List, Dict
from grammar_parser import Grammar, Production


class ClassificationResult:
    def __init__(self, grammar_type: int, label: str, explanation: List[str]):
        self.grammar_type = grammar_type  # 0,1,2,3
        self.label = label                # texto humano
        self.explanation = explanation    # pasos del razonamiento


def _length_no_epsilon(rhs: str) -> int:
    """Cuenta la longitud de la producción sin epsilon (epsilon = cadena vacía)."""
    return len(rhs)


def _is_regular(grammar: Grammar, explanation: List[str]) -> bool:
    """
    Checa si es Tipo 3 (Regular) con reglas tipo:
       A -> aB | a | ε
    Asumimos gramática lineal por la derecha.
    """
    ok = True
    for p in grammar.productions:
        lhs = p.lhs
        rhs = p.rhs

        if len(lhs) != 1 or lhs not in grammar.nonterminals:
            explanation.append(
                f"❌ Producción {lhs} -> {rhs}: el lado izquierdo debe ser un "
                f"solo no terminal (A)."
            )
            ok = False
            continue

        if rhs == "":
            # epsilon permitido, pero solo para el símbolo inicial
            if lhs != grammar.start_symbol:
                explanation.append(
                    f"❌ Producción {lhs} -> ε: epsilon sólo se permite para el "
                    f"símbolo inicial."
                )
                ok = False
            else:
                explanation.append(
                    f"✅ {lhs} -> ε permitido (símbolo inicial)."
                )
            continue

        # RHS regular right-linear:  a  ó  aB  ó  a1a2...a_kB
        nonterminals_in_rhs = [ch for ch in rhs if ch in grammar.nonterminals]

        if len(nonterminals_in_rhs) > 1:
            explanation.append(
                f"❌ {lhs} -> {rhs}: hay más de un no terminal en el lado derecho."
            )
            ok = False
            continue

        if len(nonterminals_in_rhs) == 1:
            last_nt = nonterminals_in_rhs[0]
            if rhs[-1] != last_nt:
                explanation.append(
                    f"❌ {lhs} -> {rhs}: el no terminal debe ir al FINAL (forma a*B)."
                )
                ok = False
                continue

        # Revisar que todo lo que no es NT sea terminal
        for ch in rhs:
            if ch not in grammar.nonterminals and ch not in grammar.terminals:
                explanation.append(
                    f"❌ {lhs} -> {rhs}: el símbolo '{ch}' no está identificado "
                    f"como terminal ni no terminal."
                )
                ok = False
                break
        else:
            if ok:
                explanation.append(f"✅ {lhs} -> {rhs} es compatible con gramática regular.")

    if ok:
        explanation.append("✅ Todas las producciones cumplen con la forma Regular (Tipo 3).")
    else:
        explanation.append("❌ La gramática NO es Regular (Tipo 3).")
    return ok


def _is_context_free(grammar: Grammar, explanation: List[str]) -> bool:
    """
    Tipo 2 (Libre de Contexto):
      A -> β
    con A un solo no terminal.
    """
    ok = True
    for p in grammar.productions:
        lhs = p.lhs
        rhs = p.rhs
        if len(lhs) != 1 or lhs not in grammar.nonterminals:
            explanation.append(
                f"❌ {lhs} -> {rhs}: en una GLC el lado izquierdo debe ser "
                f"un único no terminal (A)."
            )
            ok = False
        else:
            explanation.append(
                f"✅ {lhs} -> {rhs}: cumple condición de GLC (A -> β)."
            )

    if ok:
        explanation.append("✅ Todas las producciones cumplen la forma de GLC (Tipo 2).")
    else:
        explanation.append("❌ La gramática NO es puramente Libre de Contexto (Tipo 2).")
    return ok


def _is_context_sensitive(grammar: Grammar, explanation: List[str]) -> bool:
    """
    Tipo 1 (Sensible al Contexto):
      Longitud no decrece: |α| <= |β| para todas las producciones,
      salvo posible S -> ε (si S no aparece en ningún RHS).
    """
    ok = True
    start = grammar.start_symbol

    # Checar si S aparece en algún RHS
    s_in_rhs = any(start in p.rhs for p in grammar.productions)

    for p in grammar.productions:
        lhs = p.lhs
        rhs = p.rhs

        if rhs == "" and lhs == start and not s_in_rhs:
            explanation.append(
                f"✅ {lhs} -> ε permitido en GSC (S no aparece en ningún RHS)."
            )
            continue

        len_lhs = len(lhs)
        len_rhs = _length_no_epsilon(rhs)

        if len_rhs < len_lhs:
            explanation.append(
                f"❌ {lhs} -> {rhs}: |LHS|={len_lhs} > |RHS|={len_rhs}. "
                f"Viola condición sensible al contexto."
            )
            ok = False
        else:
            explanation.append(
                f"✅ {lhs} -> {rhs}: |LHS|={len_lhs} <= |RHS|={len_rhs}."
            )

    if ok:
        explanation.append("✅ Gramática cumple condiciones de GSC (Tipo 1).")
    else:
        explanation.append("❌ La gramática NO es Sensible al Contexto (Tipo 1).")
    return ok


def classify_grammar(grammar: Grammar) -> ClassificationResult:
    """
    Clasifica la gramática en el tipo MÁS RESTRICTIVO posible (3, luego 2, luego 1, luego 0).
    Devuelve un objeto con el tipo y una explicación paso a paso.
    """
    explanation: List[str] = []
    explanation.append("🔎 Iniciando clasificación de la gramática según la Jerarquía de Chomsky.")

    # 1. Intentar Regular (Tipo 3)
    explanation.append("\n=== Paso 1: Verificar si es Regular (Tipo 3) ===")
    if _is_regular(grammar, explanation):
        return ClassificationResult(
            grammar_type=3,
            label="Tipo 3 – Gramática Regular",
            explanation=explanation,
        )

    # 2. Intentar Libre de Contexto (Tipo 2)
    explanation.append("\n=== Paso 2: Verificar si es Libre de Contexto (Tipo 2) ===")
    if _is_context_free(grammar, explanation):
        return ClassificationResult(
            grammar_type=2,
            label="Tipo 2 – Gramática Libre de Contexto (GLC)",
            explanation=explanation,
        )

    # 3. Intentar Sensible al Contexto (Tipo 1)
    explanation.append("\n=== Paso 3: Verificar si es Sensible al Contexto (Tipo 1) ===")
    if _is_context_sensitive(grammar, explanation):
        return ClassificationResult(
            grammar_type=1,
            label="Tipo 1 – Gramática Sensible al Contexto (GSC)",
            explanation=explanation,
        )

    # 4. Si nada se cumple, es Tipo 0
    explanation.append("\n=== Paso 4: Clasificación final ===")
    explanation.append(
        "La gramática no cumple las restricciones de Tipo 3, 2 ni 1.\n"
        "➡ Se clasifica como Tipo 0 – Recursivamente enumerable."
    )
    return ClassificationResult(
        grammar_type=0,
        label="Tipo 0 – Gramática de Tipo 0 (Recursivamente enumerable)",
        explanation=explanation,
    )
