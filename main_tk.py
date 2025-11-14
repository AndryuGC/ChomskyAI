# main_tk.py
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import random
import os
from datetime import datetime

from grammar_parser import GrammarParser, Grammar
from classifier import classify_grammar
from examples.sample_grammars import get_sample_grammars

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False



def generar_cadenas(grammar: Grammar, max_len: int, max_expansiones: int = 2000):
    NT = grammar.nonterminals
    start = grammar.start_symbol

    from collections import deque

    inicial = start
    visitados = set([inicial])
    q = deque([inicial])
    cadenas = set()
    expansiones = 0

    while q and expansiones < max_expansiones:
        actual = q.popleft()
        expansiones += 1

        # Si ya es solo terminales
        if all(ch not in NT for ch in actual):
            if len(actual) <= max_len:
                cadenas.add(actual)
            continue

        if len(actual) > max_len + 2:
            continue

        # Primer no terminal
        idx_nt = None
        for i, ch in enumerate(actual):
            if ch in NT:
                idx_nt = i
                break
        if idx_nt is None:
            continue

        A = actual[idx_nt]

        for p in grammar.productions:
            if p.lhs != A:
                continue
            rhs = p.rhs  # "" representa epsilon
            nuevo = actual[:idx_nt] + rhs + actual[idx_nt + 1:]
            if nuevo not in visitados and len(nuevo) <= max_len + len(NT):
                visitados.add(nuevo)
                q.append(nuevo)

    return cadenas

EPS = 'ε'


def limpiar_regex(regex: str) -> str:
    return ''.join(ch for ch in regex if not ch.isspace())


def es_simbolo(c: str) -> bool:
    return c not in {'(', ')', '|', '*', '.'}


def agregar_concatenacion(regex: str) -> str:
    """
    Inserta '.' donde la concatenación es implícita.
    Ej: (ab)*a -> (a.b)*.a
    """
    res = []
    for i, c in enumerate(regex):
        res.append(c)
        if i == len(regex) - 1:
            continue
        d = regex[i + 1]
        if (es_simbolo(c) or c in {')', '*'}) and (es_simbolo(d) or d == '('):
            res.append('.')
    return ''.join(res)


def regex_a_postfix(regex: str) -> str:

    prec = {'|': 1, '.': 2}
    salida = []
    pila = []

    for c in regex:
        if es_simbolo(c):
            salida.append(c)
        elif c == '(':
            pila.append(c)
        elif c == ')':
            while pila and pila[-1] != '(':
                salida.append(pila.pop())
            if not pila:
                raise ValueError("Paréntesis desbalanceados")
            pila.pop()
        elif c in {'.', '|'}:
            while pila and pila[-1] in prec and prec[pila[-1]] >= prec[c]:
                salida.append(pila.pop())
            pila.append(c)
        elif c == '*':
            salida.append(c)
        else:
            raise ValueError(f"Símbolo no soportado en regex: {c}")

    while pila:
        op = pila.pop()
        if op in {'(', ')'}:
            raise ValueError("Paréntesis desbalanceados")
        salida.append(op)

    return ''.join(salida)


class NFAFragment:
    def __init__(self, start, accept, transitions):
        self.start = start
        self.accept = accept
        self.transitions = transitions  # dict[state][symbol] -> set(states)


def agregar_transicion(trans, src, symbol, dst):
    if src not in trans:
        trans[src] = {}
    if symbol not in trans[src]:
        trans[src][symbol] = set()
    trans[src][symbol].add(dst)


def postfix_a_nfa(postfix: str):
    """
    Construcción de Thompson.
    Retorna (start, accept, transitions, alfabeto)
    """
    stack = []
    transitions = {}
    state_counter = 0
    alphabet = set()

    for c in postfix:
        if es_simbolo(c):
            s = state_counter
            f = state_counter + 1
            state_counter += 2
            agregar_transicion(transitions, s, c, f)
            alphabet.add(c)
            stack.append(NFAFragment(s, f, transitions))
        elif c == '.':
            # concatenación
            b = stack.pop()
            a = stack.pop()
            agregar_transicion(transitions, a.accept, EPS, b.start)
            stack.append(NFAFragment(a.start, b.accept, transitions))
        elif c == '|':
            b = stack.pop()
            a = stack.pop()
            s = state_counter
            f = state_counter + 1
            state_counter += 2
            agregar_transicion(transitions, s, EPS, a.start)
            agregar_transicion(transitions, s, EPS, b.start)
            agregar_transicion(transitions, a.accept, EPS, f)
            agregar_transicion(transitions, b.accept, EPS, f)
            stack.append(NFAFragment(s, f, transitions))
        elif c == '*':
            a = stack.pop()
            s = state_counter
            f = state_counter + 1
            state_counter += 2
            agregar_transicion(transitions, s, EPS, a.start)
            agregar_transicion(transitions, s, EPS, f)
            agregar_transicion(transitions, a.accept, EPS, a.start)
            agregar_transicion(transitions, a.accept, EPS, f)
            stack.append(NFAFragment(s, f, transitions))
        else:
            raise ValueError(f"Operador no soportado en postfix: {c}")

    if len(stack) != 1:
        raise ValueError("Error al construir el AFN (stack no quedó en 1)")

    frag = stack[0]
    # Asegurar que todos los estados aparecen en transitions
    all_states = set(transitions.keys())
    for d in transitions.values():
        for dests in d.values():
            all_states |= dests
    for s in all_states:
        transitions.setdefault(s, {})
    return frag.start, frag.accept, transitions, alphabet


def epsilon_cierre(states, transitions):
    stack = list(states)
    cierre = set(states)
    while stack:
        s = stack.pop()
        for dest in transitions.get(s, {}).get(EPS, set()):
            if dest not in cierre:
                cierre.add(dest)
                stack.append(dest)
    return cierre


def mover(states, symbol, transitions):
    dest = set()
    for s in states:
        dest |= transitions.get(s, {}).get(symbol, set())
    return dest


def nfa_a_dfa(start_nfa, accept_nfa, transitions, alphabet):
    from collections import deque

    dfa_states = {}
    dfa_trans = {}
    dfa_accepts = set()

    start_set = frozenset(epsilon_cierre({start_nfa}, transitions))
    dfa_states[0] = start_set
    queue = deque([0])
    next_id = 1

    if accept_nfa in start_set:
        dfa_accepts.add(0)

    while queue:
        sid = queue.popleft()
        current_set = dfa_states[sid]
        dfa_trans[sid] = {}
        for a in alphabet:
            move_set = mover(current_set, a, transitions)
            if not move_set:
                continue
            new_set = frozenset(epsilon_cierre(move_set, transitions))
            # buscar si ya existe
            existing_id = None
            for k, sset in dfa_states.items():
                if sset == new_set:
                    existing_id = k
                    break
            if existing_id is None:
                existing_id = next_id
                dfa_states[existing_id] = new_set
                queue.append(existing_id)
                next_id += 1
                if accept_nfa in new_set:
                    dfa_accepts.add(existing_id)
            dfa_trans[sid][a] = existing_id

    dfa_start = 0
    return dfa_states, dfa_start, dfa_accepts, dfa_trans


def dfa_a_gramatica_regular(dfa_states, dfa_start, dfa_accepts, dfa_trans):
    lines = []
    lines.append(f"Gramática Regular (símbolo inicial: Q{dfa_start})\n")
    for sid in sorted(dfa_states.keys()):
        nombre = f"Q{sid}"
        trans = dfa_trans.get(sid, {})
        for a, dest in trans.items():
            lines.append(f"{nombre} -> {a} Q{dest}")
        if sid in dfa_accepts:
            lines.append(f"{nombre} -> {EPS}")
    return '\n'.join(lines)


def describir_afn(start, accept, trans, alphabet):
    lines = []
    estados = sorted(trans.keys())
    lines.append(f"Estados: {estados}")
    lines.append(f"Estado inicial: {start}")
    lines.append(f"Estado de aceptación: {accept}")
    lines.append(f"Alfabeto: {sorted(alphabet)}")
    lines.append("Transiciones:")
    for s in estados:
        for sym, dests in trans[s].items():
            for d in dests:
                lines.append(f"  {s} --{sym}--> {d}")
    return '\n'.join(lines)


def describir_afd(dfa_states, dfa_start, dfa_accepts, dfa_trans, alphabet):
    lines = []
    estados = sorted(dfa_states.keys())
    lines.append("Estados: " + ", ".join(f"Q{i}" for i in estados))
    lines.append(f"Estado inicial: Q{dfa_start}")
    lines.append("Estados de aceptación: " +
                 ", ".join(f"Q{i}" for i in sorted(dfa_accepts)))
    lines.append("Alfabeto: " + ", ".join(sorted(alphabet)))
    lines.append("Transiciones:")
    for sid in estados:
        trans = dfa_trans.get(sid, {})
        for a, dest in trans.items():
            lines.append(f"  Q{sid} --{a}--> Q{dest}")
    return '\n'.join(lines)


class ChomskyApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Chomsky Classifier AI")
        self.geometry("1150x650")

        # ---------- Notebook con pestañas ----------
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_clasificador = ttk.Frame(self.notebook)
        self.tab_conversor = ttk.Frame(self.notebook)
        self.tab_comparador = ttk.Frame(self.notebook)
        self.tab_tutor = ttk.Frame(self.notebook)
        self.tab_generador = ttk.Frame(self.notebook)

        # NOMBRES TOMADOS DEL .DOCX
        self.notebook.add(self.tab_clasificador, text="Modo Explicativo Inteligente")
        self.notebook.add(self.tab_conversor, text="Conversores entre Representaciones")
        self.notebook.add(self.tab_comparador, text="Reporte de Desempeño y Modo Comparativo")
        self.notebook.add(self.tab_tutor, text="Modo Tutor Interactivo (Quiz)")
        self.notebook.add(self.tab_generador, text="Generador Automático de Ejemplos")

        # Datos globales para modo tutor / generador
        self.sample_grammars = get_sample_grammars()
        self.idx_pregunta = 0

        # Construir pestañas
        self._build_tab_clasificador()
        self._build_tab_conversor()
        self._build_tab_comparador()
        self._build_tab_tutor()
        self._build_tab_generador()

    def _build_tab_clasificador(self):
        frame = self.tab_clasificador

        left = tk.Frame(frame, padx=10, pady=10)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right = tk.Frame(frame, padx=10, pady=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        header = tk.Label(
            left,
            text="Modo Explicativo Inteligente – Clasificador de Gramáticas (Tipos 0–3)",
            font=("Arial", 11, "bold")
        )
        header.pack(anchor="w", pady=(0, 5))

        lbl_input = tk.Label(left, text="Gramática de Entrada (una producción por línea):")
        lbl_input.pack(anchor="w")

        example_text = "S -> aA\nA -> b"
        self.txt_grammar = scrolledtext.ScrolledText(
            left, width=50, height=18, wrap=tk.WORD
        )
        self.txt_grammar.insert(tk.END, example_text)
        self.txt_grammar.pack(fill=tk.BOTH, expand=True)

        lbl_cadena = tk.Label(
            left,
            text="Ingresa una cadena para probar si pertenece al lenguaje (ej. a b):"
        )
        lbl_cadena.pack(anchor="w", pady=(10, 0))

        self.entry_cadena = tk.Entry(left)
        self.entry_cadena.pack(fill=tk.X)

        btn = tk.Button(
            left,
            text="Clasificar y Generar Explicación",
            command=self.classify_and_generate_action,
            bg="#3B82F6",
            fg="white"
        )
        btn.pack(pady=10, fill=tk.X)

        # Panel derecho
        self.lbl_result = tk.Label(
            right,
            text="Clasificación: (pendiente)",
            font=("Arial", 13, "bold"),
        )
        self.lbl_result.pack(anchor="w")

        lbl_exp = tk.Label(right, text="Explicación del modo inteligente:")
        lbl_exp.pack(anchor="w")

        self.txt_explanation = scrolledtext.ScrolledText(
            right, width=60, height=12, wrap=tk.WORD
        )
        self.txt_explanation.pack(fill=tk.BOTH, expand=True)

        lbl_prod = tk.Label(right, text="Producciones detectadas:")
        lbl_prod.pack(anchor="w", pady=(8, 0))

        self.txt_productions = scrolledtext.ScrolledText(
            right, width=60, height=6, wrap=tk.WORD
        )
        self.txt_productions.pack(fill=tk.BOTH, expand=True)

        lbl_cad_result = tk.Label(right, text="Resultado para la cadena ingresada:")
        lbl_cad_result.pack(anchor="w", pady=(8, 0))

        self.lbl_cadena_resultado = tk.Label(
            right, text="(sin probar)", fg="gray"
        )
        self.lbl_cadena_resultado.pack(anchor="w")

        # Botón para generar PDF (inciso de Reportes PDF)
        btn_pdf = tk.Button(
            right,
            text="Descargar reporte PDF",
            command=self.generar_pdf_action
        )
        btn_pdf.pack(anchor="e", pady=5)

    def classify_and_generate_action(self):
        text = self.txt_grammar.get("1.0", tk.END).strip()
        cadena = self.entry_cadena.get().strip()

        if not text:
            messagebox.showwarning("Advertencia", "Ingresa alguna gramática primero.")
            return

        try:
            grammar = GrammarParser.parse(text)
            result = classify_grammar(grammar)

            self.lbl_result.config(text=f"Clasificación: {result.label}")

            self.txt_explanation.delete("1.0", tk.END)
            for line in result.explanation:
                self.txt_explanation.insert(tk.END, line + "\n")

            self.txt_productions.delete("1.0", tk.END)
            for p in grammar.productions:
                rhs_display = p.rhs if p.rhs != "" else EPS
                self.txt_productions.insert(tk.END, f"{p.lhs} -> {rhs_display}\n")

            if cadena:
                max_len = max(10, len(cadena) + 2)
                cadenas = generar_cadenas(grammar, max_len=max_len)
                if cadena in cadenas:
                    self.lbl_cadena_resultado.config(
                        text=f"La cadena '{cadena}' SÍ puede ser generada por esta gramática.",
                        fg="darkgreen"
                    )
                else:
                    self.lbl_cadena_resultado.config(
                        text=f"La cadena '{cadena}' NO se generó en la búsqueda (hasta longitud {max_len}).",
                        fg="darkred"
                    )
            else:
                self.lbl_cadena_resultado.config(
                    text="(no se ingresó cadena para probar)", fg="gray"
                )

        except Exception as e:
            messagebox.showerror("Error al analizar", str(e))

    def generar_pdf_action(self):
        """Genera un reporte PDF con la gramática, clasificación y explicación."""
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror(
                "Reporte PDF",
                "Necesitas instalar reportlab en tu entorno:\n\n"
                "python -m pip install reportlab"
            )
            return

        gram_text = self.txt_grammar.get("1.0", tk.END).strip()
        exp_text = self.txt_explanation.get("1.0", tk.END).strip()
        prods_text = self.txt_productions.get("1.0", tk.END).strip()
        clasif = self.lbl_result.cget("text")
        cadena = self.entry_cadena.get().strip()
        cadena_res = self.lbl_cadena_resultado.cget("text")

        if not gram_text:
            messagebox.showwarning(
                "Reporte PDF",
                "Primero ingresa una gramática y pulsa 'Clasificar y Generar Explicación'."
            )
            return

        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reporte_chomsky_{now}.pdf"

        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        y = height - 50

        def draw_line(line, y_pos, font="Helvetica", size=10, bold=False):
            if bold:
                c.setFont("Helvetica-Bold", size)
            else:
                c.setFont("Helvetica", size)
            c.drawString(50, y_pos, line)
            return y_pos - 14

        # Título
        y = draw_line("Reporte – Chomsky Classifier AI", y, size=14, bold=True)
        y -= 10
        y = draw_line(clasif, y)

        if cadena:
            y = draw_line(f"Cadena analizada: {cadena}", y)
            y = draw_line(cadena_res, y)

        # Gramática
        y -= 15
        y = draw_line("Gramática de entrada:", y, bold=True)
        for line in gram_text.splitlines():
            if y < 60:
                c.showPage()
                y = height - 50
                y = draw_line("Reporte – Chomsky Classifier AI (continúa)", y, bold=True)
                y -= 10
            y = draw_line(line, y)

        # Producciones detectadas
        y -= 15
        y = draw_line("Producciones detectadas:", y, bold=True)
        for line in prods_text.splitlines():
            if y < 60:
                c.showPage()
                y = height - 50
                y = draw_line("Reporte – Chomsky Classifier AI (continúa)", y, bold=True)
                y -= 10
            y = draw_line(line, y)

        # Explicación
        y -= 15
        y = draw_line("Explicación del modo inteligente:", y, bold=True)
        for line in exp_text.splitlines():
            if y < 60:
                c.showPage()
                y = height - 50
                y = draw_line("Reporte – Chomsky Classifier AI (continúa)", y, bold=True)
                y -= 10
            y = draw_line(line, y)

        c.showPage()
        c.save()

        messagebox.showinfo(
            "Reporte PDF",
            f"Reporte guardado como:\n{os.path.abspath(filename)}"
        )

    # ==================== TAB 2: CONVERSORES ENTRE REPRESENTACIONES ====================
    def _build_tab_conversor(self):
        frame = self.tab_conversor

        top = tk.Frame(frame, padx=10, pady=10)
        top.pack(fill=tk.BOTH, expand=False)

        lbl = tk.Label(
            top,
            text="Conversores entre Representaciones\nRegex ⇒ AFN ⇒ AFD ⇒ Gramática Regular (Tipo 3)",
            font=("Arial", 11, "bold")
        )
        lbl.pack(anchor="w")

        lbl_regex = tk.Label(
            top,
            text="Ingresa una expresión regular (ej. (a|b)*abb ). Símbolos simples: a, b, c..."
        )
        lbl_regex.pack(anchor="w", pady=(10, 0))

        self.entry_regex = tk.Entry(top)
        self.entry_regex.pack(fill=tk.X)

        btn = tk.Button(
            top,
            text="Convertir Representaciones",
            command=self.convertir_regex_action
        )
        btn.pack(pady=8, anchor="w")

        middle = tk.Frame(frame, padx=10, pady=10)
        middle.pack(fill=tk.BOTH, expand=True)

        col1 = tk.Frame(middle)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(col1, text="1. Regex ⇒ AFN").pack(anchor="w")
        self.txt_afn = scrolledtext.ScrolledText(col1, width=40, height=15)
        self.txt_afn.pack(fill=tk.BOTH, expand=True)

        col2 = tk.Frame(middle)
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(col2, text="2. AFN ⇒ AFD").pack(anchor="w")
        self.txt_afd = scrolledtext.ScrolledText(col2, width=40, height=15)
        self.txt_afd.pack(fill=tk.BOTH, expand=True)

        col3 = tk.Frame(middle)
        col3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(col3, text="3. AFD ⇒ Gramática Regular (Tipo 3)").pack(anchor="w")
        self.txt_gr_regular = scrolledtext.ScrolledText(col3, width=40, height=15)
        self.txt_gr_regular.pack(fill=tk.BOTH, expand=True)

        bottom = tk.Frame(frame, padx=10, pady=5)
        bottom.pack(fill=tk.X)
        tk.Label(
            bottom,
            fg="gray"
        ).pack(anchor="w")

    def convertir_regex_action(self):
        try:
            regex = limpiar_regex(self.entry_regex.get())
            if not regex:
                messagebox.showwarning("Advertencia", "Ingresa una expresión regular.")
                return

            regex_conc = agregar_concatenacion(regex)
            postfix = regex_a_postfix(regex_conc)
            start_nfa, accept_nfa, trans_nfa, alphabet = postfix_a_nfa(postfix)
            dfa_states, dfa_start, dfa_accepts, dfa_trans = nfa_a_dfa(
                start_nfa, accept_nfa, trans_nfa, alphabet
            )
            texto_afn = describir_afn(start_nfa, accept_nfa, trans_nfa, alphabet)
            texto_afd = describir_afd(dfa_states, dfa_start, dfa_accepts, dfa_trans, alphabet)
            texto_gram = dfa_a_gramatica_regular(dfa_states, dfa_start, dfa_accepts, dfa_trans)

            self.txt_afn.delete("1.0", tk.END)
            self.txt_afd.delete("1.0", tk.END)
            self.txt_gr_regular.delete("1.0", tk.END)

            self.txt_afn.insert(tk.END, texto_afn)
            self.txt_afd.insert(tk.END, texto_afd)
            self.txt_gr_regular.insert(tk.END, texto_gram)

        except Exception as e:
            messagebox.showerror("Error en conversión", str(e))

    # ==================== TAB 3: REPORTE DE DESEMPEÑO Y MODO COMPARATIVO ====================
    def _build_tab_comparador(self):
        frame = self.tab_comparador

        top = tk.Frame(frame, padx=10, pady=10)
        top.pack(fill=tk.BOTH, expand=False)

        tk.Label(
            top,
            text="Reporte de Desempeño y Modo Comparativo\nComparador heurístico de lenguajes L(G1) y L(G2)",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        tk.Label(
            top,
            fg="gray"
        ).pack(anchor="w")

        middle = tk.Frame(frame, padx=10, pady=10)
        middle.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(middle)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right = tk.Frame(middle)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left, text="Gramática 1").pack(anchor="w")
        self.txt_g1 = scrolledtext.ScrolledText(left, width=40, height=12)
        self.txt_g1.insert(tk.END, "S -> b S b\nS -> b a")
        self.txt_g1.pack(fill=tk.BOTH, expand=True)

        tk.Label(right, text="Gramática 2").pack(anchor="w")
        self.txt_g2 = scrolledtext.ScrolledText(right, width=40, height=12)
        self.txt_g2.insert(tk.END, "S -> a S b | A\nS -> a a\nA -> a a")
        self.txt_g2.pack(fill=tk.BOTH, expand=True)

        bottom_top = tk.Frame(frame, padx=10, pady=5)
        bottom_top.pack(fill=tk.X)

        tk.Label(bottom_top, text="Longitud máxima de cadenas n (para comparar):").pack(side=tk.LEFT)
        self.entry_n = tk.Entry(bottom_top, width=5)
        self.entry_n.insert(0, "6")
        self.entry_n.pack(side=tk.LEFT, padx=5)

        btn = tk.Button(
            bottom_top,
            text="Comparar lenguajes L(G1) vs L(G2)",
            command=self.comparar_gramaticas_action
        )
        btn.pack(side=tk.LEFT, padx=10)

        bottom = tk.Frame(frame, padx=10, pady=10)
        bottom.pack(fill=tk.BOTH, expand=True)

        col1 = tk.Frame(bottom)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        col2 = tk.Frame(bottom)
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(col1, text="L(G1) (|w| <= n):").pack(anchor="w")
        self.txt_l1 = scrolledtext.ScrolledText(col1, width=40, height=10)
        self.txt_l1.pack(fill=tk.BOTH, expand=True)

        tk.Label(col2, text="L(G2) (|w| <= n):").pack(anchor="w")
        self.txt_l2 = scrolledtext.ScrolledText(col2, width=40, height=10)
        self.txt_l2.pack(fill=tk.BOTH, expand=True)

        tk.Label(bottom, text="Resultado de la comparación:").pack(anchor="w")
        self.lbl_comp_result = tk.Label(bottom, text="(pendiente)", fg="gray")
        self.lbl_comp_result.pack(anchor="w")

        tk.Label(bottom, text="Diferencias (G1 - G2):").pack(anchor="w")
        self.txt_diff_1_2 = scrolledtext.ScrolledText(bottom, width=100, height=4)
        self.txt_diff_1_2.pack(fill=tk.BOTH, expand=True)

        tk.Label(bottom, text="Diferencias (G2 - G1):").pack(anchor="w")
        self.txt_diff_2_1 = scrolledtext.ScrolledText(bottom, width=100, height=4)
        self.txt_diff_2_1.pack(fill=tk.BOTH, expand=True)

    def comparar_gramaticas_action(self):
        g1_text = self.txt_g1.get("1.0", tk.END).strip()
        g2_text = self.txt_g2.get("1.0", tk.END).strip()

        if not g1_text or not g2_text:
            messagebox.showwarning("Advertencia", "Ingresa ambas gramáticas.")
            return

        try:
            n = int(self.entry_n.get())
        except ValueError:
            messagebox.showerror("Error", "n debe ser un entero.")
            return

        try:
            g1 = GrammarParser.parse(g1_text)
            g2 = GrammarParser.parse(g2_text)

            L1 = generar_cadenas(g1, max_len=n)
            L2 = generar_cadenas(g2, max_len=n)

            self.txt_l1.delete("1.0", tk.END)
            self.txt_l2.delete("1.0", tk.END)
            for w in sorted(L1):
                self.txt_l1.insert(tk.END, w + "\n")
            for w in sorted(L2):
                self.txt_l2.insert(tk.END, w + "\n")

            diff_1_2 = sorted(L1 - L2)
            diff_2_1 = sorted(L2 - L1)

            self.txt_diff_1_2.delete("1.0", tk.END)
            self.txt_diff_2_1.delete("1.0", tk.END)
            self.txt_diff_1_2.insert(tk.END, ", ".join(diff_1_2) if diff_1_2 else "(vacío)")
            self.txt_diff_2_1.insert(tk.END, ", ".join(diff_2_1) if diff_2_1 else "(vacío)")

            if not diff_1_2 and not diff_2_1:
                self.lbl_comp_result.config(
                    text="Aproximadamente equivalentes para |w| <= n.",
                    fg="darkgreen"
                )
            else:
                self.lbl_comp_result.config(
                    text="No equivalentes (se encontraron diferencias para |w| <= n).",
                    fg="darkred"
                )

        except Exception as e:
            messagebox.showerror("Error al analizar gramáticas", str(e))

    # ==================== TAB 4: MODO TUTOR INTERACTIVO (QUIZ) ====================
    def _build_tab_tutor(self):
        frame = self.tab_tutor

        top = tk.Frame(frame, padx=10, pady=10)
        top.pack(fill=tk.BOTH, expand=False)

        tk.Label(
            top,
            text="Modo Tutor Interactivo (Quiz)",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        tk.Label(
            top,
            text="Clasifica la siguiente gramática según la Jerarquía de Chomsky (tipo más restrictivo)."
        ).pack(anchor="w")

        middle = tk.Frame(frame, padx=10, pady=10)
        middle.pack(fill=tk.BOTH, expand=True)

        tk.Label(middle, text="Gramática del ejercicio:").pack(anchor="w")
        self.txt_tutor_grammar = scrolledtext.ScrolledText(
            middle, width=60, height=10
        )
        self.txt_tutor_grammar.pack(fill=tk.BOTH, expand=True)

        opciones = [
            "Tipo 3 – Regular",
            "Tipo 2 – Libre de Contexto",
            "Tipo 1 – Sensible al Contexto",
            "Tipo 0 – Recursivamente enumerable",
        ]
        self.tipo_var = tk.StringVar(value=opciones[1])

        tk.Label(middle, text="¿A qué tipo (más restrictivo) pertenece?").pack(anchor="w", pady=(8, 0))
        self.combo_tipos = ttk.Combobox(
            middle,
            textvariable=self.tipo_var,
            values=opciones,
            state="readonly",
            width=40
        )
        self.combo_tipos.pack(anchor="w")

        btns = tk.Frame(middle)
        btns.pack(anchor="w", pady=8)

        tk.Button(btns, text="Revisar Respuesta", command=self.revisar_tutor_action).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Siguiente Pregunta", command=self.siguiente_pregunta_tutor).pack(side=tk.LEFT, padx=5)

        self.lbl_tutor_feedback = tk.Label(middle, text="(pendiente)", fg="gray")
        self.lbl_tutor_feedback.pack(anchor="w", pady=(5, 0))

        self.txt_tutor_expl = scrolledtext.ScrolledText(
            middle, width=70, height=10
        )
        self.txt_tutor_expl.pack(fill=tk.BOTH, expand=True)

        self.siguiente_pregunta_tutor(init=True)

    def _get_current_question(self):
        desc, gr = self.sample_grammars[self.idx_pregunta]
        return desc, gr

    def siguiente_pregunta_tutor(self, init=False):
        if not init:
            self.idx_pregunta = (self.idx_pregunta + 1) % len(self.sample_grammars)

        desc, gr = self._get_current_question()
        self.txt_tutor_grammar.delete("1.0", tk.END)
        self.txt_tutor_grammar.insert(tk.END, f"# {desc}\n")
        for p in gr.productions:
            rhs_display = p.rhs if p.rhs != "" else EPS
            self.txt_tutor_grammar.insert(tk.END, f"{p.lhs} -> {rhs_display}\n")

        self.lbl_tutor_feedback.config(text="(pendiente)", fg="gray")
        self.txt_tutor_expl.delete("1.0", tk.END)

    def revisar_tutor_action(self):
        desc, gr = self._get_current_question()
        result = classify_grammar(gr)

        mapa_tipo = {
            "Tipo 3 – Regular": 3,
            "Tipo 2 – Libre de Contexto": 2,
            "Tipo 1 – Sensible al Contexto": 1,
            "Tipo 0 – Recursivamente enumerable": 0,
        }

        eleccion = self.tipo_var.get()
        tipo_usuario = mapa_tipo[eleccion]
        tipo_real = result.grammar_type

        self.txt_tutor_expl.delete("1.0", tk.END)
        for line in result.explanation:
            self.txt_tutor_expl.insert(tk.END, line + "\n")

        if tipo_usuario == tipo_real:
            self.lbl_tutor_feedback.config(
                text=f"✔ Correcto. Es {result.label}.",
                fg="darkgreen"
            )
        else:
            self.lbl_tutor_feedback.config(
                text=f"✘ Incorrecto. La clasificación correcta es: {result.label}.",
                fg="darkred"
            )

    # ==================== TAB 5: GENERADOR AUTOMÁTICO DE EJEMPLOS ====================
    def _build_tab_generador(self):
        frame = self.tab_generador

        top = tk.Frame(frame, padx=10, pady=10)
        top.pack(fill=tk.BOTH, expand=False)

        tk.Label(
            top,
            text="Generador Automático de Ejemplos",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        tk.Label(
            top,
            text="Genera gramáticas aleatorias de un tipo específico (basado en la lista interna de ejemplos)."
        ).pack(anchor="w")

        middle = tk.Frame(frame, padx=10, pady=10)
        middle.pack(fill=tk.BOTH, expand=True)

        tk.Label(middle, text="Selecciona el tipo de gramática a generar:").pack(anchor="w")

        self.gen_tipo_var = tk.StringVar(value="Tipo 2")

        opciones = ["Tipo 3", "Tipo 2", "Tipo 1", "Tipo 0"]
        self.combo_gen = ttk.Combobox(
            middle,
            textvariable=self.gen_tipo_var,
            values=opciones,
            state="readonly",
            width=10
        )
        self.combo_gen.pack(anchor="w", pady=(0, 5))

        tk.Button(
            middle,
            text="Generar Gramática Aleatoria",
            command=self.generar_gramatica_ejemplo_action
        ).pack(anchor="w", pady=5)

        tk.Label(middle, text="Gramática generada:").pack(anchor="w", pady=(10, 0))
        self.txt_generador = scrolledtext.ScrolledText(
            middle, width=70, height=15
        )
        self.txt_generador.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            middle,
            fg="gray"
        ).pack(anchor="w", pady=(5, 0))

    def generar_gramatica_ejemplo_action(self):
        tipo = self.gen_tipo_var.get()
        indices_por_tipo = {
            "Tipo 3": [0],
            "Tipo 2": [1],
            "Tipo 1": [2],
            "Tipo 0": [3],
        }
        indices = indices_por_tipo[tipo]
        idx = random.choice(indices)

        desc, gr = self.sample_grammars[idx]
        self.txt_generador.delete("1.0", tk.END)
        self.txt_generador.insert(tk.END, f"# {desc}\n")
        for p in gr.productions:
            rhs_display = p.rhs if p.rhs != "" else EPS
            self.txt_generador.insert(tk.END, f"{p.lhs} -> {rhs_display}\n")


if __name__ == "__main__":
    app = ChomskyApp()
    app.mainloop()
