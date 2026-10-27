"""Analizador lexico de AgroRule.

El lenguaje trabaja con tres tipos de dato (numero, booleano y texto), reglas
WHEN/THEN/END y acciones con parametros. Los comentarios empiezan con # y
llegan hasta el final de la linea.
"""

from dataclasses import dataclass

from .errors import ErrorLexico

# Palabras reservadas. Todas se escriben en mayusculas para no confundirlas
# con identificadores de sensores o actuadores.
RESERVADAS = {
    "WHEN": "WHEN",
    "THEN": "THEN",
    "AND": "AND",
    "OR": "OR",
    "NOT": "NOT",
    "END": "END",
    "TRUE": "TRUE",
    "FALSE": "FALSE",
}

OPERADORES = [
    (">=", "OP_REL"),
    ("<=", "OP_REL"),
    ("==", "OP_REL"),
    ("!=", "OP_REL"),
    (">", "OP_REL"),
    ("<", "OP_REL"),
]

PUNTUACION = {
    "(": "LPAREN",
    ")": "RPAREN",
    ";": "SEMI",
    ",": "COMMA",
}


@dataclass(frozen=True)
class Token:
    tipo: str
    valor: str
    linea: int
    columna: int

    def __str__(self):
        return f"{self.tipo}({self.valor}) en {self.linea}:{self.columna}"


def _es_letra(caracter):
    return caracter.isalpha() or caracter == "_"


def _es_digito(caracter):
    return caracter.isdigit()


def tokenizar(texto):
    """Convierte el texto de entrada en una lista de tokens.

    Agrega al final un token EOF que el parser usa como centinela. Cada token
    conserva linea y columna para que los mensajes de error apunten al lugar
    exacto de la entrada.
    """
    tokens = []
    i = 0
    linea = 1
    columna = 1
    largo = len(texto)

    while i < largo:
        caracter = texto[i]

        if caracter == "\n":
            linea += 1
            columna = 1
            i += 1
            continue

        if caracter in " \t\r":
            columna += 1
            i += 1
            continue

        if caracter == "#":
            while i < largo and texto[i] != "\n":
                i += 1
            continue

        if _es_digito(caracter):
            inicio = i
            inicio_col = columna
            while i < largo and (_es_digito(texto[i]) or texto[i] == "."):
                i += 1
                columna += 1
            valor = texto[inicio:i]
            if valor.count(".") > 1:
                raise ErrorLexico(f"número mal formado: {valor}", linea, inicio_col)
            tokens.append(Token("NUM", valor, linea, inicio_col))
            continue

        if _es_letra(caracter):
            inicio = i
            inicio_col = columna
            while i < largo and (_es_letra(texto[i]) or _es_digito(texto[i])):
                i += 1
                columna += 1
            palabra = texto[inicio:i]
            tipo = RESERVADAS.get(palabra.upper(), "IDENT")
            tokens.append(Token(tipo, palabra, linea, inicio_col))
            continue

        if caracter == '"':
            inicio_col = columna
            i += 1
            columna += 1
            inicio = i
            while i < largo and texto[i] != '"':
                if texto[i] == "\n":
                    raise ErrorLexico("texto sin cerrar", linea, inicio_col)
                i += 1
                columna += 1
            if i >= largo:
                raise ErrorLexico("texto sin cerrar", linea, inicio_col)
            tokens.append(Token("CADENA", texto[inicio:i], linea, inicio_col))
            i += 1
            columna += 1
            continue

        encontrado = False
        for simbolo, tipo in OPERADORES:
            if texto.startswith(simbolo, i):
                tokens.append(Token(tipo, simbolo, linea, columna))
                i += len(simbolo)
                columna += len(simbolo)
                encontrado = True
                break
        if encontrado:
            continue

        if caracter in PUNTUACION:
            tokens.append(Token(PUNTUACION[caracter], caracter, linea, columna))
            i += 1
            columna += 1
            continue

        raise ErrorLexico(f"carácter no permitido: {caracter!r}", linea, columna)

    tokens.append(Token("EOF", "", linea, columna))
    return tokens
