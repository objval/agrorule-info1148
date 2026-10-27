"""Gramatica libre de contexto de AgroRule y calculo de la tabla LL(1).

Las producciones se declaran una sola vez. De esa declaracion salen FIRST,
FOLLOW y la tabla predictiva que usa el parser, de modo que el informe y el
codigo no pueden contradecirse.
"""

from .errors import ErrorSintactico

EPSILON = "epsilon"

# Cada produccion es (identificador, cabeza, cuerpo). El cuerpo vacio representa
# la produccion epsilon.
PRODUCCIONES = [
    ("P1", "programa", ("lista_reglas",)),
    ("P2", "lista_reglas", ("regla", "lista_reglas")),
    ("P3", "lista_reglas", ()),
    ("P4", "regla", ("WHEN", "cond", "THEN", "acciones", "END")),
    ("P5", "cond", ("disy",)),
    ("P6", "disy", ("conj", "disy_p")),
    ("P7", "disy_p", ("OR", "conj", "disy_p")),
    ("P8", "disy_p", ()),
    ("P9", "conj", ("neg", "conj_p")),
    ("P10", "conj_p", ("AND", "neg", "conj_p")),
    ("P11", "conj_p", ()),
    ("P12", "neg", ("NOT", "neg")),
    ("P13", "neg", ("prim",)),
    ("P14", "prim", ("LPAREN", "cond", "RPAREN")),
    ("P15", "prim", ("comp",)),
    ("P16", "comp", ("term", "OP_REL", "term")),
    ("P17", "term", ("IDENT",)),
    ("P18", "term", ("NUM",)),
    ("P19", "term", ("TRUE",)),
    ("P20", "term", ("FALSE",)),
    ("P21", "acciones", ("accion", "acciones_p")),
    ("P22", "acciones_p", ("SEMI", "accion", "acciones_p")),
    ("P23", "acciones_p", ()),
    ("P24", "accion", ("IDENT", "llamada")),
    ("P25", "llamada", ("LPAREN", "args", "RPAREN")),
    ("P26", "llamada", ()),
    ("P27", "args", ("arg", "args_p")),
    ("P28", "args_p", ("COMMA", "arg", "args_p")),
    ("P29", "args_p", ()),
    ("P30", "arg", ("NUM",)),
    ("P31", "arg", ("TRUE",)),
    ("P32", "arg", ("FALSE",)),
    ("P33", "arg", ("IDENT",)),
    ("P34", "arg", ("CADENA",)),
]

NO_TERMINALES = []
for _, cabeza, _ in PRODUCCIONES:
    if cabeza not in NO_TERMINALES:
        NO_TERMINALES.append(cabeza)

SIMBOLO_INICIAL = "programa"

TERMINALES = []
for _, _, cuerpo in PRODUCCIONES:
    for simbolo in cuerpo:
        if simbolo not in NO_TERMINALES and simbolo not in TERMINALES:
            TERMINALES.append(simbolo)
TERMINALES.append("EOF")

NOMBRE_SIMBOLO = {
    "WHEN": "WHEN",
    "THEN": "THEN",
    "AND": "AND",
    "OR": "OR",
    "NOT": "NOT",
    "END": "END",
    "TRUE": "TRUE",
    "FALSE": "FALSE",
    "OP_REL": "operador relacional",
    "LPAREN": "(",
    "RPAREN": ")",
    "SEMI": ";",
    "COMMA": ",",
    "NUM": "número",
    "IDENT": "identificador",
    "CADENA": "texto",
    "EOF": "fin de entrada",
}

CUERPO_POR_ID = {pid: (cabeza, cuerpo) for pid, cabeza, cuerpo in PRODUCCIONES}


def _first_de_secuencia(secuencia, first, nullable):
    resultado = set()
    for simbolo in secuencia:
        if simbolo == EPSILON:
            resultado.add(EPSILON)
            return resultado
        if simbolo in TERMINALES:
            resultado.add(simbolo)
            return resultado
        resultado |= (first[simbolo] - {EPSILON})
        if EPSILON not in first[simbolo]:
            return resultado
    resultado.add(EPSILON)
    return resultado


def calcular_first():
    """FIRST de cada no terminal, con epsilon donde corresponde."""
    first = {nt: set() for nt in NO_TERMINALES}
    cambio = True
    while cambio:
        cambio = False
        for _, cabeza, cuerpo in PRODUCCIONES:
            if not cuerpo:
                if EPSILON not in first[cabeza]:
                    first[cabeza].add(EPSILON)
                    cambio = True
                continue
            nuevos = _first_de_secuencia(cuerpo, first, True)
            if not nuevos <= first[cabeza]:
                first[cabeza] |= nuevos
                cambio = True
    return first


def calcular_follow(first):
    """FOLLOW de cada no terminal. El símbolo inicial recibe EOF."""
    follow = {nt: set() for nt in NO_TERMINALES}
    follow[SIMBOLO_INICIAL].add("EOF")
    cambio = True
    while cambio:
        cambio = False
        for _, cabeza, cuerpo in PRODUCCIONES:
            for indice, simbolo in enumerate(cuerpo):
                if simbolo not in NO_TERMINALES:
                    continue
                resto = cuerpo[indice + 1:]
                first_resto = _first_de_secuencia(resto, first, True) if resto else {EPSILON}
                aporte = first_resto - {EPSILON}
                if EPSILON in first_resto:
                    aporte |= follow[cabeza]
                if not aporte <= follow[simbolo]:
                    follow[simbolo] |= aporte
                    cambio = True
    return follow


def construir_tabla():
    """Tabla predictiva LL(1) y lista de conflictos si la gramatica no lo es."""
    first = calcular_first()
    follow = calcular_follow(first)
    tabla = {nt: {} for nt in NO_TERMINALES}
    conflictos = []
    for pid, cabeza, cuerpo in PRODUCCIONES:
        prediccion = _first_de_secuencia(cuerpo, first, True) if cuerpo else {EPSILON}
        if EPSILON in prediccion:
            prediccion = (prediccion - {EPSILON}) | follow[cabeza]
        for terminal in sorted(prediccion):
            if terminal in tabla[cabeza] and tabla[cabeza][terminal] != pid:
                conflictos.append((cabeza, terminal, tabla[cabeza][terminal], pid))
            else:
                tabla[cabeza][terminal] = pid
    return first, follow, tabla, conflictos


def es_ll1():
    _, _, _, conflictos = construir_tabla()
    return not conflictos, conflictos


def formatear_conjunto(conjunto):
    """Texto legible de un conjunto, con epsilon al final si aparece."""
    orden = [s for s in TERMINALES if s in conjunto]
    if EPSILON in conjunto:
        orden.append(EPSILON)
    return "{" + ", ".join(orden) + "}"


def produccion_legible(pid):
    cabeza, cuerpo = CUERPO_POR_ID[pid]
    cuerpo_texto = " ".join(cuerpo) if cuerpo else "epsilon"
    return f"{cabeza} -> {cuerpo_texto}"
