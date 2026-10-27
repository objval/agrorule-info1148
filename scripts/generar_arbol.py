"""Genera la imagen del AST de un programa de ejemplo con Graphviz."""

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from agrorule import analizar  # noqa: E402

SALIDA = RAIZ.parent / "informe" / "figuras"

PROGRAMA = """WHEN temperatura > 28 AND humedad < 40 THEN abrir_ventilador(80); avisar("calor") END"""


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    arbol = analizar(PROGRAMA)
    dot = SALIDA / "ast.dot"
    dot.write_text(arbol.a_dot(), encoding="utf-8")
    subprocess.run(
        ["dot", "-Tpng", "-Gdpi=150", str(dot), "-o", str(SALIDA / "ast.png")],
        check=True,
    )
    (SALIDA / "ast.txt").write_text(arbol.dibujar(), encoding="utf-8")
    print("AST generado en", SALIDA / "ast.png")


if __name__ == "__main__":
    main()
