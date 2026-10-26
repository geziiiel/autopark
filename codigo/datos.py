import json
import re
from pathlib import Path

PATRON_TRADICIONAL = re.compile(r"^[A-Z]{3}[0-9]{3}$")
PATRON_MERCOSUR = re.compile(r"^[A-Z]{2}[0-9]{3}[A-Z]{2}$")
PATRON_HORA = re.compile(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$")

CAMPOS_TARIFA = ("precio_bloque_30min", "precio_hora_adicional", "tope_dia")


def normalizar_patente(valor):
    if not isinstance(valor, str):
        return None
    return "".join(valor.split()).upper()


def patente_valida(patente):
    if not patente:
        return False
    return bool(PATRON_TRADICIONAL.match(patente) or PATRON_MERCOSUR.match(patente))


def normalizar_tipo(valor):
    if not isinstance(valor, str):
        return None
    return valor.strip().lower()


def parsear_hora(valor):
    if not isinstance(valor, str):
        return None
    coincidencia = PATRON_HORA.match(valor.strip())
    if not coincidencia:
        return None
    return int(coincidencia.group(1)) * 60 + int(coincidencia.group(2))


def normalizar_hora(valor):
    minutos = parsear_hora(valor)
    if minutos is None:
        return None
    return "{:02d}:{:02d}".format(minutos // 60, minutos % 60)


def a_booleano(valor):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, int) and valor in (0, 1):
        return bool(valor)
    if isinstance(valor, str):
        texto = valor.strip().lower()
        if texto in ("si", "sí", "s", "true", "1", "yes", "y"):
            return True
        if texto in ("no", "n", "false", "0"):
            return False
    return None


def a_entero(valor):
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    if isinstance(valor, str):
        texto = valor.strip()
        if re.fullmatch(r"[+-]?\d+", texto):
            return int(texto)
    return None


def formatear_pesos(valor):
    return "$" + "{:,}".format(int(valor)).replace(",", ".")


def formatear_minutos(minutos):
    horas, resto = divmod(int(minutos), 60)
    if horas and resto:
        return "{} h {} min".format(horas, resto)
    if horas:
        return "{} h".format(horas)
    return "{} min".format(resto)


def cargar_json(ruta):
    ruta = Path(ruta)
    try:

        with ruta.open("r", encoding="utf-8-sig") as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        raise ValueError("No se encontro el archivo {}".format(ruta.name))
    except OSError as error:
        raise ValueError("No se pudo leer {}: {}".format(ruta.name, error))
    except json.JSONDecodeError as error:
        raise ValueError("El archivo {} no es un JSON valido (linea {}): {}".format(
            ruta.name, error.lineno, error.msg))


def cargar_tarifas(ruta):
    datos = cargar_json(ruta)
    if not isinstance(datos, dict):
        raise ValueError("tarifas.json debe tener un objeto en la raiz")

    configuracion = datos.get("configuracion", {})
    if not isinstance(configuracion, dict):
        raise ValueError("La seccion 'configuracion' debe ser un objeto")

    tarifas_brutas = datos.get("tarifas")
    if not isinstance(tarifas_brutas, dict) or not tarifas_brutas:
        raise ValueError("Falta la seccion 'tarifas' o esta vacia")

    tarifas = {}
    for tipo_bruto, valores in tarifas_brutas.items():
        tipo = normalizar_tipo(tipo_bruto)
        if not tipo:
            raise ValueError("Hay una categoria de tarifa sin nombre")
        if not isinstance(valores, dict):
            raise ValueError("La tarifa de '{}' debe ser un objeto".format(tipo_bruto))

        limpia = {}
        for campo in CAMPOS_TARIFA:
            numero = a_entero(valores.get(campo))
            if numero is None or numero < 0:
                raise ValueError("Tarifa '{}': '{}' falta o no es un numero valido".format(
                    tipo_bruto, campo))
            limpia[campo] = numero


        precio_lavado = a_entero(valores.get("precio_lavado", 0))
        if precio_lavado is None or precio_lavado < 0:
            raise ValueError("Tarifa '{}': 'precio_lavado' no es un numero valido".format(
                tipo_bruto))
        limpia["precio_lavado"] = precio_lavado

        tarifas[tipo] = limpia

    return {"configuracion": configuracion, "tarifas": tarifas}
