"""
Music 10 - Ponto de Entrada Alternativo (app.py)
Permite iniciar a aplicação via `streamlit run app.py` ou `streamlit run main_app.py`.
"""

import os
import runpy

if __name__ == "__main__":
    main_path = os.path.join(os.path.dirname(__file__), "main_app.py")
    runpy.run_path(main_path, run_name="__main__")
else:
    main_path = os.path.join(os.path.dirname(__file__), "main_app.py")
    runpy.run_path(main_path)
