🧠 Chomsky Classifier AI

Aplicación interactiva en Python diseñada para analizar, clasificar y transformar gramáticas formales utilizando la Jerarquía de Chomsky.
Incluye una interfaz gráfica completa, conversores automáticos entre representaciones y herramientas de práctica.

🚀 Características Principales
📘 1. Modo Explicativo Inteligente

Clasifica gramáticas en Tipo 0, 1, 2 o 3.

Explicación paso a paso del análisis.

Verificación de pertenencia de cadenas.

Generación de reportes PDF.

🔁 2. Conversores entre Representaciones

Convierte automáticamente:

Expresión Regular → AFN (Thompson)

AFN → AFD (Subconjuntos)

AFD → Gramática Regular

Muestra estados, transiciones y producciones generadas.

📊 3. Reporte de Desempeño y Comparador

Compara dos gramáticas generando su lenguaje hasta longitud n.

Identifica coincidencias y diferencias.

Determina si los lenguajes parecen equivalentes.

🎓 4. Modo Tutor Interactivo

Presenta gramáticas aleatorias.

El usuario debe clasificarlas.

Retroalimentación inmediata y explicación.

🧬 5. Generador Automático de Gramáticas

Genera gramáticas aleatorias de Tipo 0, 1, 2 o 3.

Útil para estudiar o practicar.

🛠️ Tecnologías Utilizadas

🐍 Python 3.14

🪟 Tkinter — Interfaz gráfica

📝 ReportLab — Generación de PDF

🧩 Construcción de Thompson (AFN)

🔄 Método de los Subconjuntos (AFN → AFD)

📐 Conversión AFD → Gramática Regular


▶️ Cómo Ejecutarlo
1. Crear entorno virtual
python -m venv .venv

2. Activarlo

Windows:

.\.venv\Scripts\activate

3. Instalar dependencias
pip install reportlab

4. Ejecutar el programa
python main_tk.py
