"""Pruebas del analizador AgroRule.

Se cubren los diez casos validos, los diez invalidos y los cinco casos limite
que exige el enunciado del proyecto.
"""

import sys
import subprocess
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agrorule import ErrorSintactico, analizar  # noqa: E402
from agrorule.errors import ErrorLexico  # noqa: E402
from agrorule.grammar import construir_tabla, es_ll1  # noqa: E402
from agrorule.lexer import tokenizar  # noqa: E402

VALIDOS = [
    "WHEN temperatura > 28 THEN abrir_ventilador END",
    "WHEN humedad < 30 AND temperatura > 25 THEN regar(20) END",
    'WHEN suelo == seco OR lluvia == FALSE THEN regar(15); avisar("riego activo") END',
    "WHEN NOT (temperatura > 30) THEN cerrar_techo END",
    "WHEN luz >= 800 THEN bajar_malla(50); encender_extractor END",
    "WHEN temperatura > 28 THEN abrir_ventilador END WHEN humedad < 30 THEN regar(20) END",
    "WHEN CO2 > 900 AND humedad > 80 THEN ventilar(TRUE) END",
    "WHEN NOT NOT lluvia == TRUE THEN cerrar_techo END",
    "WHEN ((temperatura > 28)) THEN abrir_ventilador(75) END",
    'WHEN ph >= 6.5 AND ph <= 7.5 THEN fertirriego(1.5, "nitrato") END',
]

INVALIDOS = [
    ("WHEN temperatura > 28 abrir_ventilador END", "then"),
    ("WHEN temperatura > 28 THEN abrir_ventilador", "end"),
    ("WHEN temperatura > THEN abrir_ventilador END", "valor"),
    ("WHEN temperatura > 28 THEN END", "acción"),
    ("WHEN temperatura > 28 THEN regar(20) abrir_ventilador END", "entre acciones"),
    ("WHEN THEN regar(20) END", "condición"),
    ("WHEN (temperatura > 28 THEN regar(20) END", "cierre"),
    ("WHEN temperatura > 28 THEN regar(20) END @", "carácter"),
    ("WHEN temperatura > 28 THEN regar(20, ) END", "argumento"),
    ("WHEN temperatura 28 THEN regar(20) END", "operador"),
]

LIMITE = [
    ("", 0),
    ("# solo comentarios\n# sin reglas\n", 0),
    ("WHEN NOT NOT NOT temperatura > 5 THEN calentar END", 1),
    ("WHEN temperatura > 5 THEN avisar END", 1),
    ("WHEN temperatura > 5 THEN regar(1); regar(2); regar(3); cerrar_techo END", 1),
]


class PruebasGramatica(unittest.TestCase):
    def test_gramatica_es_ll1(self):
        valida, conflictos = es_ll1()
        self.assertTrue(valida, f"hay conflictos LL(1): {conflictos}")

    def test_la_tabla_cubre_todos_los_no_terminales(self):
        first, follow, tabla, _ = construir_tabla()
        self.assertEqual(set(tabla), set(first))
        for no_terminal, fila in tabla.items():
            self.assertTrue(fila, f"{no_terminal} no tiene entradas en la tabla")

    def test_first_y_follow_del_simbolo_inicial(self):
        first, follow, _, _ = construir_tabla()
        self.assertIn("EOF", follow["programa"])
        self.assertIn("WHEN", first["programa"])


class PruebasValidas(unittest.TestCase):
    def test_diez_entradas_validas(self):
        for numero, programa in enumerate(VALIDOS, 1):
            with self.subTest(caso=numero):
                arbol = analizar(programa)
                self.assertGreaterEqual(len(arbol.reglas), 1)

    def test_multiples_reglas_se_conservan_en_orden(self):
        arbol = analizar(VALIDOS[5])
        self.assertEqual(len(arbol.reglas), 2)
        self.assertEqual(arbol.reglas[0].acciones[0].nombre, "abrir_ventilador")
        self.assertEqual(arbol.reglas[1].acciones[0].nombre, "regar")

    def test_ast_refleja_la_precedencia_de_and_sobre_or(self):
        arbol = analizar("WHEN a > 1 OR b > 2 AND c > 3 THEN accion END")
        condicion = arbol.reglas[0].condicion
        self.assertEqual(condicion.operador, "OR")
        self.assertEqual(condicion.derecha.operador, "AND")

    def test_los_argumentos_conservan_tipo(self):
        arbol = analizar('WHEN a > 1 THEN regar(20, TRUE, "x") END')
        tipos = [argumento.tipo for argumento in arbol.reglas[0].acciones[0].argumentos]
        self.assertEqual(tipos, ["numero", "booleano", "texto"])

    def test_el_arbol_se_puede_exportar_a_dot(self):
        arbol = analizar(VALIDOS[0])
        dot = arbol.a_dot()
        self.assertTrue(dot.startswith("digraph AST"))
        self.assertIn("->", dot)


class PruebasInvalidas(unittest.TestCase):
    def test_diez_entradas_invalidas(self):
        for numero, (programa, fragmento) in enumerate(INVALIDOS, 1):
            with self.subTest(caso=numero):
                with self.assertRaises((ErrorSintactico, ErrorLexico)) as contexto:
                    analizar(programa)
                mensaje = str(contexto.exception).lower()
                self.assertIn(
                    fragmento,
                    mensaje,
                    f"el mensaje no menciona {fragmento!r}: {mensaje}",
                )

    def test_el_error_indica_linea_y_columna(self):
        with self.assertRaises(ErrorSintactico) as contexto:
            analizar("WHEN temperatura > 28\nTHEN regar(20) abrir_ventilador END")
        self.assertIn("línea 2", str(contexto.exception))

    def test_error_muestra_terminales_de_la_tabla(self):
        with self.assertRaises(ErrorSintactico) as contexto:
            analizar("WHEN THEN regar END")
        esperados = contexto.exception.esperado
        self.assertIn("NOT", esperados)
        self.assertIn("identificador", esperados)
        self.assertIn("(", esperados)
        self.assertIn("Se esperaba:", str(contexto.exception))

    def test_palabras_reservadas_distinguen_mayusculas(self):
        for palabra in ("when", "When"):
            with self.subTest(palabra=palabra):
                with self.assertRaises(ErrorSintactico):
                    analizar(f"{palabra} a > 1 THEN regar END")
        self.assertEqual(tokenizar("true")[0].tipo, "IDENT")

    def test_digitos_no_ascii_se_rechazan_sin_excepcion_nativa(self):
        for valor in ("²", "١", "a²"):
            with self.subTest(valor=valor):
                with self.assertRaises(ErrorLexico):
                    analizar(f"WHEN a > {valor} THEN regar END")

    def test_decimales_incompletos_se_rechazan(self):
        for valor in ("1.", "1.2.3"):
            with self.subTest(valor=valor):
                with self.assertRaises(ErrorLexico) as contexto:
                    analizar(f"WHEN a > {valor} THEN regar END")
                self.assertIn("mal formado", str(contexto.exception))

    def test_numeros_fuera_de_rango_se_rechazan_en_ambos_contextos(self):
        enorme = "9" * 400
        for programa in (f"WHEN a > {enorme} THEN regar END",
                         f"WHEN a > 1 THEN regar({enorme}) END"):
            with self.subTest(argumento="regar(" in programa):
                with self.assertRaises(ErrorLexico) as contexto:
                    analizar(programa)
                self.assertIn("fuera de rango", str(contexto.exception))

    def test_llamada_sin_argumentos_no_pertenece_a_la_gramatica(self):
        with self.assertRaises(ErrorSintactico) as contexto:
            analizar("WHEN a > 1 THEN regar() END")
        self.assertIn("argumento", str(contexto.exception))


class PruebasLimite(unittest.TestCase):
    def test_casos_limite(self):
        for programa, reglas_esperadas in LIMITE:
            with self.subTest(programa=programa[:40]):
                arbol = analizar(programa)
                self.assertEqual(len(arbol.reglas), reglas_esperadas)

    def test_anidamiento_profundo_no_desborda(self):
        programa = "WHEN " + "(" * 40 + "temperatura > 5" + ")" * 40 + " THEN calentar END"
        arbol = analizar(programa)
        self.assertEqual(len(arbol.reglas), 1)

    def test_limite_de_grupos_informa_posicion(self):
        programa = "WHEN " + "(" * 81 + "a > 1" + ")" * 81 + " THEN regar END"
        with self.assertRaises(ErrorSintactico) as contexto:
            analizar(programa)
        self.assertIn("80 grupos anidados", str(contexto.exception))
        self.assertIn("columna 86", str(contexto.exception))

    def test_texto_largo_en_argumentos(self):
        programa = 'WHEN a > 1 THEN avisar("' + "x" * 500 + '") END'
        arbol = analizar(programa)
        self.assertEqual(len(arbol.reglas[0].acciones[0].argumentos[0].valor), 500)

    def test_negaciones_consecutivas_no_desbordan(self):
        cantidad = 1200
        arbol = analizar("WHEN " + "NOT " * cantidad + "a > 1 THEN regar END")
        condicion = arbol.reglas[0].condicion
        for _ in range(cantidad):
            self.assertEqual(type(condicion).__name__, "Negacion")
            condicion = condicion.expresion
        self.assertEqual(type(condicion).__name__, "Comparacion")

class PruebasCLI(unittest.TestCase):
    def ejecutar(self, *argumentos):
        return subprocess.run(
            [sys.executable, "-m", "agrorule", *argumentos],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True, check=False,
        )

    def test_texto_vacio_y_archivo_omitido(self):
        vacio = self.ejecutar("--texto", "")
        self.assertEqual(vacio.returncode, 0, vacio.stderr)
        self.assertIn("Reglas reconocidas: 0", vacio.stdout)
        omitido = self.ejecutar()
        self.assertEqual(omitido.returncode, 2)
        self.assertIn("indica un archivo", omitido.stderr)

    def test_errores_cli_no_muestran_traceback(self):
        for valor in ("²", "1.", "9" * 400):
            with self.subTest(valor=valor[:20]):
                proceso = self.ejecutar("--texto", f"WHEN a > {valor} THEN regar END")
                self.assertEqual(proceso.returncode, 1, proceso.stderr)
                self.assertIn("Error léxico", proceso.stdout)
                self.assertNotIn("Traceback", proceso.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
