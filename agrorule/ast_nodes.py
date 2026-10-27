"""Nodos del arbol sintactico abstracto de AgroRule.

El AST conserva la estructura de la entrada, no los simbolos de la gramatica.
Por eso una regla queda como Regla(condicion, acciones) sin guardar WHEN, THEN
ni END. Esa diferencia es la que se muestra en el informe cuando se compara el
arbol de derivacion con el AST.
"""

from dataclasses import dataclass, field


@dataclass
class Termino:
    tipo: str
    valor: object

    def etiqueta(self):
        if self.tipo == "numero":
            return f"número {self.valor:g}"
        if self.tipo == "booleano":
            return f"booleano {'TRUE' if self.valor else 'FALSE'}"
        if self.tipo == "texto":
            return f'texto "{self.valor}"'
        return f"identificador {self.valor}"

    def hijos(self):
        return []


@dataclass
class Comparacion:
    operador: str
    izquierda: object
    derecha: object

    def etiqueta(self):
        return f"comparación {self.operador}"

    def hijos(self):
        return [self.izquierda, self.derecha]


@dataclass
class OpBinaria:
    operador: str
    izquierda: object
    derecha: object

    def etiqueta(self):
        return f"lógico {self.operador}"

    def hijos(self):
        return [self.izquierda, self.derecha]


@dataclass
class Negacion:
    expresion: object

    def etiqueta(self):
        return "negación NOT"

    def hijos(self):
        return [self.expresion]


@dataclass
class Accion:
    nombre: str
    argumentos: list
    linea: int

    def etiqueta(self):
        return f"acción {self.nombre}"

    def hijos(self):
        return list(self.argumentos)


@dataclass
class Regla:
    condicion: object
    acciones: list
    linea: int

    def etiqueta(self):
        return f"regla (línea {self.linea})"

    def hijos(self):
        return [self.condicion] + list(self.acciones)


@dataclass
class Programa:
    reglas: list = field(default_factory=list)

    def etiqueta(self):
        return f"programa ({len(self.reglas)} {'regla' if len(self.reglas) == 1 else 'reglas'})"

    def hijos(self):
        return list(self.reglas)

    # ------------------------------------------------------------- recorrido
    def dibujar(self):
        """Arbol en texto con lineas guia, util para revisar a mano."""
        lineas = []

        def visitar(nodo, prefijo, es_ultimo):
            conector = "└─ " if es_ultimo else "├─ "
            lineas.append(prefijo + conector + nodo.etiqueta())
            hijos = nodo.hijos()
            for indice, hijo in enumerate(hijos):
                extension = "   " if es_ultimo else "│  "
                visitar(hijo, prefijo + extension, indice == len(hijos) - 1)

        lineas.append(self.etiqueta())
        for indice, regla in enumerate(self.reglas):
            visitar(regla, "", indice == len(self.reglas) - 1)
        return "\n".join(lineas)

    def a_dot(self):
        """Representacion Graphviz para incluir en el informe."""
        lineas = ["digraph AST {", "  rankdir=TB;", "  node [shape=box, fontname=\"Arial\", fontsize=10];"]
        contador = [0]

        def nuevo_id():
            contador[0] += 1
            return f"n{contador[0]}"

        def visitar(nodo, padre=None):
            identificador = nuevo_id()
            etiqueta = nodo.etiqueta().replace('"', '\\"')
            lineas.append(f'  {identificador} [label="{etiqueta}"];')
            if padre:
                lineas.append(f"  {padre} -> {identificador};")
            for hijo in nodo.hijos():
                visitar(hijo, identificador)

        visitar(self)
        lineas.append("}")
        return "\n".join(lineas)



def contar_nodos(nodo):
    """Cuenta los nodos del subarbol, util para comparar tamanos entre entradas."""
    return 1 + sum(contar_nodos(hijo) for hijo in nodo.hijos())
