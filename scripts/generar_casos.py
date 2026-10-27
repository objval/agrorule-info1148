"""Genera la tabla de casos de prueba del informe ejecutando el analizador.

Las 25 entradas se corren de verdad y la tabla muestra el resultado obtenido, no
el esperado escrito a mano. Si el comportamiento cambia, la tabla cambia con el.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from agrorule import analizar  # noqa: E402
from agrorule.errors import ErrorLexico, ErrorSintactico  # noqa: E402

DESTINO = RAIZ.parent / "informe" / "tablas"
FILA = r"\\"

VALIDOS = [
    "WHEN temperatura > 28 THEN abrir_ventilador END",
    "WHEN humedad < 30 AND temperatura > 25 THEN regar(20) END",
    'WHEN suelo == seco OR lluvia == FALSE THEN regar(15); avisar("riego activo") END',
    "WHEN NOT (temperatura > 30) THEN cerrar_techo END",
    "WHEN luz >= 800 THEN bajar_malla(50); encender_extractor END",
    "WHEN temperatura > 28 THEN abrir_ventilador END WHEN humedad < 30 THEN regar(20) END",
    "WHEN CO2 > 900 AND humedad > 80 THEN ventilar(TRUE) END",
    "WHEN NOT NOT lluvia == TRUE THEN cerrar_techo END",
    "WHEN ((temperatura > 28)) THEN abrir_ventilador(75) END",
    'WHEN ph >= 6.5 AND ph <= 7.5 THEN fertirriego(1.5, "nitrato") END',
]

INVALIDOS = [
    "WHEN temperatura > 28 abrir_ventilador END",
    "WHEN temperatura > 28 THEN abrir_ventilador",
    "WHEN temperatura > THEN abrir_ventilador END",
    "WHEN temperatura > 28 THEN END",
    "WHEN temperatura > 28 THEN regar(20) abrir_ventilador END",
    "WHEN THEN regar(20) END",
    "WHEN (temperatura > 28 THEN regar(20) END",
    "WHEN temperatura > 28 THEN regar(20) END @",
    "WHEN temperatura > 28 THEN regar(20, ) END",
    "WHEN temperatura 28 THEN regar(20) END",
]

LIMITE = [
    "",
    "# solo comentarios",
    "WHEN NOT NOT NOT temperatura > 5 THEN calentar END",
    "WHEN temperatura > 5 THEN avisar END",
    "WHEN temperatura > 5 THEN regar(1); regar(2); regar(3); cerrar_techo END",
]


def escapar(texto):
    """Deja el texto apto para \\texttt dentro de una celda de tabla."""
    reemplazos = [
        ("\\", r"\textbackslash{}"),
        ("_", r"\_"),
        ("#", r"\#"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("{", r"\{"),
        ("}", r"\}"),
        ('"', r"\textquotedbl{}"),
        ("^", r"\^{}"),
        ("~", r"\textasciitilde{}"),
    ]
    for viejo, nuevo in reemplazos:
        texto = texto.replace(viejo, nuevo)
    return texto


def resultado(programa):
    try:
        arbol = analizar(programa)
        cantidad = len(arbol.reglas)
        return f"válida, {cantidad} {'regla' if cantidad == 1 else 'reglas'}"
    except (ErrorSintactico, ErrorLexico) as error:
        mensaje = str(error)
        if "):" in mensaje:
            mensaje = mensaje.split("):", 1)[1].strip()
        return "inválida: " + mensaje


def fila(numero, programa):
    entrada = escapar(programa) if programa else "(vacío)"
    return f"{numero}&\\texttt{{{entrada}}}&{escapar(resultado(programa))}" + FILA


def main():
    lineas = [
        r"{\footnotesize\setlength{\tabcolsep}{4pt}\begin{longtable}{L{0.7cm}L{7.7cm}L{7.1cm}}",
        r"\caption{Casos de prueba ejecutados sobre el analizador.}\label{tab:casos}" + FILA,
        r"\toprule\textbf{N}&\textbf{Entrada}&\textbf{Resultado obtenido}" + FILA + r"\midrule\endfirsthead",
        r"\toprule\textbf{N}&\textbf{Entrada}&\textbf{Resultado obtenido}" + FILA + r"\midrule\endhead",
        r"\multicolumn{3}{l}{\textbf{Válidas}}" + FILA + r"\midrule",
    ]
    for numero, programa in enumerate(VALIDOS, 1):
        lineas.append(fila(numero, programa))
    lineas.append(r"\midrule\multicolumn{3}{l}{\textbf{Inválidas}}" + FILA + r"\midrule")
    for numero, programa in enumerate(INVALIDOS, 11):
        lineas.append(fila(numero, programa))
    lineas.append(r"\midrule\multicolumn{3}{l}{\textbf{Casos límite}}" + FILA + r"\midrule")
    for numero, programa in enumerate(LIMITE, 21):
        lineas.append(fila(numero, programa))
    lineas.append(r"\bottomrule\end{longtable}}")

    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / "casos.tex").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("tabla de casos generada con", len(VALIDOS) + len(INVALIDOS) + len(LIMITE), "casos")


if __name__ == "__main__":
    main()
