"""Validacion de cada movimiento del lote.

Siempre se devuelve el primer motivo de rechazo encontrado, en el orden en que
los pide el enunciado, para que el CSV se entienda de una sola lectura.
"""

from datos import (
    a_booleano,
    a_entero,
    normalizar_hora,
    normalizar_patente,
    normalizar_tipo,
    parsear_hora,
    patente_valida,
)
from tarifas import mapa_tarifas


def _texto(valor):
    return "" if valor is None else str(valor)


def validar_movimiento(movimiento, tarifas, ids_vistos):
    """Devuelve (movimiento_normalizado, None) o (None, motivo_del_rechazo)."""
    if not isinstance(movimiento, dict):
        return None, "Movimiento invalido (no es un objeto)"

    id_movimiento = _texto(movimiento.get("id")).strip()
    if not id_movimiento:
        return None, "ID vacio"
    if id_movimiento in ids_vistos:
        return None, "ID repetido ({})".format(id_movimiento)

    patente_cruda = movimiento.get("patente")
    patente = normalizar_patente(patente_cruda)
    if not patente_valida(patente):
        return None, "Patente invalida ({})".format(_texto(patente_cruda))

    tipo_crudo = movimiento.get("tipo_vehiculo")
    tipo = normalizar_tipo(tipo_crudo)
    if tipo not in mapa_tarifas(tarifas):
        return None, "Tipo de vehiculo invalido ({})".format(_texto(tipo_crudo))

    dias_crudos = movimiento.get("dias", 0)
    dias = a_entero(dias_crudos)
    if dias is None or dias < 0:
        return None, "Dias invalidos ({})".format(_texto(dias_crudos))

    entrada = ""
    salida = ""
    minutos = 0

    if dias == 0:
        entrada = normalizar_hora(movimiento.get("entrada"))
        if entrada is None:
            return None, "Hora de entrada invalida ({})".format(
                _texto(movimiento.get("entrada")))

        salida = normalizar_hora(movimiento.get("salida"))
        if salida is None:
            return None, "Hora de salida invalida ({})".format(
                _texto(movimiento.get("salida")))

        minutos = parsear_hora(salida) - parsear_hora(entrada)
        if minutos < 0:
            return None, "Salida anterior a la entrada"
        if minutos == 0:
            return None, "Duracion cero"

    if "solicito_lavado" in movimiento:
        lavado = a_booleano(movimiento.get("solicito_lavado"))
        if lavado is None:
            return None, "Valor de lavado invalido ({})".format(
                _texto(movimiento.get("solicito_lavado")))
    else:
        lavado = False

    return {
        "id": id_movimiento,
        "patente": patente,
        "tipo_vehiculo": tipo,
        "dias": dias,
        "entrada": entrada,
        "salida": salida,
        "minutos": minutos,
        "solicito_lavado": lavado,
    }, None
