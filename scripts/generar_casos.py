"""Genera 25 casos ejecutados con resultado esperado, obtenido y observación.

Cada entrada se analiza y la generación falla si su aceptación difiere de la
expectativa. Los detalles de errores se obtienen de la excepción real.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from agrorule import analizar  # noqa: E402
from agrorule.errors import ErrorLexico, ErrorSintactico  # noqa: E402

DESTINO = (RAIZ / "docs/c2/tablas" if (RAIZ / "docs/c2").exists()
           else RAIZ.parent / "informe/tablas")
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


OBS_VALIDOS = [
    "Regla mínima", "AND en la condición", "OR y dos acciones", "NOT con paréntesis",
    "Dos acciones", "Dos reglas", "Argumento booleano", "Negación repetida",
    "Agrupación anidada", "Decimales y texto",
]
OBS_INVALIDOS = [
    "Falta THEN", "Falta END", "Falta el valor", "Falta una acción",
    "Falta separador", "Falta condición", "Falta cerrar grupo",
    "Símbolo no admitido", "Falta argumento", "Falta operador",
]
OBS_LIMITE = [
    "Lista vacía admitida", "Comentario sin reglas", "NOT repetido",
    "Acción sin paréntesis", "Cuatro acciones",
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
        return True, f"aceptada, {cantidad} {'regla' if cantidad == 1 else 'reglas'}"
    except (ErrorSintactico, ErrorLexico) as error:
        tipo = "léxico" if isinstance(error, ErrorLexico) else "sintáctico"
        return False, f"rechazada, {tipo} L{error.linea}:C{error.columna}"


def fila(numero, programa, esperado, observacion):
    entrada = escapar(programa) if programa else "(vacío)"
    aceptada, obtenido = resultado(programa)
    if aceptada != esperado:
        raise AssertionError(f"caso {numero}: se esperaba {esperado}, se obtuvo {obtenido}")
    esperado_texto = "acepta" if esperado else "rechaza"
    return (f"{numero}&\\texttt{{{entrada}}}&{esperado_texto}&{escapar(obtenido)}"
            f"&{escapar(observacion)}" + FILA)


def main():
    assert (len(VALIDOS), len(INVALIDOS), len(LIMITE)) == (10, 10, 5)
    lineas = [
        r"{\footnotesize\setlength{\tabcolsep}{3pt}\begin{longtable}{L{0.55cm}L{6.5cm}L{1.6cm}L{3.2cm}L{3.7cm}}",
        r"\caption{Casos de prueba: expectativa y resultado observado al ejecutar el analizador.}\label{tab:casos}" + FILA,
        r"\toprule\textbf{N}&\textbf{Entrada}&\textbf{Esperado}&\textbf{Obtenido}&\textbf{Observación}" + FILA + r"\midrule\endfirsthead",
        r"\toprule\textbf{N}&\textbf{Entrada}&\textbf{Esperado}&\textbf{Obtenido}&\textbf{Observación}" + FILA + r"\midrule\endhead",
        r"\multicolumn{5}{l}{\textbf{Válidas}}" + FILA + r"\midrule",
    ]
    for numero, (programa, observacion) in enumerate(zip(VALIDOS, OBS_VALIDOS, strict=True), 1):
        lineas.append(fila(numero, programa, True, observacion))
    lineas.append(r"\midrule\multicolumn{5}{l}{\textbf{Inválidas}}" + FILA + r"\midrule")
    for numero, (programa, observacion) in enumerate(zip(INVALIDOS, OBS_INVALIDOS, strict=True), 11):
        lineas.append(fila(numero, programa, False, observacion))
    lineas.append(r"\midrule\multicolumn{5}{l}{\textbf{Casos límite}}" + FILA + r"\midrule")
    for numero, (programa, observacion) in enumerate(zip(LIMITE, OBS_LIMITE, strict=True), 21):
        lineas.append(fila(numero, programa, True, observacion))
    lineas.append(r"\bottomrule\end{longtable}}")

    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / "casos.tex").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("tabla de casos generada con", len(VALIDOS) + len(INVALIDOS) + len(LIMITE), "casos")


if __name__ == "__main__":
    main()
