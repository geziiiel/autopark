"""Escritura de los CSV y reportes por consola."""

import csv
from pathlib import Path

from datos import formatear_minutos, formatear_pesos

CAMPOS_LIQUIDACION = [
    "id", "patente", "tipo_vehiculo", "entrada", "salida", "dias", "minutos",
    "bloques_30", "horas_adicionales", "estacionamiento_base", "bonificacion",
    "estacionamiento", "lavado", "total", "tope_aplicado",
]

CAMPOS_RECHAZADOS = ["id", "patente", "tipo_vehiculo", "motivo"]

CAMPOS_MANUAL = ["id", "fecha_registro"] + [
    campo for campo in CAMPOS_LIQUIDACION if campo != "id"
]


def escribir_csv(ruta, campos, filas):
    """Escribe un CSV completo (borra el anterior)."""
    with Path(ruta).open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        for fila in filas:
            escritor.writerow({campo: fila.get(campo, "") for campo in campos})


def escribir_liquidacion(validos, ruta):
    escribir_csv(ruta, CAMPOS_LIQUIDACION, validos)


def escribir_rechazados(rechazados, ruta):
    escribir_csv(ruta, CAMPOS_RECHAZADOS, rechazados)


def escribir_ranking(validos, ruta):
    """Desafio nivel 1 N.º 3: mismos registros, de mayor a menor total."""
    ordenados = sorted(validos, key=lambda fila: (-fila["total"], fila["patente"]))
    escribir_csv(ruta, CAMPOS_LIQUIDACION, ordenados)


def agregar_liquidacion_manual(registro, ruta):
    """Agrega una fila a liquidacion-manual.csv sin borrar lo anterior."""
    ruta = Path(ruta)
    existe = ruta.exists() and ruta.stat().st_size > 0

    if existe:
        archivo = ruta.open("a", newline="", encoding="utf-8")
    else:
        # utf-8-sig solo al crear: si se usa al agregar, mete un BOM en el medio.
        archivo = ruta.open("w", newline="", encoding="utf-8-sig")

    with archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS_MANUAL)
        if not existe:
            escritor.writeheader()
        escritor.writerow({campo: registro.get(campo, "") for campo in CAMPOS_MANUAL})


def imprimir_desglose(patente, tipo_vehiculo, liquidacion):
    print()
    print("=" * 52)
    print("LIQUIDACION")
    print("=" * 52)
    print("Patente:  {}".format(patente))
    print("Tipo:     {}".format(tipo_vehiculo))

    if liquidacion["dias"] > 0:
        print("Tiempo:   {} dia(s) completo(s)".format(liquidacion["dias"]))
    else:
        detalle = "{} ({} bloques de 30 min".format(
            formatear_minutos(liquidacion["minutos"]), liquidacion["bloques_30"])
        if liquidacion["horas_adicionales"]:
            detalle += " + {} hora(s) adicional(es)".format(
                liquidacion["horas_adicionales"])
        detalle += ")"
        print("Tiempo:   " + detalle)

    print("Estacionamiento base:      {:>12}".format(
        formatear_pesos(liquidacion["estacionamiento_base"])))
    if liquidacion["bonificacion"]:
        print("Bonificacion por lavado:  {:>12}".format(
            "-" + formatear_pesos(liquidacion["bonificacion"])))
    print("Estacionamiento a cobrar:  {:>12}".format(
        formatear_pesos(liquidacion["estacionamiento"])))
    print("Lavado:                    {:>12}".format(
        formatear_pesos(liquidacion["lavado"])))
    if liquidacion["tope_aplicado"]:
        print("(se aplico el tope diario de la categoria)")
    print("-" * 52)
    print("TOTAL A PAGAR:             {:>12}".format(
        formatear_pesos(liquidacion["total"])))
    print("=" * 52)


def imprimir_resumen(validos, rechazados):
    total = sum(fila["total"] for fila in validos)
    print()
    print("=" * 52)
    print("RESUMEN DEL LOTE")
    print("=" * 52)
    print("Procesados:      {}".format(len(validos)))
    print("Rechazados:      {}".format(len(rechazados)))
    print("Total recaudado: {}".format(formatear_pesos(total)))

    if rechazados:
        print()
        print("Rechazos por motivo:")
        conteo = {}
        for fila in rechazados:
            conteo[fila["motivo"]] = conteo.get(fila["motivo"], 0) + 1
        for motivo in sorted(conteo):
            print("  - {}: {}".format(motivo, conteo[motivo]))


def calcular_metricas(validos):
    """Desafio nivel 1 N.º 2: datos para el reporte ejecutivo."""
    recaudado = {}
    cantidad = {}
    minutos = {}
    lavados = 0

    for fila in validos:
        tipo = fila["tipo_vehiculo"]
        recaudado[tipo] = recaudado.get(tipo, 0) + fila["total"]
        cantidad[tipo] = cantidad.get(tipo, 0) + 1

        # Las estadias prolongadas se miden en dias: se pasan a minutos para
        # que el promedio sea comparable con las del mismo dia.
        duracion = fila["dias"] * 1440 if fila["dias"] > 0 else fila["minutos"]
        minutos[tipo] = minutos.get(tipo, 0) + duracion

        if fila["lavado"] > 0:
            lavados += 1

    promedios = {tipo: minutos[tipo] / cantidad[tipo] for tipo in cantidad}
    mas_rentable = max(recaudado, key=recaudado.get) if recaudado else None
    porcentaje_lavado = (lavados / len(validos) * 100) if validos else 0

    return {
        "recaudado": recaudado,
        "cantidad": cantidad,
        "promedios": promedios,
        "mas_rentable": mas_rentable,
        "porcentaje_lavado": porcentaje_lavado,
        "lavados": lavados,
        "total_vehiculos": len(validos),
    }


def imprimir_metricas(metricas):
    print()
    print("-" * 52)
    print("METRICAS DEL NEGOCIO (desafio nivel 1 N.º 2)")
    print("-" * 52)

    if metricas["mas_rentable"] is None:
        print("No hay movimientos validos para calcular metricas.")
        return

    tipo = metricas["mas_rentable"]
    print("Categoria mas rentable: {} ({})".format(
        tipo, formatear_pesos(metricas["recaudado"][tipo])))
    print("Vehiculos con lavado:   {} de {} ({:.1f}%)".format(
        metricas["lavados"], metricas["total_vehiculos"],
        metricas["porcentaje_lavado"]))
    print("Estadia promedio por categoria:")
    for categoria in sorted(metricas["promedios"]):
        print("  - {}: {:.1f} min".format(
            categoria, metricas["promedios"][categoria]))

    print()
    print("Recaudacion por categoria:")
    for categoria in sorted(metricas["recaudado"]):
        print("  - {}: {} ({} vehiculos)".format(
            categoria,
            formatear_pesos(metricas["recaudado"][categoria]),
            metricas["cantidad"][categoria]))
