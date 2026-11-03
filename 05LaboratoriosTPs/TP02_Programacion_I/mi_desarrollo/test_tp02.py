"""Pruebas del controlador sin necesidad de abrir el simulador.

Desde la carpeta del TP: python -m unittest discover -s mi_desarrollo -v
"""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import mi_tp02
from robot import ErrorDeSeguridad, Robot


INVALIDOS = [
    (None, "tupla"),
    (3, "tupla"),
    ("avanzar", "tupla"),
    (["detenerse"], "tupla"),
    ((), "vacia"),
    (("volar", 0.2, 1.0), "desconocido"),
    ((["avanzar"], 0.2, 1.0), "desconocido"),
    (("avanzar", 0.2), "velocidad y tiempo"),
    (("girar",), "velocidad y tiempo"),
    (("avanzar", 0.2, 1.0, 4), "velocidad y tiempo"),
    (("saludar", 2), "no lleva"),
    (("detenerse", 0.0, 1.0), "no lleva"),
    (("avanzar", "rapido", 1.0), "velocidad"),
    (("girar", 0.2, "mucho"), "tiempo"),
    (("avanzar", True, 1.0), "velocidad"),
    (("girar", 0.2, False), "tiempo"),
    (("avanzar", 0.2, -1.0), "negativo"),
]


class PruebasControlador(unittest.TestCase):
    def test_comandos_validos(self):
        comandos = [
            ("avanzar", 0.2, 2.0),
            ("avanzar", -0.2, 0),
            ("girar", -0.5, 3.14),
            ("girar", 0, 1),
            ("detenerse",),
            ("saludar",),
        ]
        for comando in comandos:
            with self.subTest(comando=comando):
                self.assertIs(mi_tp02.comando_es_valido(comando), True)
                self.assertEqual(mi_tp02.motivo_comando_invalido(comando), "")

    def test_comandos_invalidos_y_motivos(self):
        for comando, motivo in INVALIDOS:
            with self.subTest(comando=comando):
                self.assertIs(mi_tp02.comando_es_valido(comando), False)
                self.assertIn(motivo, mi_tp02.motivo_comando_invalido(comando))

    def test_limites_los_valida_el_robot(self):
        for comando in [("avanzar", 0.9, 2.0), ("girar", 3.0, 2.0),
                        ("avanzar", 0.2, 50.0)]:
            with self.subTest(comando=comando):
                self.assertIs(mi_tp02.comando_es_valido(comando), True)

    def test_cada_orden_llama_al_metodo_correspondiente(self):
        for comando in [("avanzar", -0.2, 2.0), ("girar", -0.5, 3.14),
                        ("detenerse",), ("saludar",)]:
            with self.subTest(comando=comando):
                robot = Mock(spec=Robot)
                resultado = mi_tp02.ejecutar_comando(robot, comando)
                self.assertTrue(resultado.startswith("Ejecutado:"))
                metodo = getattr(robot, comando[0])
                if len(comando) == 3:
                    metodo.assert_called_once_with(velocidad=comando[1], tiempo=comando[2])
                else:
                    metodo.assert_called_once_with()
                self.assertEqual(len(robot.mock_calls), 1)

    def test_ejecutar_invalido_no_llama_al_robot(self):
        for comando, motivo in INVALIDOS:
            with self.subTest(comando=comando):
                robot = Mock(spec=Robot)
                resultado = mi_tp02.ejecutar_comando(robot, comando)
                self.assertTrue(resultado.startswith("Rechazado:"))
                self.assertIn(motivo, resultado)
                self.assertEqual(robot.mock_calls, [])

    def test_error_de_seguridad_detiene_y_devuelve_el_motivo(self):
        robot = Mock(spec=Robot)
        robot.avanzar.side_effect = ErrorDeSeguridad("Velocidad fuera del limite.")
        resultado = mi_tp02.ejecutar_comando(robot, ("avanzar", 0.9, 2.0))
        self.assertEqual(resultado, "Rechazado: Velocidad fuera del limite.")
        robot.detenerse.assert_called_once_with()

    def test_mision_continua_tras_rechazos_y_conserva_historial(self):
        robot = Mock(spec=Robot)
        robot.avanzar.side_effect = ErrorDeSeguridad("Velocidad fuera del limite.")
        previo = {"comando": ("saludar",), "resultado": "Ejecutado: saludar."}
        historial = [previo]
        mision = [("volar",), ("avanzar", 0.9, 2.0), ("saludar",), ("detenerse",)]
        with redirect_stdout(io.StringIO()):
            mi_tp02.ejecutar_mision(robot, mision, historial)
        self.assertIs(historial[0], previo)
        self.assertEqual([r["comando"] for r in historial[1:]], mision)
        self.assertTrue(historial[1]["resultado"].startswith("Rechazado:"))
        self.assertTrue(historial[2]["resultado"].startswith("Rechazado:"))
        self.assertTrue(historial[3]["resultado"].startswith("Ejecutado:"))
        self.assertTrue(historial[4]["resultado"].startswith("Ejecutado:"))
        robot.saludar.assert_called_once_with()
        self.assertEqual(robot.detenerse.call_count, 2)

    def test_reporte_cuenta_y_muestra_cada_rechazo(self):
        historial = [
            {"comando": ("saludar",), "resultado": "Ejecutado: saludar."},
            {"comando": ("volar",), "resultado": "Rechazado: Comando desconocido: volar."},
            {"comando": ("girar", 0.2, -1), "resultado": "Rechazado: El tiempo no puede ser negativo."},
        ]
        salida = io.StringIO()
        with redirect_stdout(salida):
            mi_tp02.generar_reporte(historial)
        self.assertIn("Total de comandos: 3", salida.getvalue())
        self.assertIn("Ejecutados: 1", salida.getvalue())
        self.assertIn("Rechazados: 2", salida.getvalue())
        self.assertIn("Comando desconocido: volar.", salida.getvalue())
        self.assertIn("El tiempo no puede ser negativo.", salida.getvalue())
        self.assertEqual(len(historial), 3)

    def test_mision_y_reporte_vacios(self):
        robot = Mock(spec=Robot)
        historial = []
        salida = io.StringIO()
        with redirect_stdout(salida):
            mi_tp02.ejecutar_mision(robot, [], historial)
            mi_tp02.generar_reporte(historial)
        self.assertEqual(robot.mock_calls, [])
        self.assertEqual(historial, [])
        self.assertIn("Total de comandos: 0", salida.getvalue())
        self.assertIn("Ejecutados: 0", salida.getvalue())
        self.assertIn("Rechazados: 0", salida.getvalue())

    def test_main_detiene_y_desconecta_si_falla_la_mision(self):
        robot = Mock(spec=Robot)
        with patch("mi_tp02.Robot", return_value=robot), \
             patch("mi_tp02.ejecutar_mision", side_effect=RuntimeError("Falla de conexion")):
            with self.assertRaises(RuntimeError):
                mi_tp02.main()
        robot.detenerse.assert_called_once_with()
        robot.desconectar.assert_called_once_with()

    def test_main_desconecta_aunque_falle_la_detencion_final(self):
        robot = Mock(spec=Robot)
        robot.detenerse.side_effect = RuntimeError("Falla al detener")
        with patch("mi_tp02.Robot", return_value=robot), \
             patch("mi_tp02.ejecutar_mision"), patch("mi_tp02.generar_reporte"):
            with self.assertRaises(RuntimeError):
                mi_tp02.main()
        robot.desconectar.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
