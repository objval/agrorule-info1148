"""Errores del analisis lexico y sintactico."""


class ErrorLexico(Exception):
    """Caracter o secuencia que no pertenece al alfabeto del lenguaje."""

    def __init__(self, mensaje, linea, columna):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna

    def __str__(self):
        return f"Error léxico (línea {self.linea}, columna {self.columna}): {self.mensaje}"


class ErrorSintactico(Exception):
    """La secuencia de tokens no cumple la gramatica.

    Guarda la posicion del token que rompio la regla y, cuando se conoce, el
    conjunto de simbolos que la gramatica admitia en ese punto. Ese conjunto
    sale de la tabla LL(1), por lo que el mensaje y la gramatica no pueden
    divergir.
    """

    def __init__(self, mensaje, linea, columna, esperado=None, encontrado=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna
        self.esperado = list(esperado) if esperado else []
        self.encontrado = encontrado

    def __str__(self):
        mensaje = self.mensaje.rstrip(".")
        base = f"Error sintáctico (línea {self.linea}, columna {self.columna}): {mensaje}."
        if self.esperado:
            base += " Se esperaba: " + ", ".join(self.esperado) + "."
        if self.encontrado:
            base += f" Se encontró: {self.encontrado}."
        return base
