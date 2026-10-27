"""Analizador sintactico predictivo de AgroRule por descenso recursivo.

Cada funcion del parser corresponde a un no terminal de la gramatica. Cuando un
no terminal tiene mas de una produccion, la eleccion se hace consultando la
tabla LL(1) con el token de adelanto. Si la tabla no admite ese token, el error
incluye el conjunto de simbolos que la gramatica si admitia.
"""

from .ast_nodes import Accion, Comparacion, Negacion, OpBinaria, Programa, Regla, Termino
from .errors import ErrorSintactico
from .grammar import NO_TERMINALES, NOMBRE_SIMBOLO, construir_tabla, produccion_legible
from .lexer import tokenizar

FIRST, FOLLOW, TABLA, CONFLICTOS = construir_tabla()

# Mensajes para el usuario. Cuando un no terminal falla, se explica en palabras
# del dominio en vez de mostrar su nombre interno, que solo sirve para depurar.
MENSAJES = {
    "lista_reglas": "se esperaba la palabra reservada WHEN o el final del programa",
    "cond": "se esperaba una condición formada por dos valores y un operador relacional",
    "disy": "se esperaba una condición formada por dos valores y un operador relacional",
    "disy_p": "se esperaba OR o el final de la condición (THEN o un paréntesis de cierre)",
    "conj_p": "se esperaba AND, OR o el final de la condición (THEN o un paréntesis de cierre)",
    "conj": "se esperaba una condición formada por dos valores y un operador relacional",
    "neg": "se esperaba una condición formada por dos valores y un operador relacional",
    "prim": "se esperaba una condición o un paréntesis de apertura",
    "comp": "se esperaba una comparación entre dos valores",
    "term": "se esperaba un valor (número, identificador, TRUE o FALSE)",
    "acciones": "se esperaba al menos una acción después de THEN",
    "acciones_p": "se esperaba ';' entre acciones o END para cerrar la regla",
    "llamada": "se esperaba '(' con los argumentos, ';' para otra acción o END para cerrar la regla",
    "args": "se esperaba un argumento",
    "args_p": "se esperaba ',' o el paréntesis de cierre de los argumentos",
    "arg": "se esperaba un argumento (número, TRUE, FALSE, identificador o texto)",
}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0
        self.reglas_construidas = []

    # ---------------------------------------------------------------- utilidades
    @property
    def actual(self):
        return self.tokens[self.posicion]

    def _avanzar(self):
        token = self.tokens[self.posicion]
        if token.tipo != "EOF":
            self.posicion += 1
        return token

    def _esperados(self, no_terminal):
        return [NOMBRE_SIMBOLO.get(t, t) for t in sorted(TABLA[no_terminal])]

    def _elegir(self, no_terminal):
        """Devuelve el identificador de produccion que la tabla asigna al token actual."""
        token = self.actual
        produccion = TABLA[no_terminal].get(token.tipo)
        if produccion is None:
            mensaje = MENSAJES.get(no_terminal, f"no hay producción para {no_terminal} con este símbolo")
            esperado = None if no_terminal in MENSAJES else self._esperados(no_terminal)
            raise ErrorSintactico(
                mensaje,
                token.linea,
                token.columna,
                esperado=esperado,
                encontrado=NOMBRE_SIMBOLO.get(token.tipo, token.tipo),
            )
        return produccion

    def _consumir(self, tipo, mensaje):
        token = self.actual
        if token.tipo != tipo:
            raise ErrorSintactico(
                mensaje,
                token.linea,
                token.columna,
                encontrado=NOMBRE_SIMBOLO.get(token.tipo, f"{token.valor}"),
            )
        return self._avanzar()

    # ------------------------------------------------------------- no terminales
    def programa(self):
        reglas = self.lista_reglas()
        if self.actual.tipo != "EOF":
            token = self.actual
            raise ErrorSintactico(
                "sobra contenido después de la última regla",
                token.linea,
                token.columna,
                esperado=[NOMBRE_SIMBOLO["EOF"]],
                encontrado=f"{token.valor}",
            )
        return Programa(reglas)

    def lista_reglas(self):
        reglas = []
        while self._elegir("lista_reglas") == "P2":
            reglas.append(self.regla())
        return reglas

    def regla(self):
        inicio = self._consumir("WHEN", "se esperaba la palabra reservada WHEN")
        condicion = self.cond()
        self._consumir("THEN", "se esperaba la palabra reservada THEN")
        acciones = self.acciones()
        self._consumir("END", "se esperaba la palabra reservada END para cerrar la regla")
        return Regla(condicion, acciones, inicio.linea)

    def cond(self):
        return self.disy()

    def disy(self):
        izquierda = self.conj()
        while self._elegir("disy_p") == "P7":
            self._avanzar()
            derecha = self.conj()
            izquierda = OpBinaria("OR", izquierda, derecha)
        return izquierda

    def conj(self):
        izquierda = self.neg()
        while self._elegir("conj_p") == "P10":
            self._avanzar()
            derecha = self.neg()
            izquierda = OpBinaria("AND", izquierda, derecha)
        return izquierda

    def neg(self):
        if self._elegir("neg") == "P12":
            self._avanzar()
            return Negacion(self.neg())
        return self.prim()

    def prim(self):
        if self._elegir("prim") == "P14":
            self._avanzar()
            interior = self.cond()
            self._consumir("RPAREN", "se esperaba un paréntesis de cierre")
            return interior
        return self.comp()

    def comp(self):
        izquierda = self.term()
        operador = self._consumir(
            "OP_REL", "se esperaba un operador relacional (>, <, >=, <=, ==, !=)"
        )
        derecha = self.term()
        return Comparacion(operador.valor, izquierda, derecha)

    def term(self):
        token = self.actual
        produccion = self._elegir("term")
        if produccion == "P17":
            self._avanzar()
            return Termino("identificador", token.valor)
        if produccion == "P18":
            self._avanzar()
            return Termino("numero", float(token.valor))
        if produccion == "P19":
            self._avanzar()
            return Termino("booleano", True)
        self._avanzar()
        return Termino("booleano", False)

    def acciones(self):
        acciones = [self.accion()]
        while self._elegir("acciones_p") == "P22":
            self._avanzar()
            acciones.append(self.accion())
        return acciones

    def accion(self):
        nombre = self._consumir("IDENT", "se esperaba el nombre de una acción")
        argumentos = self.llamada()
        return Accion(nombre.valor, argumentos, nombre.linea)

    def llamada(self):
        if self._elegir("llamada") == "P26":
            return []
        self._consumir("LPAREN", "se esperaba un paréntesis de apertura")
        argumentos = self.args()
        self._consumir("RPAREN", "se esperaba un paréntesis de cierre en los argumentos")
        return argumentos

    def args(self):
        argumentos = [self.arg()]
        while self._elegir("args_p") == "P28":
            self._avanzar()
            argumentos.append(self.arg())
        return argumentos

    def arg(self):
        token = self.actual
        produccion = self._elegir("arg")
        if produccion == "P30":
            self._avanzar()
            return Termino("numero", float(token.valor))
        if produccion == "P31":
            self._avanzar()
            return Termino("booleano", True)
        if produccion == "P32":
            self._avanzar()
            return Termino("booleano", False)
        if produccion == "P33":
            self._avanzar()
            return Termino("identificador", token.valor)
        self._avanzar()
        return Termino("texto", token.valor)


def analizar(texto):
    """Analiza un programa completo y devuelve el AST.

    Lanza ErrorSintactico o ErrorLexico si la entrada no es valida.
    """
    tokens = tokenizar(texto)
    parser = Parser(tokens)
    return parser.programa()
