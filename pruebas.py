"""Pruebas del sistema AutoPark.

Se corren con:  python pruebas.py
No hace falta instalar nada: son assert comunes.
"""

from pathlib import Path

from datos import cargar_json, cargar_tarifas, normalizar_patente, patente_valida
from procesamiento import procesar_lote
from reportes import calcular_metricas
from tarifas import calcular_estacionamiento_recursivo, liquidar
from validaciones import validar_movimiento

BASE = Path(__file__).resolve().parent


def probar_patentes():
    assert patente_valida(normalizar_patente("ABC123"))
    assert patente_valida(normalizar_patente("AA123BB"))
    assert patente_valida(normalizar_patente(" BF 901 GG "))
    assert not patente_valida(normalizar_patente("PATENTE99"))
    assert not patente_valida(normalizar_patente("A123BC"))
    assert not patente_valida(normalizar_patente("ABC-123"))
    assert not patente_valida(normalizar_patente(""))
    assert not patente_valida(normalizar_patente(None))


def probar_recursion(tarifas):
    # auto: bloque $700, hora adicional $1200
    assert calcular_estacionamiento_recursivo(0, "auto", tarifas) == 0
    assert calcular_estacionamiento_recursivo(1, "auto", tarifas) == 700
    assert calcular_estacionamiento_recursivo(30, "auto", tarifas) == 700
    assert calcular_estacionamiento_recursivo(31, "auto", tarifas) == 1400
    assert calcular_estacionamiento_recursivo(120, "auto", tarifas) == 2800
    assert calcular_estacionamiento_recursivo(121, "auto", tarifas) == 4000
    assert calcular_estacionamiento_recursivo(135, "auto", tarifas) == 4000
    assert calcular_estacionamiento_recursivo(180, "auto", tarifas) == 4000
    assert calcular_estacionamiento_recursivo(181, "auto", tarifas) == 5200

    # camioneta: bloque $1000, hora adicional $1800
    assert calcular_estacionamiento_recursivo(135, "camioneta", tarifas) == 5800


def probar_lavado(tarifas):
    # 60 minutos con lavado: se bonifica todo el estacionamiento.
    liq = liquidar(0, 60, "auto", True, tarifas)
    assert liq["estacionamiento"] == 0
    assert liq["bonificacion"] == 1400
    assert liq["total"] == 5000

    # 135 minutos con lavado: paga lavado + 1 hora excedente.
    liq = liquidar(0, 135, "auto", True, tarifas)
    assert liq["bonificacion"] == 2800
    assert liq["estacionamiento"] == 1200
    assert liq["total"] == 6200

    # 135 minutos sin lavado: paga los 4 bloques + 1 hora.
    liq = liquidar(0, 135, "auto", False, tarifas)
    assert liq["total"] == 4000

    # Estadía prolongada: 2 días + lavado.
    liq = liquidar(2, 0, "auto", True, tarifas)
    assert liq["estacionamiento"] == 32000
    assert liq["total"] == 37000


def probar_tope(tarifas):
    tarifas_chicas = {
        "configuracion": tarifas["configuracion"],
        "tarifas": {
            "auto": dict(tarifas["tarifas"]["auto"], tope_dia=1000),
        },
    }
    liq = liquidar(0, 120, "auto", False, tarifas_chicas)
    assert liq["estacionamiento"] == 1000
    assert liq["tope_aplicado"] is True

    liq = liquidar(0, 60, "auto", True, tarifas_chicas)
    assert liq["estacionamiento"] == 0
    assert liq["total"] == 5000


def probar_validaciones(tarifas):
    base = {
        "id": "X1", "patente": "AA123BB", "tipo_vehiculo": "auto",
        "entrada": "08:00", "salida": "09:00", "solicito_lavado": False,
    }

    def motivo(cambios):
        movimiento = dict(base)
        movimiento.update(cambios)
        return validar_movimiento(movimiento, tarifas, set())[1]

    assert motivo({"patente": "PATENTE99"}) == "Patente invalida (PATENTE99)"
    assert motivo({"patente": " BF 901 GG "}) is None
    assert motivo({"tipo_vehiculo": "tractor"}) is not None
    assert motivo({"tipo_vehiculo": "  MOTO  "}) is None
    assert motivo({"entrada": "18:00", "salida": "15:00"}) == "Salida anterior a la entrada"
    assert motivo({"entrada": "08:00", "salida": "08:00"}) == "Duracion cero"
    assert motivo({"entrada": "25:00"}) is not None
    assert motivo({"salida": "ocho"}) is not None
    assert motivo({"id": ""}) == "ID vacio"
    assert motivo({"id": None}) == "ID vacio"
    assert motivo({"id": "   "}) == "ID vacio"
    assert motivo({"patente": None}) == "Patente invalida (vacio)"
    assert motivo({"solicito_lavado": "tal vez"}) is not None
    assert motivo({"dias": -1}) is not None

    # Días > 0 no piden hora de salida.
    prolongada = {
        "id": "X2", "patente": "ABC123", "tipo_vehiculo": "auto",
        "dias": 3, "solicito_lavado": True,
    }
    normalizado, error = validar_movimiento(prolongada, tarifas, set())
    assert error is None and normalizado["dias"] == 3

    # ID repetido: la segunda vez se rechaza.
    ids = {"X1"}
    assert validar_movimiento(base, tarifas, ids)[1] == "ID repetido (X1)"


def probar_lote(tarifas):
    datos = cargar_json(BASE / "movimientos.json")
    validos, rechazados = procesar_lote(datos, tarifas)

    assert len(validos) == 30, "Se esperaban 30 validos y hay {}".format(len(validos))
    assert len(rechazados) == 3, "Se esperaban 3 rechazados y hay {}".format(len(rechazados))
    assert sum(fila["total"] for fila in validos) == 129000

    por_id = {fila["id"]: fila for fila in validos}
    assert por_id["MOV001"]["total"] == 700
    assert por_id["MOV004"]["total"] == 5200
    assert por_id["MOV010"]["total"] == 12900
    assert por_id["MOV014"]["total"] == 8600
    assert por_id["MOV017"]["total"] == 4000
    assert por_id["MOV030"]["total"] == 9400

    motivos = {fila["id"]: fila["motivo"] for fila in rechazados}
    assert motivos["MOV031"] == "Salida anterior a la entrada"
    assert motivos["MOV032"].startswith("Tipo de vehiculo invalido")
    assert motivos["MOV033"].startswith("Patente invalida")

    metricas = calcular_metricas(validos)
    assert metricas["mas_rentable"] == "camioneta"
    assert metricas["recaudado"]["camioneta"] == 64900
    assert metricas["recaudado"]["auto"] == 49500
    assert metricas["recaudado"]["moto"] == 14600
    assert metricas["lavados"] == 13
    assert round(metricas["porcentaje_lavado"], 1) == 43.3
    assert round(metricas["promedios"]["auto"], 1) == 113.0
    assert round(metricas["promedios"]["moto"], 1) == 66.9
    assert round(metricas["promedios"]["camioneta"], 1) == 138.3


def main():
    tarifas = cargar_tarifas(BASE / "tarifas.json")

    probar_patentes()
    probar_recursion(tarifas)
    probar_lavado(tarifas)
    probar_tope(tarifas)
    probar_validaciones(tarifas)
    probar_lote(tarifas)

    print("Todas las pruebas pasaron: 6 grupos OK.")


if __name__ == "__main__":
    main()
