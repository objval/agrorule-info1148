"""Genera las tablas LaTeX del informe a partir de la gramatica.

Todo lo que aparece en el informe se calcula aqui: FIRST, FOLLOW, tabla LL(1),
lista de producciones y conteos. Si la gramatica cambia, el informe se regenera
con una corrida y no queda desactualizado.
"""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from agrorule.grammar import (  # noqa: E402
    CUERPO_POR_ID,
    EPSILON,
    NO_TERMINALES,
    PRODUCCIONES,
    SIMBOLO_INICIAL,
    TERMINALES,
    construir_tabla,
    es_ll1,
)

DESTINO = RAIZ.parent / "informe" / "tablas"
DESTINO.mkdir(parents=True, exist_ok=True)

NOMBRE_COLUMNA = {
    "WHEN": "WHEN",
    "THEN": "THEN",
    "AND": "AND",
    "OR": "OR",
    "NOT": "NOT",
    "END": "END",
    "TRUE": "TRUE",
    "FALSE": "FALSE",
    "OP_REL": "op",
    "LPAREN": "(",
    "RPAREN": ")",
    "SEMI": ";",
    "COMMA": ",",
    "NUM": "num",
    "IDENT": "id",
    "CADENA": "txt",
    "EOF": "$",
}

NOMBRE_FILA = {
    "programa": "programa",
    "lista_reglas": "lista\\_reglas",
    "regla": "regla",
    "cond": "cond",
    "disy": "disy",
    "disy_p": "disy'",
    "conj": "conj",
    "conj_p": "conj'",
    "neg": "neg",
    "prim": "prim",
    "comp": "comp",
    "term": "term",
    "acciones": "acciones",
    "acciones_p": "acciones'",
    "accion": "accion",
    "llamada": "llamada",
    "args": "args",
    "args_p": "args'",
    "arg": "arg",
}


def escapar(texto):
    return texto.replace("_", "\\_").replace("#", "\\#").replace("&", "\\&").replace("%", "\\%")


def lista_latex(conjunto):
    orden = [t for t in TERMINALES if t in conjunto]
    if EPSILON in conjunto:
        orden.append(EPSILON)
    return ", ".join(NOMBRE_COLUMNA.get(t, t) if t != EPSILON else "$\\varepsilon$" for t in orden)


def tabla_producciones():
    lineas = [
        "{\\small\\begin{longtable}{L{1.1cm}L{12.0cm}}",
        "\\caption{Producciones de la gramática de AgroRule.}\\label{tab:producciones}\\\\",
        "\\toprule\\textbf{ID}&\\textbf{Producción}\\\\\\midrule\\endfirsthead",
        "\\toprule\\textbf{ID}&\\textbf{Producción}\\\\\\midrule\\endhead",
    ]
    for pid, cabeza, cuerpo in PRODUCCIONES:
        if cuerpo:
            rhs = " ".join(escapar(s) if s not in NO_TERMINALES else NOMBRE_FILA.get(s, s) for s in cuerpo)
        else:
            rhs = "$\\varepsilon$"
        lineas.append(f"{pid}&{NOMBRE_FILA.get(cabeza, cabeza)} $\\rightarrow$ {rhs}\\\\\\")
    lineas += ["\\bottomrule\\end{longtable}}", ""]
    return "\n".join(lineas)


def tabla_first_follow(first, follow):
    lineas = [
        "{\\small\\begin{longtable}{L{3.0cm}L{6.6cm}L{6.2cm}}",
        "\\caption{Conjuntos FIRST y FOLLOW por no terminal.}\\label{tab:firstfollow}\\\\",
        "\\toprule\\textbf{No terminal}&\\textbf{FIRST}&\\textbf{FOLLOW}\\\\\\midrule\\endfirsthead",
        "\\toprule\\textbf{No terminal}&\\textbf{FIRST}&\\textbf{FOLLOW}\\\\\\midrule\\endhead",
    ]
    for no_terminal in NO_TERMINALES:
        lineas.append(
            f"{NOMBRE_FILA.get(no_terminal, no_terminal)}&{{{lista_latex(first[no_terminal])}}}&{{{lista_latex(follow[no_terminal])}}}\\\\\\"
        )
    lineas += ["\\bottomrule\\end{longtable}}", ""]
    return "\n".join(lineas)


def tabla_ll1(tabla):
    columnas = "".join("C{1.05cm}" for _ in TERMINALES)
    cabecera = "&".join(f"\\rotatebox{{90}}{{\\scriptsize {NOMBRE_COLUMNA[t]}}}" for t in TERMINALES)
    lineas = [
        "{\\scriptsize\\begin{longtable}{L{2.0cm}" + columnas + "}",
        "\\caption{Tabla predictiva LL(1). Cada celda indica la producción que se aplica.}\\label{tab:ll1}\\\\\\",
        "\\toprule\\textbf{No terminal}&" + cabecera + "\\\\\\midrule\\endfirsthead",
        "\\toprule\\textbf{No terminal}&" + cabecera + "\\\\\\midrule\\endhead",
    ]
    for no_terminal in NO_TERMINALES:
        celdas = [tabla[no_terminal].get(t, "") for t in TERMINALES]
        lineas.append(NOMBRE_FILA.get(no_terminal, no_terminal) + "&" + "&".join(celdas) + "\\\\")
    lineas += ["\\bottomrule\\end{longtable}}", ""]
    return "\n".join(lineas)


def main():
    first, follow, tabla, conflictos = construir_tabla()
    valida, conflictos = es_ll1()

    (DESTINO / "producciones.tex").write_text(tabla_producciones(), encoding="utf-8")
    (DESTINO / "first_follow.tex").write_text(tabla_first_follow(first, follow), encoding="utf-8")
    (DESTINO / "tabla_ll1.tex").write_text(tabla_ll1(tabla), encoding="utf-8")

    resumen = {
        "producciones": len(PRODUCCIONES),
        "no_terminales": len(NO_TERMINALES),
        "terminales": len(TERMINALES),
        "simbolo_inicial": SIMBOLO_INICIAL,
        "es_ll1": valida,
        "conflictos": len(conflictos),
        "celdas_tabla": sum(len(fila) for fila in tabla.values()),
    }
    (DESTINO / "resumen.json").write_text(json.dumps(resumen, indent=2), encoding="utf-8")
    print(json.dumps(resumen, indent=2))


if __name__ == "__main__":
    main()
