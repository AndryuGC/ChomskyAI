# main.py
import streamlit as st

from grammar_parser import GrammarParser
from classifier import classify_grammar
from visualizer import grammar_to_dot
from examples.sample_grammars import get_sample_grammars
from tutor import get_quiz_questions


def page_classifier():
    st.header("🔎 Chomsky Classifier AI – Clasificador de Gramáticas")

    st.markdown(
        "Ingresa las reglas de la gramática, una por línea, usando `->` o `→`.\n\n"
        "**Ejemplo:**\n"
        "`S -> aA`\n\n"
        "`A -> b`"
    )

    default_grammar = "S -> aA\nA -> b"
    text = st.text_area("Gramática de entrada", value=default_grammar, height=200)

    if st.button("Clasificar gramática"):
        try:
            grammar = GrammarParser.parse(text)
            result = classify_grammar(grammar)

            st.success(f"Resultado: **{result.label}**")
            st.subheader("Explicación paso a paso")
            for line in result.explanation:
                st.markdown(line)

            st.subheader("Producciones detectadas")
            for p in grammar.productions:
                rhs_display = p.rhs if p.rhs != "" else "ε"
                st.code(f"{p.lhs} -> {rhs_display}", language="text")

            # Visualización DOT básica
            st.subheader("Diagrama (Graphviz DOT)")
            dot_code = grammar_to_dot(grammar)
            st.code(dot_code, language="dot")
            st.info(
                "Puedes copiar este código DOT y usar Graphviz "
                "(por ejemplo, la herramienta online `dreampuf.github.io/GraphvizOnline`) "
                "para generar un diagrama."
            )

        except Exception as e:
            st.error(f"Error al analizar la gramática: {e}")


def page_examples():
    st.header("📘 Ejemplos de Gramáticas por Tipo")
    examples = get_sample_grammars()

    for desc, gr in examples:
        with st.expander(desc):
            for p in gr.productions:
                rhs_display = p.rhs if p.rhs != "" else "ε"
                st.code(f"{p.lhs} -> {rhs_display}", language="text")


def page_tutor():
    st.header("🧠 Modo Tutor – Quiz de Jerarquía de Chomsky (versión básica)")

    questions = get_quiz_questions()
    # Para que no sea muy largo, tomamos una sola pregunta por ejecución
    if not questions:
        st.warning("No hay preguntas disponibles.")
        return

    # Elegir pregunta por índice (puedes cambiar a random si quieres)
    idx = st.number_input(
        "Selecciona índice de pregunta",
        min_value=0,
        max_value=len(questions) - 1,
        value=0,
        step=1,
    )

    desc, grammar, result_real = questions[idx]

    st.subheader("Gramática a clasificar")
    st.write(desc)
    for p in grammar.productions:
        rhs_display = p.rhs if p.rhs != "" else "ε"
        st.code(f"{p.lhs} -> {rhs_display}", language="text")

    st.markdown("¿Qué tipo crees que es esta gramática?")

    opciones = {
        "Tipo 3 – Regular": 3,
        "Tipo 2 – Libre de Contexto": 2,
        "Tipo 1 – Sensible al Contexto": 1,
        "Tipo 0 – Recursivamente enumerable": 0,
    }

    respuesta_usuario = st.radio("Tu respuesta:", list(opciones.keys()))

    if st.button("Comprobar respuesta"):
        tipo_usuario = opciones[respuesta_usuario]
        tipo_real = result_real.grammar_type

        if tipo_usuario == tipo_real:
            st.success("✅ ¡Correcto!")
        else:
            st.error("❌ Incorrecto.")

        st.markdown(
            f"**Clasificación correcta:** {result_real.label}"
        )

        st.subheader("Explicación del agente")
        for line in result_real.explanation:
            st.markdown(line)


def main():
    st.set_page_config(
        page_title="Chomsky Classifier AI",
        page_icon="📚",
        layout="wide",
    )

    st.sidebar.title("Chomsky Classifier AI")
    st.sidebar.markdown(
        "Agente para clasificar gramáticas por la Jerarquía de Chomsky "
        "(Tipo 0, 1, 2, 3)."
    )

    page = st.sidebar.radio(
        "Navegación",
        options=["Clasificador", "Ejemplos", "Tutor"],
    )

    if page == "Clasificador":
        page_classifier()
    elif page == "Ejemplos":
        page_examples()
    else:
        page_tutor()


if __name__ == "__main__":
    main()
