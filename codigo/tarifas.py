from datos import a_entero


def mapa_tarifas(tarifas):
    if isinstance(tarifas, dict) and isinstance(tarifas.get("tarifas"), dict):
        return tarifas["tarifas"]
    return tarifas


def configuracion(tarifas):
    if isinstance(tarifas, dict) and isinstance(tarifas.get("configuracion"), dict):
        return tarifas["configuracion"]
    return {}


def _limites(tarifas):
    config = configuracion(tarifas)
    bloque = a_entero(config.get("minutos_bloque_inicial")) or 30
    limite = a_entero(config.get("minutos_limite_primer_tramo")) or 120
    hora = a_entero(config.get("minutos_hora_adicional")) or 60
    return bloque, limite, hora


def _tarifa(tarifas, tipo_vehiculo):
    return mapa_tarifas(tarifas)[tipo_vehiculo]


def calcular_estacionamiento_recursivo(minutos_restantes, tipo_vehiculo, tarifas):
    if minutos_restantes <= 0:
        return 0

    bloque, limite, hora = _limites(tarifas)
    tarifa = _tarifa(tarifas, tipo_vehiculo)

    if minutos_restantes <= limite:
        return tarifa["precio_bloque_30min"] + calcular_estacionamiento_recursivo(
            minutos_restantes - bloque, tipo_vehiculo, tarifas)

    return (calcular_estacionamiento_recursivo(limite, tipo_vehiculo, tarifas)
            + _calcular_horas_excedentes(minutos_restantes - limite,
                                         tarifa["precio_hora_adicional"], hora))


def _calcular_horas_excedentes(minutos, precio_hora, minutos_hora):
    if minutos <= 0:
        return 0
    return precio_hora + _calcular_horas_excedentes(minutos - minutos_hora,
                                                    precio_hora, minutos_hora)


def liquidar(dias, minutos, tipo_vehiculo, solicito_lavado, tarifas):
    tarifa = _tarifa(tarifas, tipo_vehiculo)
    bloque, limite, hora = _limites(tarifas)
    tope = tarifa["tope_dia"]
    precio_lavado = tarifa["precio_lavado"]

    if dias > 0:
        estacionamiento = dias * tope
        return {
            "dias": dias,
            "minutos": 0,
            "bloques_30": 0,
            "horas_adicionales": 0,
            "estacionamiento_base": estacionamiento,
            "bonificacion": 0,
            "estacionamiento": estacionamiento,
            "lavado": precio_lavado if solicito_lavado else 0,
            "total": estacionamiento + (precio_lavado if solicito_lavado else 0),
            "tope_aplicado": False,
        }

    base = calcular_estacionamiento_recursivo(minutos, tipo_vehiculo, tarifas)
    tope_aplicado = base > tope
    base_con_tope = min(base, tope)

    if minutos <= limite:
        bloques = (minutos + bloque - 1) // bloque
        horas = 0
    else:
        bloques = (limite + bloque - 1) // bloque
        horas = (minutos - limite + hora - 1) // hora

    if solicito_lavado:
        if minutos <= limite:

            bonificacion = base_con_tope
            estacionamiento = 0
        else:

            bonificacion = min(bloques * tarifa["precio_bloque_30min"], base_con_tope)
            estacionamiento = base_con_tope - bonificacion
        costo_lavado = precio_lavado
    else:
        bonificacion = 0
        estacionamiento = base_con_tope
        costo_lavado = 0

    return {
        "dias": 0,
        "minutos": minutos,
        "bloques_30": bloques,
        "horas_adicionales": horas,
        "estacionamiento_base": base,
        "bonificacion": bonificacion,
        "estacionamiento": estacionamiento,
        "lavado": costo_lavado,
        "total": estacionamiento + costo_lavado,
        "tope_aplicado": tope_aplicado,
    }
