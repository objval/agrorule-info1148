"""Convierte salidas reales de la consola en imagenes para el anexo.

No se dibuja nada a mano: cada imagen es la salida que produjo el analizador en
esta misma corrida.
"""

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

SALIDA = RAIZ.parent / "informe" / "figuras"
PY = sys.executable

CASOS = [
    ("captura_valido.png", ["-m", "agrorule", "examples/validos/03_tres_reglas.ar", "--ast"]),
    ("captura_error.png", ["-m", "agrorule", "examples/invalidos/01_sin_then.ar"]),
    ("captura_tabla.png", ["-m", "agrorule", "--tabla"]),
]


def render(texto, destino):
    lineas = texto.splitlines()[:48]
    fuente = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 15)
    ancho = max(len(linea) for linea in lineas) * 9 + 40
    alto = len(lineas) * 22 + 70
    imagen = Image.new("RGB", (max(ancho, 700), alto), (28, 32, 38))
    dibujo = ImageDraw.Draw(imagen)
    dibujo.rectangle((0, 0, imagen.width, 34), fill=(48, 54, 62))
    for indice, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        dibujo.ellipse((14 + indice * 22, 11, 26 + indice * 22, 23), fill=color)
    dibujo.text((90, 10), "agrorule  ·  consola", font=fuente, fill=(190, 196, 204))
    for indice, linea in enumerate(lineas):
        color = (120, 214, 130) if not linea.lower().startswith("error") else (255, 138, 128)
        dibujo.text((18, 48 + indice * 22), linea, font=fuente, fill=color)
    imagen.save(destino, optimize=True)
    print("captura:", destino.name, imagen.size)


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    for nombre, argumentos in CASOS:
        resultado = subprocess.run(
            [PY] + argumentos, cwd=RAIZ, capture_output=True, text=True
        )
        texto = (resultado.stdout or "") + (resultado.stderr or "")
        render(texto, SALIDA / nombre)


if __name__ == "__main__":
    main()
