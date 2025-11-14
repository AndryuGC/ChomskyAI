Chomsky Classifier AI
Andry González Cantoral - 2000924

Herramienta desarrollada para analizar, clasificar y transformar gramáticas formales según la Jerarquía de Chomsky. Incluye una interfaz gráfica construida en Python (Tkinter) y diversos módulos para trabajar con autómatas, expresiones regulares y gramáticas regulares.

Características
1. Modo Explicativo Inteligente

Clasifica una gramática en Tipo 0, 1, 2 o 3.

Genera una explicación paso a paso justificando la clasificación.

Permite evaluar si una cadena puede ser generada por la gramática.

Opción para generar un reporte PDF.

2. Conversores entre Representaciones

Convierte automáticamente:

Expresión Regular → AFN (Construcción de Thompson)

AFN → AFD (Método de los Subconjuntos)

AFD → Gramática Regular Tipo 3

Muestra todos los estados, transiciones y producciones generadas.

3. Reporte de Desempeño y Modo Comparativo

Compara dos gramáticas generando sus lenguajes hasta una longitud n.

Identifica cadenas comunes y diferencias entre los lenguajes.

Determina si parecen equivalentes de forma heurística.

4. Modo Tutor Interactivo

Muestra una gramática aleatoria.

El usuario debe clasificarla.

El sistema evalúa la respuesta y explica el porqué.

5. Generador Automático de Gramáticas

Genera gramáticas aleatorias de cualquier tipo (0, 1, 2 o 3).

Útil para ejercicios, práctica y validación.

Tecnologías Utilizadas

Python 3.14

Tkinter (Interfaz gráfica)

Reportlab (Generación de PDF)

Construcción de Thompson (AFN)

Método de Subconjuntos (AFN → AFD)

Conversión AFD → Gramática Regular

Estructura del Proyecto

main_tk.py
Contiene la interfaz gráfica y la integración de todos los módulos.

grammar_parser.py
Analiza el texto de entrada y construye la estructura formal de una gramática.

classifier.py
Implementa la lógica de clasificación según la Jerarquía de Chomsky.

examples/sample_grammars.py
Gramáticas de ejemplo utilizadas en el modo tutor y el generador automático.

Ejecución

Crear y activar el entorno virtual

python -m venv .venv
.\.venv\Scripts\activate


Instalar dependencias

pip install reportlab


Ejecutar la aplicación

python main_tk.py
