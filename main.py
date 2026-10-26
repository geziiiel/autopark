import csv
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent

sys.path.insert(0, str(BASE / "codigo"))

from datos import (
    a_entero,
    a_booleano,
    cargar_json,
    cargar_tarifas,
    formatear_minutos,
    formatear_pesos,
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
from tarifas import configuracion, liquidar, mapa_tarifas

DATOS = BASE / "datos"
SALIDAS = BASE / "salidas"
RUTA_LIQUIDACION = SALIDAS / "liquidacion.csv"
RUTA_RECHAZADOS = SALIDAS / "rechazados.csv"
RUTA_RANKING = SALIDAS / "liquidacion_ranking.csv"
RUTA_EXCEL = SALIDAS / "liquidacion.xlsx"
RUTA_MANUAL = SALIDAS / "liquidacion-manual.csv"

CAMPOS_NUMERICOS = (
    "dias",
    "minutos",
    "bloques_30",
    "horas_adicionales",
    "estacionamiento_base",
    "bonificacion",
    "estacionamiento",
    "lavado",
    "total",
)


def buscar_en_datos(nombre):
    for carpeta in (DATOS, BASE):
        ruta = carpeta / nombre
        if ruta.exists():
            return ruta
    return DATOS / nombre


def buscar_tarifas():
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


def leer_csv(ruta):
    ruta = Path(ruta)
    try:
        if not ruta.exists() or ruta.stat().st_size == 0:
            return []
        with ruta.open(newline="", encoding="utf-8-sig") as archivo:
            return list(csv.DictReader(archivo))
    except (OSError, csv.Error) as error:
        print("No se pudo leer {}: {}".format(ruta.name, error))
        return []


def convertir_liquidacion(fila):
    convertida = dict(fila)
    for campo in CAMPOS_NUMERICOS:
        convertida[campo] = a_entero(fila.get(campo)) or 0
    return convertida


def cargar_liquidaciones():
    filas = []
    for ruta, origen in ((RUTA_LIQUIDACION, "lote"), (RUTA_MANUAL, "manual")):
        for fila in leer_csv(ruta):
            convertida = convertir_liquidacion(fila)
            convertida["origen"] = origen
            filas.append(convertida)
    return filas


def formatear_tiempo(fila):
    if fila["dias"] > 0:
        return "{} dia(s)".format(fila["dias"])
    return formatear_minutos(fila["minutos"])


def historial_patente():
    print()
    print("--- HISTORIAL POR PATENTE ---")
    texto = input("Patente (Enter para volver): ").strip()
    if texto == "":
        return

    patente = normalizar_patente(texto)
    if not patente or not patente_valida(patente):
        print("Patente invalida. Formatos: ABC123 o AA123BB.")
        return

    filas = [fila for fila in cargar_liquidaciones()
             if fila.get("patente") == patente]
    if not filas:
        print("No hay movimientos registrados para {}.".format(patente))
        return

    cantidad = len(filas)
    total = sum(fila["total"] for fila in filas)
    minutos = sum(
        fila["dias"] * 1440 if fila["dias"] > 0 else fila["minutos"]
        for fila in filas)
    promedio = minutos / cantidad

    print()
    print("{:<22}{}".format("Patente:", patente))
    print("{:<22}{}".format("Ingresos registrados:", cantidad))
    print("{:<22}{}".format("Total acumulado:", formatear_pesos(total)))
    print("{:<22}{:.1f} min".format("Estadia promedio:", promedio).replace(".", ","))
    print()
    print("Detalle:")
    for fila in filas:
        print("  - {} | {} | {} | {} | lavado {} | {}".format(
            fila["origen"],
            fila.get("id", "-"),
            fila.get("tipo_vehiculo", "-"),
            formatear_tiempo(fila),
            fila.get("solicito_lavado", "-"),
            formatear_pesos(fila["total"])))
        fecha = fila.get("fecha_registro")
        if fecha:
            print("    Registrado: {}".format(fecha))


def ver_ranking():
    print()
    print("--- RANKING DEL ULTIMO LOTE ---")
    filas = [convertir_liquidacion(fila) for fila in leer_csv(RUTA_RANKING)]
    if not filas:
        print("No hay ranking. Procesa un lote con la opcion 2.")
        return

    print("Movimientos: {}".format(len(filas)))
    print()
    for puesto, fila in enumerate(filas[:10], 1):
        print("{:>2}. {:<10} {:<10} {:<10} {:>12}".format(
            puesto,
            fila.get("id", "-"),
            fila.get("patente", "-"),
            fila.get("tipo_vehiculo", "-"),
            formatear_pesos(fila["total"])))
    if len(filas) > 10:
        print("... y {} movimientos mas.".format(len(filas) - 10))


def ver_rechazados():
    print()
    print("--- MOVIMIENTOS RECHAZADOS ---")
    filas = leer_csv(RUTA_RECHAZADOS)
    if not filas:
        print("No hay rechazos guardados. Procesa un lote con la opcion 2.")
        return

    print("{:<10} {:<10} {:<12} {}".format(
        "ID", "PATENTE", "TIPO", "MOTIVO"))
    print("-" * 70)
    for fila in filas:
        print("{:<10} {:<10} {:<12} {}".format(
            fila.get("id", "-"),
            fila.get("patente", "-"),
            fila.get("tipo_vehiculo", "-"),
            fila.get("motivo", "-")))
    print()
    print("Total: {}".format(len(filas)))


def ver_estadisticas():
    print()
    print("--- ESTADISTICAS DEL ULTIMO LOTE ---")
    validos = [convertir_liquidacion(fila)
               for fila in leer_csv(RUTA_LIQUIDACION)]
    if not validos:
        print("No hay un lote procesado. Usa la opcion 2.")
        return

    rechazados = leer_csv(RUTA_RECHAZADOS)
    metricas = calcular_metricas(validos)
    imprimir_resumen(validos, rechazados)
    imprimir_metricas(metricas)


def ver_tarifas(tarifas):
    print()
    print("--- TARIFAS VIGENTES ---")
    config = configuracion(tarifas)
    print("Configuracion:")
    print("  Bloque inicial:      {} min".format(
        config.get("minutos_bloque_inicial", 30)))
    print("  Limite primer tramo: {} min".format(
        config.get("minutos_limite_primer_tramo", 120)))
    print("  Hora adicional:      {} min".format(
        config.get("minutos_hora_adicional", 60)))
    print("  Dia completo:        {} min".format(
        config.get("minutos_dia_completo", 1440)))
    print()
    print("Categorias:")
    mapa = mapa_tarifas(tarifas)
    for tipo in sorted(mapa):
        valores = mapa[tipo]
        print("  {}:".format(tipo.capitalize()))
        print("    Bloque de 30 min: {}".format(
            formatear_pesos(valores.get("precio_bloque_30min", 0))))
        print("    Hora adicional:   {}".format(
            formatear_pesos(valores.get("precio_hora_adicional", 0))))
        print("    Tope diario:      {}".format(
            formatear_pesos(valores.get("tope_dia", 0))))
        print("    Lavado:           {}".format(
            formatear_pesos(valores.get("precio_lavado", 0))))
    print()
    print("Bonificacion por lavado: hasta 4 bloques (120 min) de estacionamiento.")


def ver_ayuda():
    print()
    print("--- AYUDA, FORMATOS Y ARCHIVOS ---")
    print("Patentes: ABC123 (tradicional) o AA123BB (Mercosur).")
    print("Horas: HH:MM entre 00:00 y 23:59.")
    print("Dias: 0 = mismo dia; mayor a 0 = se cobra por dia completo.")
    print()
    print("Lote JSON: datos/movimientos.json")
    print("Obligatorios: id, patente, tipo_vehiculo.")
    print("Si dias es 0 o falta, entrada y salida son obligatorias.")
    print("solicito_lavado es opcional; si falta, vale false.")
    print("El id debe ser unico dentro del lote.")
    print()
    print("Archivos generados:")
    for ruta in (RUTA_LIQUIDACION, RUTA_RECHAZADOS, RUTA_RANKING,
                 RUTA_EXCEL, RUTA_MANUAL):
        try:
            if ruta.exists():
                print("  - {} ({:.1f} KB)".format(
                    ruta.name, ruta.stat().st_size / 1024))
            else:
                print("  - {} (no generado)".format(ruta.name))
        except OSError as error:
            print("  - {} (no se pudo leer: {})".format(ruta.name, error))


def pausar_y_limpiar():
    try:
        input("\nPresione Enter para volver al menu...")
    except EOFError:
        pass
    import os
    os.system("cls" if os.name == "nt" else "clear")


def mostrar_menu():
    print()
    print("=" * 62)
    print("      AUTOPARK - GESTION DE ESTACIONAMIENTO")
    print("=" * 62)
    print("  OPERACIONES")
    print("   1. Cobro manual en ventanilla")
    print("   2. Procesar lote de movimientos (JSON -> CSV + Excel)")
    print()
    print("  CONSULTAS")
    print("   3. Historial y totales por patente")
    print("   4. Ranking del ultimo lote")
    print("   5. Movimientos rechazados")
    print("   6. Estadisticas del ultimo lote")
    print()
    print("  CONFIGURACION Y AYUDA")
    print("   7. Ver tarifas vigentes")
    print("   8. Ayuda, formatos y archivos generados")
    print()
    print("   9. Salir")
    print("=" * 62)


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
            historial_patente()
        elif opcion == "4":
            ver_ranking()
        elif opcion == "5":
            ver_rechazados()
        elif opcion == "6":
            ver_estadisticas()
        elif opcion == "7":
            ver_tarifas(tarifas)
        elif opcion == "8":
            ver_ayuda()
        elif opcion == "9":
            print("Hasta luego.")
            break
        else:
            print("Opcion invalida. Ingresa un numero del 1 al 9.")
        pausar_y_limpiar()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nSaliendo...")
