# tutor.py
from typing import List, Tuple
from examples.sample_grammars import get_sample_grammars
from grammar_parser import Grammar
from classifier import classify_grammar, ClassificationResult


def get_quiz_questions() -> List[Tuple[str, Grammar, ClassificationResult]]:
    """
    Genera una lista de preguntas para el modo tutor.
    Cada elemento: (descripcion, grammar, resultado_real)
    """
    samples = get_sample_grammars()
    questions = []

    for desc, gr in samples:
        result = classify_grammar(gr)
        questions.append((desc, gr, result))

    return questions
