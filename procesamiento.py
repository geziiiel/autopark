"""Procesamiento del lote de movimientos."""

from tarifas import liquidar
from validaciones import validar_movimiento


def procesar_lote(datos, tarifas):
    """Recorre los movimientos, valida y liquida.

    Devuelve (validos, rechazados). Cada valido es un diccionario listo para
    el CSV, con el desglose de la liquidacion ya calculado.
    """
    if not isinstance(datos, dict):
        raise ValueError("movimientos.json debe tener un objeto en la raiz")

    movimientos = datos.get("movimientos")
    if not isinstance(movimientos, list):
        raise ValueError("El JSON no tiene una lista llamada 'movimientos'")

    validos = []
    rechazados = []
    ids_vistos = set()

    for movimiento in movimientos:
        normalizado, motivo = validar_movimiento(movimiento, tarifas, ids_vistos)

        if motivo is not None:
            rechazados.append({
                "id": _texto(movimiento.get("id")) if isinstance(movimiento, dict) else "",
                "patente": _texto(movimiento.get("patente")) if isinstance(movimiento, dict) else "",
                "tipo_vehiculo": _texto(movimiento.get("tipo_vehiculo")) if isinstance(movimiento, dict) else "",
                "motivo": motivo,
            })
            continue

        ids_vistos.add(normalizado["id"])
        liquidacion = liquidar(
            normalizado["dias"],
            normalizado["minutos"],
            normalizado["tipo_vehiculo"],
            normalizado["solicito_lavado"],
            tarifas,
        )

        validos.append({
            "id": normalizado["id"],
            "patente": normalizado["patente"],
            "tipo_vehiculo": normalizado["tipo_vehiculo"],
            "entrada": normalizado["entrada"],
            "salida": normalizado["salida"],
            "dias": liquidacion["dias"],
            "minutos": liquidacion["minutos"],
            "bloques_30": liquidacion["bloques_30"],
            "horas_adicionales": liquidacion["horas_adicionales"],
            "estacionamiento_base": liquidacion["estacionamiento_base"],
            "bonificacion": liquidacion["bonificacion"],
            "estacionamiento": liquidacion["estacionamiento"],
            "lavado": liquidacion["lavado"],
            "total": liquidacion["total"],
            "tope_aplicado": "S" if liquidacion["tope_aplicado"] else "N",
        })

    return validos, rechazados


def _texto(valor):
    return "" if valor is None else str(valor)
