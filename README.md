# AgroRule: analizador sintáctico LL(1) para un DSL de invernaderos

Proyecto de Teoría de la Computación (INFO1148). El repositorio contiene el
diseño del lenguaje, la gramática libre de contexto, el cálculo de FIRST y
FOLLOW, la tabla predictiva LL(1) y el analizador sintáctico implementado en
Python con descenso recursivo guiado por la tabla.

La versión de Convocatoria 2 incluye el [informe PDF](docs/informe_C2.pdf),
su [fuente LaTeX](docs/c2/informe.tex) y las capturas en `docs/c2/figuras/`.
El PDF anterior (`docs/informe.pdf`) se conserva como respaldo de C1.

## Requisitos

Python 3.10 o superior. No se usan bibliotecas externas para el análisis. Para
regenerar la imagen del árbol se necesita Graphviz (`dot`) instalado. Para
regenerar las capturas del informe se necesita Pillow (`pip install pillow`).

## Ejecución

```bash
# analizar un archivo
python3 -m agrorule examples/validos/03_tres_reglas.ar

# analizar texto directo y mostrar el árbol
python3 -m agrorule --texto 'WHEN temperatura > 28 THEN abrir_ventilador(80) END' --ast

# ver tokens
python3 -m agrorule examples/validos/01_riego_simple.ar --tokens

# exportar el AST a Graphviz
python3 -m agrorule examples/validos/03_tres_reglas.ar --dot ast.dot

# imprimir FIRST, FOLLOW y la tabla LL(1)
python3 -m agrorule --tabla

# pruebas
python3 -m unittest discover -s tests -v
```

Códigos de salida: 0 si la entrada es válida, 1 si el análisis falla, 2 si el
archivo no existe.

## Formato de entrada

Una regla tiene la forma `WHEN <condición> THEN <acciones> END`. Se pueden
escribir varias reglas seguidas. La condición compara dos valores con
`>`, `<`, `>=`, `<=`, `==` o `!=`, y se puede combinar con `AND`, `OR`, `NOT` y
paréntesis. Las acciones son identificadores con argumentos entre paréntesis o sin
paréntesis cuando no tienen argumentos (`regar`, no `regar()`). Se separan por
punto y coma. Los comentarios empiezan con `#`. Las palabras reservadas se
escriben en mayúsculas, y los números usan dígitos ASCII (`1` o `1.5`, no `1.`).
Se admiten hasta 80 grupos de paréntesis anidados; una profundidad mayor se
rechaza con un error que indica línea y columna.

```
# ejemplo
WHEN temperatura > 28 AND humedad < 40 THEN abrir_ventilador(80); avisar("calor") END
```

## Estructura

```
agrorule/
  lexer.py      analizador lexico, tokens con linea y columna
  grammar.py    producciones, FIRST, FOLLOW y tabla LL(1) calculados
  parser.py     descenso recursivo que consulta la tabla
  ast_nodes.py  nodos del AST, dibujo en texto y exportacion a Graphviz
  errors.py     errores lexicos y sintacticos con posicion
  cli.py        interfaz de linea de comandos
scripts/        generacion de tablas, arbol y capturas para el informe
tests/          23 pruebas, incluidos 10 validos, 10 invalidos y 5 casos limite
examples/       programas de ejemplo validos e invalidos
```

## Reconstrucción del informe C2

Desde la raíz del repositorio, los generadores actualizan `docs/c2/tablas/` y
`docs/c2/figuras/` (requieren Pillow para las capturas y Graphviz para el AST):

```bash
python3 scripts/generar_tablas.py
python3 scripts/generar_casos.py
python3 scripts/generar_arbol.py
python3 scripts/capturas.py
cd docs/c2
pdflatex -interaction=nonstopmode -halt-on-error informe.tex
pdflatex -interaction=nonstopmode -halt-on-error informe.tex
```

## Resultados

La gramática tiene 34 producciones, 19 no terminales y 16 terminales más el
centinela de fin de entrada. No tiene recursión izquierda ni conflictos, por lo
que la tabla LL(1) queda completa con 68 celdas y el analizador no retrocede.
