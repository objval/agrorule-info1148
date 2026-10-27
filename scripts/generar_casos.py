"""Genera la tabla de casos de prueba del informe ejecutando el analizador.

Las 25 entradas se corren de verdad y la tabla muestra el resultado obtenido, no
el que se esperaba escribir a mano. Si alguna cambia de comportamiento, la tabla
del informe cambia con ella.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from agrorule import analizar  # noqa: E402
from agrorule.errors import ErrorLexico, ErrorSintactico  # noqa: E402

DESTINO = RAIZ.parent / "informe" / "tablas"

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
    ("", "programa vacío, cero reglas"),
    ("# solo comentarios", "comentarios sin reglas"),
    ("WHEN NOT NOT NOT temperatura > 5 THEN calentar END", "negaciones anidadas"),
    ("WHEN temperatura > 5 THEN avisar END", "acción sin argumentos"),
    ("WHEN temperatura > 5 THEN regar(1); regar(2); regar(3); cerrar_techo END", "cuatro acciones"),
]


def escapar(texto):
    for viejo, nuevo in [("\\", "\\textbackslash{}"), ("_", "\\_"), ("#", "\\#"),
                         ("&", "\\&"), ("%", "\\%"), ("{", "\\{"), ("}", "\\}"),
                         ('"', "\\textquotedbl{}"), ("^", "\\^{}"), ("~", "\\textasciitilde{}")]:
        texto = texto.replace(viejo, nuevo)
    return texto


def resultado(programa):
    try:
        arbol = analizar(programa)
        return f"válida, {len(arbol.reglas)} regla(s)"
    except (ErrorSintactico, ErrorLexico) as error:
        mensaje = str(error)
        if ":" in mensaje:
            mensaje = mensaje.split(":", 1)[1].strip()
        return "inválida: " + mensaje[:95]


def filas(casos, desde):
    lineas = []
    for indice, programa in enumerate(casos, desde):
        entrada = escapar(programa) if programa else "(vacío)"
        lineas.append(f"{indice}&\\texttt{{{entrada}}}&{escapar(resultado(programa))}\\\\\\")
    return lineas


def main():
    lineas = [
        "{\\footnotesize\\begin{longtable}{L{0.7cm}L{8.4cm}L{7.4cm}}",
        "\\caption{Casos de prueba ejecutados sobre el analizador.}\\label{tab:casos}\\\\",
        "\\toprule\\textbf{N}&\\textbf{Entrada}&\\textbf{Resultado obtenido}\\\\\\midrule\\endfirsthead",
        "\\toprule\\textbf{N}&\\textbf{Entrada}&\\textbf{Resultado obtenido}\\\\\\midrule\\endhead",
    ]
    lineas.append("\\multicolumn{3}{l}{\\textbf{Válidas}}\\\\\\midrule")
    lineas += filas(VALIDOS, 1)
    lineas.append("\\midrule\\multicolumn{3}{l}{\\textbf{Inválidas}}\\\\\\midrule")
    lineas += filas(INVALIDOS, 11)
    lineas.append("\\midrule\\multicolumn{3}{l}{\\textbf{Casos límite}}\\\\\\midrule")
    for indice, (programa, nota) in enumerate(LIMITE, 21):
        entrada = escapar(programa) if programa else "(vacío)"
        lineas.append(f"{indice}&\\texttt{{{entrada}}}&{escapar(resultado(programa))}\\\\\\")
    lineas += ["\\bottomrule\\end{longtable}}", ""]
    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / "casos.tex").write_text("\n".join(lineas), encoding="utf-8")
    print("tabla de casos generada con", len(VALIDOS) + len(INVALIDOS) + len(LIMITE), "casos")


if __name__ == "__main__":
    main()
