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

FILA = r"\\"
EPS = r"$\varepsilon$"
FLECHA = r"$\rightarrow$"
DOLAR = r"\$"

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
    "EOF": DOLAR,
}

NOMBRE_FILA = {
    "programa": "programa",
    "lista_reglas": r"lista\_reglas",
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
    return (texto.replace("_", r"\_").replace("#", r"\#")
            .replace("&", r"\&").replace("%", r"\%"))


def nombre_terminal(terminal):
    if terminal == "EOF":
        return DOLAR
    return NOMBRE_COLUMNA.get(terminal, escapar(terminal))


def lista_latex(conjunto):
    orden = [t for t in TERMINALES if t in conjunto]
    if EPSILON in conjunto:
        orden.append(EPSILON)
    partes = [EPS if t == EPSILON else nombre_terminal(t) for t in orden]
    return ", ".join(partes)


def tabla_producciones():
    lineas = [
        r"{\small\begin{longtable}{L{1.1cm}L{12.2cm}}",
        r"\caption{Producciones de la gramática de AgroRule.}\label{tab:producciones}" + FILA,
        r"\toprule\textbf{ID}&\textbf{Producción}" + FILA + r"\midrule\endfirsthead",
        r"\toprule\textbf{ID}&\textbf{Producción}" + FILA + r"\midrule\endhead",
    ]
    for pid, cabeza, cuerpo in PRODUCCIONES:
        if cuerpo:
            rhs = " ".join(NOMBRE_FILA.get(s, escapar(s)) if s in NO_TERMINALES else escapar(s)
                           for s in cuerpo)
        else:
            rhs = EPS
        lineas.append(f"{pid}&{NOMBRE_FILA.get(cabeza, cabeza)} {FLECHA} {rhs}" + FILA)
    lineas.append(r"\bottomrule\end{longtable}}")
    return "\n".join(lineas) + "\n"


def tabla_first_follow(first, follow):
    lineas = [
        r"{\small\setlength{\tabcolsep}{4pt}\begin{longtable}{L{2.8cm}L{6.3cm}L{5.9cm}}",
        r"\caption{Conjuntos FIRST y FOLLOW por no terminal.}\label{tab:firstfollow}" + FILA,
        r"\toprule\textbf{No terminal}&\textbf{FIRST}&\textbf{FOLLOW}" + FILA + r"\midrule\endfirsthead",
        r"\toprule\textbf{No terminal}&\textbf{FIRST}&\textbf{FOLLOW}" + FILA + r"\midrule\endhead",
    ]
    for no_terminal in NO_TERMINALES:
        lineas.append(
            f"{NOMBRE_FILA.get(no_terminal, no_terminal)}&{{{lista_latex(first[no_terminal])}}}"
            f"&{{{lista_latex(follow[no_terminal])}}}" + FILA
        )
    lineas.append(r"\bottomrule\end{longtable}}")
    return "\n".join(lineas) + "\n"


def tabla_ll1(tabla):
    columnas = "".join("C{0.98cm}" for _ in TERMINALES)
    cabecera = "&".join(r"\rotatebox{90}{\scriptsize " + nombre_terminal(t) + "}" for t in TERMINALES)
    lineas = [
        r"{\scriptsize\setlength{\tabcolsep}{3.4pt}\begin{longtable}{L{1.7cm}" + columnas + "}",
        r"\caption{Tabla predictiva LL(1). Cada celda indica la producción que se aplica.}"
        r"\label{tab:ll1}" + FILA,
        r"\toprule\textbf{No terminal}&" + cabecera + FILA + r"\midrule\endfirsthead",
        r"\toprule\textbf{No terminal}&" + cabecera + FILA + r"\midrule\endhead",
    ]
    for no_terminal in NO_TERMINALES:
        celdas = [tabla[no_terminal].get(t, "") for t in TERMINALES]
        lineas.append(NOMBRE_FILA.get(no_terminal, no_terminal) + "&" + "&".join(celdas) + FILA)
    lineas.append(r"\bottomrule\end{longtable}}")
    return "\n".join(lineas) + "\n"


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
