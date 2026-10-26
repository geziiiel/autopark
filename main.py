"""Sistema de Gestion de Estacionamiento AutoPark.

Trabajo Practico N.º 2 - Programacion I / II.
"""

import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
# Los modulos del programa estan en codigo/; se agrega al path antes de importar.
sys.path.insert(0, str(BASE / "codigo"))

from datos import (
    a_entero,
    a_booleano,
    cargar_json,
    cargar_tarifas,
    normalizar_hora,
    normalizar_patente,
    normalizar_tipo,
    parsear_hora,
    patente_valida,
)
from procesamiento import procesar_lote
from reportes import (
    agregar_liquidacion_manual,
    calcular_metricas,
    escribir_excel,
    escribir_liquidacion,
    escribir_ranking,
    escribir_rechazados,
    imprimir_desglose,
    imprimir_metricas,
    imprimir_resumen,
)
from tarifas import liquidar, mapa_tarifas

DATOS = BASE / "datos"
SALIDAS = BASE / "salidas"
RUTA_LIQUIDACION = SALIDAS / "liquidacion.csv"
RUTA_RECHAZADOS = SALIDAS / "rechazados.csv"
RUTA_RANKING = SALIDAS / "liquidacion_ranking.csv"
RUTA_EXCEL = SALIDAS / "liquidacion.xlsx"
RUTA_MANUAL = SALIDAS / "liquidacion-manual.csv"


def buscar_en_datos(nombre):
    """Busca un archivo en datos/ y, por compatibilidad, en la raiz."""
    for carpeta in (DATOS, BASE):
        ruta = carpeta / nombre
        if ruta.exists():
            return ruta
    return DATOS / nombre


def buscar_tarifas():
    """Acepta tarifas.json (enunciado) o tarifa.json (nombre alternativo)."""
    for nombre in ("tarifas.json", "tarifa.json"):
        ruta = buscar_en_datos(nombre)
        if ruta.exists():
            return ruta
    return DATOS / "tarifas.json"


def pedir_patente():
    while True:
        texto = input("Patente (Enter para cancelar): ").strip()
        if texto == "":
            return None
        patente = normalizar_patente(texto)
        if patente and patente_valida(patente):
            return patente
        print("Patente invalida. Formatos: ABC123 (tradicional) o AA123BB (Mercosur).")


def pedir_tipo(tarifas):
    tipos = sorted(mapa_tarifas(tarifas))
    while True:
        texto = input("Tipo de vehiculo ({}): ".format(" / ".join(tipos)))
        tipo = normalizar_tipo(texto)
        if tipo in tipos:
            return tipo
        print("Tipo invalido. Opciones: {}.".format(", ".join(tipos)))


def pedir_dias():
    while True:
        texto = input("¿Cuantos dias pasaron? (0 si se retira en el mismo dia): ")
        dias = a_entero(texto)
        if dias is not None and dias >= 0:
            return dias
        print("Ingresa un numero entero mayor o igual a 0.")


def pedir_hora(mensaje):
    while True:
        texto = input(mensaje).strip()
        hora = normalizar_hora(texto)
        if hora is not None:
            return hora
        print("Hora invalida. Usa el formato HH:MM (por ejemplo 08:30).")


def pedir_lavado():
    while True:
        texto = input("¿Solicito lavado? (S/N): ")
        lavado = a_booleano(texto)
        if lavado is not None:
            return lavado
        print("Responde S o N.")


def cobro_manual(tarifas):
    print()
    print("--- COBRO MANUAL EN VENTANILLA ---")

    patente = pedir_patente()
    if patente is None:
        print("Cobro cancelado.")
        return

    tipo_vehiculo = pedir_tipo(tarifas)
    dias = pedir_dias()

    entrada = ""
    salida = ""
    minutos = 0

    if dias == 0:
        entrada = pedir_hora("Hora de entrada (HH:MM): ")
        while True:
            salida = pedir_hora("Hora de salida (HH:MM): ")
            minutos = parsear_hora(salida) - parsear_hora(entrada)
            if minutos < 0:
                print("La salida no puede ser anterior a la entrada.")
                continue
            if minutos == 0:
                print("La salida no puede ser igual a la entrada.")
                continue
            break
    else:
        print("Se liquida por {} dia(s) completo(s), sin pedir hora de salida.".format(dias))

    solicito_lavado = pedir_lavado()
    liquidacion = liquidar(dias, minutos, tipo_vehiculo, solicito_lavado, tarifas)

    imprimir_desglose(patente, tipo_vehiculo, liquidacion)

    ahora = datetime.now()
    registro = {
        "id": "MAN-{}{:03d}".format(
            ahora.strftime("%Y%m%d%H%M%S"), ahora.microsecond // 1000),
        "fecha_registro": ahora.strftime("%Y-%m-%d %H:%M:%S"),
        "patente": patente,
        "tipo_vehiculo": tipo_vehiculo,
        "entrada": entrada,
        "salida": salida,
        "dias": liquidacion["dias"],
        "minutos": liquidacion["minutos"],
        "bloques_30": liquidacion["bloques_30"],
        "horas_adicionales": liquidacion["horas_adicionales"],
        "estacionamiento_base": liquidacion["estacionamiento_base"],
        "bonificacion": liquidacion["bonificacion"],
        "estacionamiento": liquidacion["estacionamiento"],
        "solicito_lavado": "S" if solicito_lavado else "N",
        "lavado": liquidacion["lavado"],
        "total": liquidacion["total"],
        "tope_aplicado": "S" if liquidacion["tope_aplicado"] else "N",
    }

    try:
        agregar_liquidacion_manual(registro, RUTA_MANUAL)
    except OSError as error:
        print()
        print("No se pudo guardar el registro: {}".format(error))
        print("Cerrá liquidacion-manual.csv si está abierto en Excel.")
        return

    print()
    print("Registro guardado en {}.".format(RUTA_MANUAL.name))

def procesar_lote_opcion(tarifas):
    print()
    print("--- PROCESAMIENTO POR LOTE ---")
    ruta_movimientos = buscar_en_datos("movimientos.json")
    try:
        datos = cargar_json(ruta_movimientos)
        validos, rechazados = procesar_lote(datos, tarifas)
    except ValueError as error:
        print("Error: {}".format(error))
        return

    fecha_operacion = datos.get("fecha_operacion") if isinstance(datos, dict) else None

    try:
        escribir_liquidacion(validos, RUTA_LIQUIDACION)
        escribir_rechazados(rechazados, RUTA_RECHAZADOS)
        escribir_ranking(validos, RUTA_RANKING)
    except OSError as error:
        print("No se pudieron escribir los CSV: {}".format(error))
        print("Cerrá los archivos si están abiertos en Excel y volvé a intentar.")
        return

    metricas = calcular_metricas(validos)
    imprimir_resumen(validos, rechazados)
    imprimir_metricas(metricas)

    excel_generado = True
    try:
        escribir_excel(validos, rechazados, metricas, RUTA_EXCEL,
                       fecha_operacion)
    except ImportError as error:
        excel_generado = False
        print()
        print("Aviso: no se genero {}: {}".format(RUTA_EXCEL.name, error))
    except OSError as error:
        excel_generado = False
        print()
        print("No se pudo escribir {}: {}".format(RUTA_EXCEL.name, error))
        print("Cerrá el archivo si está abierto en Excel y volvé a intentar.")

    print()
    print("Archivos generados:")
    print("  - {}".format(RUTA_LIQUIDACION.name))
    print("  - {}".format(RUTA_RECHAZADOS.name))
    print("  - {} (desafio nivel 1 N.º 3)".format(RUTA_RANKING.name))
    if excel_generado:
        print("  - {} (hojas ordenadas + recuadro de estadisticas)".format(
            RUTA_EXCEL.name))


def mostrar_menu():
    print()
    print("=" * 50)
    print("   SISTEMA DE GESTION DE ESTACIONAMIENTO AUTOPARK")
    print("=" * 50)
    print("1. Registrar / Consultar cobro manual")
    print("2. Procesar lote de movimientos (JSON -> CSV + Excel)")
    print("3. Salir")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        SALIDAS.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        print("No se pudo crear la carpeta de salidas: {}".format(error))
        return

    ruta_tarifas = buscar_tarifas()
    try:
        tarifas = cargar_tarifas(ruta_tarifas)
    except ValueError as error:
        print("No se pudieron cargar las tarifas: {}".format(error))
        return

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            cobro_manual(tarifas)
        elif opcion == "2":
            procesar_lote_opcion(tarifas)
        elif opcion == "3":
            print("Hasta luego.")
            break
        else:
            print("Opcion invalida. Ingresa 1, 2 o 3.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nSaliendo...")
