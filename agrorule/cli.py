"""Interfaz de linea de comandos de AgroRule."""

import argparse
import sys
from pathlib import Path

from .errors import ErrorLexico, ErrorSintactico
from .grammar import construir_tabla, es_ll1, formatear_conjunto, produccion_legible
from .lexer import tokenizar
from .parser import analizar


def _leer_entrada(argumentos):
    if argumentos.texto:
        return argumentos.texto
    ruta = Path(argumentos.archivo)
    if not ruta.exists():
        print(f"No existe el archivo {ruta}")
        raise SystemExit(2)
    return ruta.read_text(encoding="utf-8")


def _mostrar_tabla():
    first, follow, tabla, conflictos = construir_tabla()
    print("FIRST y FOLLOW por no terminal")
    for no_terminal in first:
        print(f"  {no_terminal:14s} FIRST {formatear_conjunto(first[no_terminal]):40s} FOLLOW {formatear_conjunto(follow[no_terminal])}")
    valida, conflictos = es_ll1()
    print("\nLa gramatica es LL(1):", "si" if valida else "no")
    for cabeza, terminal, uno, otro in conflictos:
        print(f"  conflicto en {cabeza} con {terminal}: {uno} y {otro}")
    print("\nTabla predictiva")
    for no_terminal, fila in tabla.items():
        for terminal, produccion in sorted(fila.items()):
            print(f"  M[{no_terminal}, {terminal}] = {produccion_legible(produccion)}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="agrorule",
        description="Analizador sintactico del lenguaje de automatizacion de invernaderos AgroRule",
    )
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("archivo", nargs="?", help="archivo .ar con el programa a analizar")
    grupo.add_argument("--texto", help="programa entregado directamente como texto")
    parser.add_argument("--ast", action="store_true", help="imprime el arbol sintactico")
    parser.add_argument("--dot", help="escribe el AST en formato Graphviz en la ruta indicada")
    parser.add_argument("--tokens", action="store_true", help="imprime la lista de tokens")
    parser.add_argument("--tabla", action="store_true", help="imprime FIRST, FOLLOW y la tabla LL(1)")
    argumentos = parser.parse_args(argv)

    if argumentos.tabla:
        _mostrar_tabla()
        return 0

    if not argumentos.archivo and not argumentos.texto:
        parser.error("indica un archivo .ar, un programa con --texto o consulta la tabla con --tabla")

    try:
        texto = _leer_entrada(argumentos)
        if argumentos.tokens:
            for token in tokenizar(texto):
                print(token)
        arbol = analizar(texto)
    except (ErrorLexico, ErrorSintactico) as error:
        print(error)
        return 1

    if argumentos.ast:
        print(arbol.dibujar())
    if argumentos.dot:
        Path(argumentos.dot).write_text(arbol.a_dot(), encoding="utf-8")
        print(f"AST escrito en {argumentos.dot}")
    if not argumentos.ast and not argumentos.dot and not argumentos.tokens:
        print(f"Entrada valida. Reglas reconocidas: {len(arbol.reglas)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
