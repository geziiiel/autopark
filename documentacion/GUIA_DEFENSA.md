# Guía de defensa — AutoPark

> **Objetivo:** explicar el código con tus palabras, sin memorizar cada línea.
>
> **Regla de oro:** para cada función decí **qué recibe**, **qué hace** y **qué
> devuelve**. Si te señalan una línea, primero ubicá la función y después
> explicá esa línea.

Explicar “línea por línea” no significa recitar 600 líneas: significa que, si te
preguntan por una línea, sabés qué hace, con qué variables trabaja y por qué está
ahí. Las tablas de esta guía agrupan líneas consecutivas que cumplen la misma
función.

---

## 1. La idea general en 30 segundos

AutoPark lee dos archivos JSON:

- `datos/tarifas.json` → precios y configuración.
- `datos/movimientos.json` → movimientos del día.

Después:

1. valida cada movimiento;
2. calcula el estacionamiento con una función recursiva;
3. aplica el tope diario y el beneficio de lavado;
4. genera los CSV y el Excel;
5. muestra un resumen y las métricas del negocio.

`main.py` es la puerta de entrada. El resto del código está en `codigo/`.

---

## 2. Mapa de archivos

| Archivo | Responsabilidad | Frase corta para la defensa |
|---|---|---|
| `main.py` | Menú, cobro manual y coordinación | “Es el orquestador: pide datos, llama a los módulos y muestra resultados.” |
| `codigo/datos.py` | Leer JSON, normalizar y validar formatos | “Acá no se calcula nada: se limpian y validan los datos de entrada.” |
| `codigo/validaciones.py` | Decidir si un movimiento se acepta o se rechaza | “Devuelve el primer motivo de rechazo, en el orden del enunciado.” |
| `codigo/tarifas.py` | Calcular el cobro | “Acá está la recursión y la liquidación final.” |
| `codigo/procesamiento.py` | Recorrer el lote | “Valida, liquida y arma las filas que van a los CSV.” |
| `codigo/reportes.py` | CSV, Excel, métricas y resúmenes | “Separa la salida del cálculo: si falla el Excel, los CSV ya están hechos.” |
| `codigo/pruebas.py` | Probar todo con `assert` | “Son pruebas automáticas; si algo se rompe, falla acá.” |
| `datos/` | JSON de entrada | “Datos que puede reemplazar el profesor.” |
| `salidas/` | CSV y Excel generados | “Resultados del programa.” |

---

## 3. El recorrido de una ejecución

Cuando escribís `python main.py` pasa esto:

1. Python ejecuta `main.py`.
2. Se define `BASE` y se agrega `codigo/` al `sys.path`.
3. Se importan los módulos (`datos`, `tarifas`, `validaciones`, etc.).
4. `main()` crea la carpeta `salidas/` si no existe.
5. `buscar_tarifas()` encuentra `datos/tarifas.json`.
6. `cargar_tarifas()` valida los precios.
7. Aparece el menú con nueve opciones agrupadas.
8. Si elegís **1** → `cobro_manual()`.
9. Si elegís **2** → `procesar_lote_opcion()`.
10. Si elegís **3 a 8** → consultas, tarifas y ayuda (`historial_patente()`, `ver_ranking()`, `ver_rechazados()`, `ver_estadisticas()`, `ver_tarifas()`, `ver_ayuda()`).
11. Si elegís **9** → termina.
12. Después de cada acción, `pausar_y_limpiar()` espera Enter y limpia la pantalla para volver al menú.

### Opción 2, paso a paso

```text
procesar_lote_opcion()
  → buscar_en_datos("movimientos.json")
  → cargar_json()
  → procesar_lote()
       → validar_movimiento() por cada movimiento
       → liquidar() por cada movimiento válido
  → escribir_liquidacion()
  → escribir_rechazados()
  → escribir_ranking()
  → calcular_metricas()
  → imprimir_resumen()
  → imprimir_metricas()
  → escribir_excel()
```

### Opción 1, paso a paso

```text
cobro_manual()
  → pedir_patente()
  → pedir_tipo()
  → pedir_dias()
  → pedir_hora() (solo si dias == 0)
  → pedir_lavado()
  → liquidar()
  → imprimir_desglose()
  → agregar_liquidacion_manual()
```

---

## 4. Explicación por archivo y por líneas

### 4.1. `main.py`

| Líneas | Qué explicar |
|---|---|
| 1-8 | Imports. `BASE` es la carpeta del proyecto. `sys.path.insert` agrega `codigo/` para que funcionen los imports. |
| 10-35 | Se importan solo las funciones que usa `main.py`. Cada módulo tiene una responsabilidad. |
| 37-43 | Rutas de datos y salidas. `DATOS` apunta a `datos/`; `SALIDAS` a `salidas/`. |
| 45-55 | `CAMPOS_NUMERICOS`: campos que se convierten a entero al leer los CSV. |
| 58-63 | `buscar_en_datos()` busca primero en `datos/` y, por compatibilidad, en la raíz. |
| 66-71 | `buscar_tarifas()` acepta `tarifas.json` o `tarifa.json`. |
| 74-82 | `pedir_patente()`: pide hasta que sea válida; Enter cancela. |
| 85-92 | `pedir_tipo()`: muestra las categorías disponibles y valida contra las tarifas. |
| 95-101 | `pedir_dias()`: entero mayor o igual a 0. |
| 104-110 | `pedir_hora()`: normaliza a `HH:MM` o vuelve a pedir. |
| 113-119 | `pedir_lavado()`: usa `a_booleano()` y acepta S/N. |
| 122-129 | Empieza el cobro manual; si la patente es `None`, cancela. |
| 131-136 | Pide tipo y días; inicializa horas y minutos. |
| 138-149 | Si `dias == 0`, pide entrada y salida, calcula minutos y rechaza salida anterior o duración cero. |
| 150-151 | Si `dias > 0`, no pide horas: se cobra por día completo. |
| 153-156 | Pide lavado, llama a `liquidar()` y muestra el desglose. |
| 158-178 | Arma el registro con un ID único `MAN-...` usando fecha, hora y milisegundos. |
| 180-189 | Guarda en `liquidacion-manual.csv`; si el archivo está abierto, captura `OSError` y avisa. |
| 191-202 | Opción 2: busca y lee el JSON, llama a `procesar_lote()` y obtiene la fecha de operación. |
| 204-211 | Escribe los tres CSV; si alguno está bloqueado, avisa y no rompe el programa. |
| 213-215 | Calcula métricas y muestra el resumen por consola. |
| 217-229 | Intenta generar el Excel. Si falta `openpyxl` o el archivo está abierto, avisa y sigue. |
| 231-238 | Lista los archivos generados. |
| 241-250 | `leer_csv()`: lee un CSV con `utf-8-sig` y devuelve una lista de diccionarios; si no existe, devuelve `[]`. |
| 253-257 | `convertir_liquidacion()`: convierte a entero los campos numéricos de una fila. |
| 260-267 | `cargar_liquidaciones()`: une `liquidacion.csv` (lote) y `liquidacion-manual.csv` (manual). |
| 270-273 | `formatear_tiempo()`: muestra días completos o minutos según corresponda. |
| 276-318 | `historial_patente()`: pide una patente, suma ingresos, total y promedio, y muestra el detalle. |
| 321-339 | `ver_ranking()`: lee el ranking y muestra el top 10. |
| 342-360 | `ver_rechazados()`: lee y muestra los rechazados con su motivo. |
| 363-375 | `ver_estadisticas()`: recalcula el resumen y las métricas del último lote desde los CSV. |
| 378-406 | `ver_tarifas()`: muestra configuración, precios por categoría y la bonificación por lavado. |
| 409-432 | `ver_ayuda()`: explica formatos, campos del JSON y archivos generados. |
| 435-441 | `pausar_y_limpiar()`: espera Enter y limpia la consola antes de volver al menú. |
| 444-464 | `mostrar_menu()`: imprime las nueve opciones agrupadas por Operaciones, Consultas y Configuración. |
| 467-477 | `main()`: configura la salida UTF-8 y crea `salidas/`. |
| 479-484 | Carga las tarifas; si hay error, muestra el mensaje y termina. |
| 486-511 | Bucle del menú: 1 manual, 2 lote, 3 historial, 4 ranking, 5 rechazados, 6 estadísticas, 7 tarifas, 8 ayuda, 9 salir; después de cada acción pausa y limpia. |
| 514-518 | Punto de entrada; captura `Ctrl+C` y `EOFError` para salir prolijamente. |

**Frase para defender `sys.path.insert`:**

> “Como separé el código en `codigo/`, `main.py` agrega esa carpeta al path
> antes de importar. Así el programa se sigue ejecutando desde la raíz con
> `python main.py`.”

---

### 4.2. `codigo/datos.py`

| Líneas | Qué explicar |
|---|---|
| 1-9 | Imports y expresiones regulares. `PATRON_TRADICIONAL`, `PATRON_MERCOSUR` y `PATRON_HORA`. |
| 12-15 | `normalizar_patente()`: si no es texto devuelve `None`; si es texto, saca espacios y pasa a mayúsculas. |
| 18-21 | `patente_valida()`: true si cumple cualquiera de los dos formatos. |
| 24-27 | `normalizar_tipo()`: saca espacios de los costados y pasa a minúsculas. |
| 30-36 | `parsear_hora()`: convierte `HH:MM` a minutos desde las 00:00. Usa grupos de la regex. |
| 39-43 | `normalizar_hora()`: vuelve a formato `HH:MM` con dos dígitos. |
| 46-57 | `a_booleano()`: acepta bool, 0/1 y textos como `si`, `s`, `true`, `no`, `n`, `false`. Si no entiende, devuelve `None`. |
| 60-71 | `a_entero()`: acepta enteros, floats enteros y textos con dígitos. Rechaza `bool` a propósito. |
| 74-75 | `formatear_pesos()`: `1234567` → `$1.234.567`. |
| 78-84 | `formatear_minutos()`: `135` → `2 h 15 min`. |
| 87-99 | `cargar_json()`: abre con `utf-8-sig`, captura archivo inexistente, error de lectura y JSON inválido. |
| 102-140 | `cargar_tarifas()`: valida que la raíz sea un objeto, que exista `tarifas`, que cada categoría tenga los tres precios obligatorios y que `precio_lavado` sea válido. |

**Líneas importantes:**

- **13-15:** `if not isinstance(valor, str): return None` evita que un número o
  `None` rompa la normalización.
- **15:** `"".join(valor.split()).upper()` saca **todos** los espacios, no solo
  los de los costados.
- **21:** `bool(...)` porque `re.match` devuelve un objeto o `None`, no un bool.
- **33-36:** `group(1)` son las horas y `group(2)` los minutos.
- **61-62:** `bool` es subclase de `int` en Python; por eso se rechaza antes de
  aceptar enteros.
- **91:** `utf-8-sig` acepta archivos con o sin BOM, típico de Windows/Notepad.
- **107-113:** valida la estructura general antes de recorrer categorías.
- **116-129:** recorre cada categoría y exige los tres campos numéricos.
- **132-136:** el lavado es opcional; si falta, vale 0.

---

### 4.3. `codigo/tarifas.py`

| Líneas | Qué explicar |
|---|---|
| 1 | Importa `a_entero` para leer la configuración. |
| 4-7 | `mapa_tarifas()` acepta la estructura completa o solo el diccionario interno. |
| 10-13 | `configuracion()` devuelve la sección de configuración o `{}`. |
| 16-21 | `_limites()` lee bloque, límite y hora adicional; usa 30/120/60 por defecto. |
| 24-25 | `_tarifa()` devuelve la tarifa de la categoría. |
| 28-41 | **Recursión principal.** Caso base y dos ramas. |
| 44-48 | **Recursión de horas excedentes.** |
| 51-70 | `liquidar()` para `dias > 0`: cobra días completos y lavado. |
| 72-74 | Calcula la base recursiva y aplica el tope con `min()`. |
| 76-81 | Calcula bloques y horas adicionales para mostrarlos en el desglose. |
| 83-96 | Aplica la bonificación por lavado. |
| 98-109 | Devuelve el diccionario completo con todos los importes. |

#### La recursión, línea por línea

```python
if minutos_restantes <= 0:          # caso base
    return 0

bloque, limite, hora = _limites(tarifas)
tarifa = _tarifa(tarifas, tipo_vehiculo)

if minutos_restantes <= limite:     # hasta 120 minutos
    return tarifa["precio_bloque_30min"] + calcular_estacionamiento_recursivo(
        minutos_restantes - bloque, tipo_vehiculo, tarifas)

return (calcular_estacionamiento_recursivo(limite, tipo_vehiculo, tarifas)
        + _calcular_horas_excedentes(minutos_restantes - limite,
                                     tarifa["precio_hora_adicional"], hora))
```

**Qué decir:**

> “La función recibe los minutos que faltan. Si ya no queda nada, devuelve 0:
> ese es el caso base. Si quedan 120 minutos o menos, suma un bloque de 30 y se
> llama a sí misma con 30 minutos menos. Si quedan más de 120, cobra los 120
> minutos con la recursión y el excedente lo cobra por hora completa con otra
> función recursiva. No usa `for` ni `while`.”

**Traza de 135 minutos para auto:**

```text
calcular(135)
  → 135 > 120
  → calcular(120) + horas_excedentes(15)
  → calcular(120) = 700 + 700 + 700 + 700 = 2800
  → horas_excedentes(15) = 1200
  → total = 4000
```

**Traza de 181 minutos para auto:**

```text
calcular(181)
  → calcular(120) = 2800
  → horas_excedentes(61)
       → 1200 + horas_excedentes(1)
       → 1200 + 1200
       → 2400
  → total = 5200
```

**Por qué 135 no es 3300:** el pseudocódigo de ejemplo restaba la hora del total
y después cobraba los bloques. Eso descontaba parte de las dos primeras horas.
La regla escrita dice **4 bloques + 1 hora**, y eso es lo que hace el código.

#### `liquidar()`, línea por línea

- **52-55:** obtiene tarifa, límites, tope y precio de lavado.
- **57-70:** si `dias > 0`, cobra `dias * tope_dia` y suma lavado. No usa horas.
- **72:** calcula la base con la recursión.
- **73:** `tope_aplicado = base > tope` guarda si se recortó.
- **74:** `base_con_tope = min(base, tope)` aplica el tope.
- **76-81:** calcula bloques y horas solo para el desglose.
- **83-91:** con lavado y hasta 120 minutos, bonifica todo el estacionamiento.
- **88-91:** con lavado y más de 120 minutos, bonifica las dos primeras horas
  (4 bloques) y cobra solo el excedente.
- **93-96:** sin lavado, paga el estacionamiento con tope.
- **98-109:** devuelve todos los datos: días, minutos, bloques, base,
  bonificación, estacionamiento, lavado, total y si se aplicó el tope.

**Ejemplos para tener a mano:**

| Caso | Resultado |
|---|---|
| Auto, 60 min, con lavado | Estacionamiento $0, lavado $5.000, total $5.000 |
| Auto, 135 min, con lavado | Bonificación $2.800, estacionamiento $1.200, total $6.200 |
| Auto, 135 min, sin lavado | Total $4.000 |
| Auto, 2 días, con lavado | Estacionamiento $32.000, total $37.000 |
| Auto, 120 min, sin lavado, tope $1.000 | Estacionamiento $1.000, tope aplicado |

---

### 4.4. `codigo/validaciones.py`

| Líneas | Qué explicar |
|---|---|
| 1-10 | Imports de normalización, parseo y `mapa_tarifas`. |
| 13-17 | `_texto()`: si el valor es `None` o está vacío, devuelve `"vacio"` para el mensaje. |
| 20-22 | Verifica que el movimiento sea un diccionario. |
| 24-29 | Valida el ID: `None` → vacío; `strip()`; rechaza vacío y repetido. |
| 31-34 | Normaliza y valida la patente. |
| 36-39 | Normaliza el tipo y verifica que exista en las tarifas. |
| 41-44 | Lee `dias` (por defecto 0) y exige entero mayor o igual a 0. |
| 46-48 | Inicializa entrada, salida y minutos. |
| 50-65 | Si `dias == 0`, valida horas, calcula minutos y rechaza salida anterior o duración cero. |
| 67-73 | Valida `solicito_lavado`; si falta, queda `False`. |
| 75-84 | Devuelve el movimiento normalizado y `None` como motivo. |

**Orden de validación:** ID, patente, tipo, días, horas, lavado. Se devuelve el
**primer** motivo encontrado para que el CSV se entienda de una sola lectura.

**Ejemplos:**

- `PATENTE99` → `"Patente invalida (PATENTE99)"`.
- `" BF 901 GG "` → válida, se normaliza a `BF901GG`.
- `tractor` → `"Tipo de vehiculo invalido (tractor)"`.
- `18:00` a `15:00` → `"Salida anterior a la entrada"`.
- `08:00` a `08:00` → `"Duracion cero"`.
- ID `""`, `None` o `"   "` → `"ID vacio"`.
- ID repetido → `"ID repetido (X1)"`.
- `dias = -1` → `"Dias invalidos (-1)"`.
- `dias = 3` → no pide horas.

---

### 4.5. `codigo/procesamiento.py`

| Líneas | Qué explicar |
|---|---|
| 5-7 | Verifica que el JSON sea un diccionario. |
| 9-11 | Verifica que exista la lista `movimientos`. |
| 13-15 | Crea listas `validos` y `rechazados`, y el set `ids_vistos`. |
| 17-27 | Recorre cada movimiento; si hay motivo, lo agrega a `rechazados` y sigue. |
| 29-36 | Si es válido, agrega el ID al set y llama a `liquidar()`. |
| 38-55 | Arma la fila final con todos los campos; convierte lavado y tope a `S/N`. |
| 57 | Devuelve `(validos, rechazados)`. |
| 60-61 | `_texto()` auxiliar para rechazados. |

**Por qué `ids_vistos` es un `set`:** buscar dentro de un set es mucho más
rápido que recorrer una lista, y el set no permite duplicados. El primer ID
válido se registra; si aparece de nuevo, se rechaza.

---

### 4.6. `codigo/reportes.py`

| Líneas | Qué explicar |
|---|---|
| 7-17 | Listas de campos de los CSV. `CAMPOS_MANUAL` agrega `fecha_registro` y evita repetir `id`. |
| 20-25 | `ordenar_liquidacion()` por patente e ID; `ordenar_rechazados()` por ID y patente. |
| 28-32 | `contar_rechazos()`: diccionario motivo → cantidad, ordenado. |
| 35-40 | `escribir_csv()`: abre en `w`, `newline=""`, `utf-8-sig`; escribe encabezado y filas. |
| 43-53 | Los tres escritores: liquidación, rechazados y ranking. |
| 56-70 | `agregar_liquidacion_manual()`: si el archivo existe, agrega; si no, crea con encabezado. |
| 73-106 | `imprimir_desglose()`: muestra patente, tiempo, base, bonificación, lavado y total. |
| 109-123 | `imprimir_resumen()`: procesados, rechazados, total y motivos. |
| 126-156 | `calcular_metricas()`: recaudación, cantidad, promedios, más rentable y porcentaje de lavado. |
| 159-186 | `imprimir_metricas()`: muestra las métricas por consola. |
| 189-229 | Constantes del Excel: campos, anchos y formatos. |
| 232-241 | `escribir_excel()`: importa `openpyxl`; si falta, lanza `ImportError`. |
| 243-279 | Colores, fuentes, rellenos, alineaciones y bordes. |
| 281-340 | `escribir_tabla()`: título, encabezado, filas, formatos, colores, anchos, filtro y congelar paneles. |
| 342-360 | Fecha del reporte, creación del libro y de las cuatro hojas. |
| 362-403 | Llena Liquidación, Ranking (con puesto y top 3 dorado) y Rechazados. |
| 405-437 | Totales y encabezado de la hoja Estadísticas. |
| 439-490 | `seccion()`, `dato()` y `tabla()`: helpers para armar el recuadro. |
| 492-548 | Contenido: resumen, recaudación por categoría, promedios, rechazos y top 5. |
| 550-572 | Borde exterior, anchos, configuración de página y color de pestaña. |
| 574-594 | Gráfico de barras con `BarChart` y `Reference`. |
| 596-598 | Activa Estadísticas, guarda y devuelve la ruta. |

**Líneas importantes:**

- **21:** `sorted(validos, key=lambda fila: (fila["patente"], fila["id"]))`:
  ordena por patente y, si hay empate, por ID.
- **25:** mismo concepto para rechazados.
- **36:** `newline=""` evita filas en blanco en Windows.
- **52:** `-fila["total"]` ordena de mayor a menor.
- **58:** `ruta.stat().st_size > 0` evita escribir el encabezado dos veces.
- **61-64:** si el archivo ya existe se abre en `a`; si no, en `w` con
  `utf-8-sig`. No se usa `utf-8-sig` al agregar porque metería un BOM en el
  medio del archivo.
- **138:** una estadía de `dias > 0` se cuenta como `dias * 1440` minutos para
  que el promedio sea comparable.
- **145:** `max(recaudado, key=recaudado.get)` devuelve la categoría con más
  recaudación.
- **234-241:** el Excel es opcional; el `try/except ImportError` permite que el
  programa siga con los CSV.
- **324-325:** si la fila está en la lista de colores, se pinta; así se resaltan
  los tres primeros del ranking.
- **442:** `nonlocal fila` permite que las funciones internas avancen el
  contador de filas de la hoja de estadísticas.
- **596:** `libro.active = 0` hace que el Excel abra en `Estadísticas`.

---

### 4.7. `codigo/pruebas.py`

| Líneas | Qué explicar |
|---|---|
| 1-16 | Imports, `RAIZ` y `DATOS`. |
| 19-27 | Pruebas de patentes válidas e inválidas. |
| 30-43 | Pruebas de recursión: 0, 1, 30, 31, 120, 121, 135, 180, 181 y camioneta. |
| 46-66 | Pruebas de lavado: 60 min, 135 min, sin lavado y 2 días. |
| 69-82 | Prueba del tope con una tarifa modificada a $1.000. |
| 85-121 | Pruebas de validaciones: patente, tipo, horas, duración cero, ID vacío, ID repetido, días negativos y estadía prolongada. |
| 124-177 | Pruebas del lote: 30 válidos, 3 rechazados, total $129.000, IDs concretos, métricas y orden. |
| 180-219 | Prueba del Excel si `openpyxl` está instalado: hojas, orden, totales y gráfico. |
| 222-236 | Carga tarifas, ejecuta los seis grupos y muestra el mensaje final. |

**Qué decir:**

> “Las pruebas usan `assert`: si una condición no se cumple, el programa falla
> con un error. Cubren patentes, recursión, lavado, tope, validaciones, lote,
> orden y Excel. Se corren con `python codigo/pruebas.py`.”

---

## 5. Preguntas típicas y respuestas cortas

| Pregunta | Respuesta sugerida |
|---|---|
| ¿Qué hace el programa? | Lee tarifas y movimientos, valida, liquida y genera CSV/Excel con estadísticas. |
| ¿Dónde está la recursión? | En `codigo/tarifas.py`, función `calcular_estacionamiento_recursivo`. |
| ¿Usa `for` o `while` la recursión? | No. Baja restando 30 o 60 minutos hasta el caso base. |
| ¿Cuál es el caso base? | `minutos_restantes <= 0` → devuelve 0. |
| ¿Por qué 135 minutos son $4.000? | 4 bloques de 30 min ($2.800) + 1 hora adicional ($1.200). |
| ¿Por qué 181 minutos son $5.200? | 4 bloques ($2.800) + 2 horas adicionales ($2.400). |
| ¿Qué pasa si `dias > 0`? | Se cobra `dias * tope_dia` y no se piden horas. |
| ¿El tope limita el lavado? | No. El tope se aplica al estacionamiento; el lavado se suma aparte. |
| ¿Se cruza la medianoche? | No. Si la salida es anterior a la entrada, se rechaza. |
| ¿Qué pasa con `MOV031`? | Se rechaza porque la salida es anterior a la entrada. |
| ¿Cómo validás una patente? | Se normaliza y se compara con dos regex: `ABC123` o `AA123BB`. |
| ¿Qué pasa si el ID está repetido? | El primero válido se registra; el segundo se rechaza con `"ID repetido"`. |
| ¿Qué pasa si el ID es `None` o vacío? | Se rechaza con `"ID vacio"`. |
| ¿Qué pasa si falta `dias`? | Vale 0 por defecto. |
| ¿Qué pasa si falta `solicito_lavado`? | Vale `False` por defecto. |
| ¿Qué pasa si falta `precio_lavado`? | Vale 0; el lavado es opcional en la tarifa. |
| ¿Qué pasa si falta una tarifa obligatoria? | `cargar_tarifas()` rechaza todo el archivo con un mensaje claro. |
| ¿Qué pasa si el JSON está mal? | `cargar_json()` lanza `ValueError` con el nombre y la línea del error. |
| ¿Qué pasa si el JSON no tiene `movimientos`? | `procesar_lote()` lanza `ValueError`. |
| ¿Qué pasa si un movimiento no es un objeto? | Se rechaza con `"Movimiento invalido"`. |
| ¿Cómo se ordena la liquidación? | Por patente y, si hay empate, por ID. |
| ¿Cómo se ordena el ranking? | Por total de mayor a menor y, si hay empate, por patente. |
| ¿Qué diferencia hay entre `liquidacion.csv` y el ranking? | Tienen los mismos datos, pero el ranking está ordenado por total descendente. |
| ¿Qué desafíos implementaste? | N.º 2 (métricas del negocio) y N.º 3 (ranking CSV). |
| ¿Qué pasa si no está `openpyxl`? | Se generan los CSV y se muestra un aviso; el programa no se rompe. |
| ¿Por qué usás `utf-8-sig`? | Para aceptar archivos con o sin BOM, común en Windows. |
| ¿Por qué `newline=""`? | Para que el CSV no tenga filas en blanco en Windows. |
| ¿Por qué `a_entero` rechaza `bool`? | Porque en Python `True` es subclase de `int` y se convertiría en 1. |
| ¿Por qué usás un `set` para los IDs? | Para detectar duplicados rápido y sin repetir. |
| ¿Cómo se genera el ID manual? | Con la fecha, la hora y los milisegundos: `MAN-...`. |
| ¿Qué pasa si un CSV está abierto en Excel? | Se captura `OSError` y se avisa que lo cierres. |
| ¿Cómo se genera el Excel? | Con `openpyxl`: cuatro hojas, estilos, recuadro de estadísticas y gráfico. |
| ¿Por qué el Excel abre en Estadísticas? | Porque `libro.active = 0`. |
| ¿Qué prueba que todo funcione? | `python codigo/pruebas.py` → 6 grupos OK. |
| ¿Qué resultado da el JSON de ejemplo? | 30 procesados, 3 rechazados, $129.000; camioneta la más rentable; 13/30 lavados. |

---

## 6. Guion corto para la presentación (2 minutos)

> “Buen día. Mi programa se llama AutoPark y resuelve la liquidación de un
> estacionamiento. La entrada es `main.py`, que muestra un menú con nueve
> opciones: cobro manual, proceso por lote, consultas, tarifas y ayuda.
>
> Los datos se leen desde `datos/`. `datos.py` se encarga de normalizar patentes,
> tipos y horas, y de validar las tarifas. `validaciones.py` decide si un
> movimiento se acepta o se rechaza, siempre devolviendo el primer motivo.
>
> La parte central está en `tarifas.py`: `calcular_estacionamiento_recursivo`
> calcula el estacionamiento sin usar `for` ni `while`. Si quedan 120 minutos o
> menos, suma un bloque de 30 y se llama otra vez; si quedan más de 120, cobra
> las dos primeras horas y el excedente por hora completa. Por ejemplo, 135
> minutos de auto dan $4.000: cuatro bloques más una hora.
>
> Después `procesamiento.py` recorre el lote, valida, liquida y arma las filas.
> `reportes.py` genera los CSV ordenados, calcula las métricas y, si está
> `openpyxl`, arma el Excel con estadísticas y gráfico.
>
> Implementé dos desafíos de nivel 1: el N.º 2, métricas del negocio, y el N.º 3,
> ranking ordenado por total. Lo probé con el JSON de ejemplo: 30 procesados, 3
> rechazados y $129.000 recaudados. Las pruebas automáticas dan 6 grupos OK.”

---

## 7. Cómo hacer la Demo en vivo

1. Mostrá la estructura de carpetas.
2. Corré las pruebas:

   ```cmd
   python codigo/pruebas.py
   ```

3. Corré el programa:

   ```cmd
   python main.py
   ```

4. Elegí la opción **2** y mostrá el resumen.
5. Abrí `salidas/liquidacion.csv`, `salidas/rechazados.csv` y
   `salidas/liquidacion_ranking.csv`.
6. Abrí `salidas/liquidacion.xlsx` y mostrá:
   - hoja `Estadísticas`;
   - hoja `Liquidación` ordenada por patente;
   - hoja `Ranking` con el top 3 resaltado;
   - hoja `Rechazados` ordenada por ID.
7. Volvé al menú, elegí **1** y cargá un caso simple:
   - patente `ABC123`;
   - tipo `auto`;
   - días `0`;
   - entrada `08:00`;
   - salida `08:30`;
   - lavado `N`.
   Debe dar **$700** y guardar en `salidas/liquidacion-manual.csv`.
8. Volvé al menú, elegí **3** y buscá `ABC123`: debe mostrar el ingreso manual,
   el total acumulado y la estadía promedio.
9. Cerrá con la opción **9**.

**Antes de la demo:** cerrá el Excel si está abierto, para que el programa pueda
sobrescribir el archivo.

---

## 8. Preguntas trampa

| Pregunta trampa | Respuesta correcta |
|---|---|
| “¿La recursión tiene un `for` escondido?” | No. Solo se llama a sí misma y usa `if`. |
| “¿El tope también limita el lavado?” | No. El tope es del estacionamiento; el lavado se suma. |
| “¿El Excel es obligatorio?” | No. Es opcional; sin `openpyxl` se generan los CSV. |
| “¿Se puede cruzar la medianoche?” | No. Si la salida es menor que la entrada, se rechaza. |
| “¿MOV031 es válido?” | No. Tiene salida anterior a la entrada. |
| “¿`dias` es obligatorio?” | No. Si falta, vale 0. |
| “¿Qué pasa si el JSON tiene una lista en la raíz?” | `procesar_lote` lo rechaza con un `ValueError`. |
| “¿Qué pasa si una tarifa está incompleta?” | `cargar_tarifas` rechaza todo el archivo. |
| “¿Qué pasa si `solicito_lavado` es `"tal vez"`?” | Se rechaza con `"Valor de lavado invalido"`. |
| “¿Qué pasa si la patente tiene espacios?” | Se normaliza; `" BF 901 GG "` es válida. |
| “¿Qué pasa si la hora es `8:05`?” | Se acepta y se normaliza a `08:05`. |
| “¿Qué pasa si la hora es `08:5`?” | Se rechaza; los minutos necesitan dos dígitos. |

---

## 9. Mini cuestionario para practicar

1. ¿Cuál es la función que contiene la recursión?
2. ¿Cuál es el caso base?
3. ¿Qué hace la función si quedan 120 minutos o menos?
4. ¿Qué hace si quedan más de 120?
5. ¿Por qué 135 minutos de auto cuestan $4.000?
6. ¿Dónde se valida la patente?
7. ¿Qué pasa si el ID está repetido?
8. ¿Cómo se ordena `liquidacion.csv`?
9. ¿Cómo se ordena el ranking?
10. ¿Qué hojas tiene el Excel?
11. ¿Qué pasa si falta `openpyxl`?
12. ¿Qué desafíos implementaste?
13. ¿Qué pasa si `dias > 0`?
14. ¿El tope limita el lavado?
15. ¿Se cruza la medianoche?

**Respuestas:**

1. `calcular_estacionamiento_recursivo`, en `codigo/tarifas.py`.
2. `minutos_restantes <= 0` → devuelve 0.
3. Suma un bloque de 30 y se llama con 30 minutos menos.
4. Cobra 120 minutos con la recursión y el excedente por hora completa.
5. 4 bloques de $700 + 1 hora de $1.200 = $4.000.
6. En `patente_valida()`, dentro de `codigo/datos.py`; la usa
   `validar_movimiento()`.
7. El primero válido se registra; el segundo se rechaza con `"ID repetido"`.
8. Por patente y, si hay empate, por ID.
9. Por total de mayor a menor y, si hay empate, por patente.
10. `Estadísticas`, `Liquidación`, `Ranking` y `Rechazados`.
11. Se generan los CSV y se muestra un aviso; el programa sigue funcionando.
12. N.º 2 (métricas del negocio) y N.º 3 (ranking CSV).
13. Se cobra `dias * tope_dia` y no se piden horas.
14. No. El tope es solo del estacionamiento.
15. No. Se rechaza si la salida es anterior a la entrada.

---

## 10. Checklist final

- [ ] `python codigo/pruebas.py` → `6 grupos OK`.
- [ ] `python main.py` → opción 2 → 30 procesados, 3 rechazados, $129.000.
- [ ] `salidas/liquidacion.csv` tiene 30 filas y está ordenado por patente.
- [ ] `salidas/rechazados.csv` tiene 3 filas y está ordenado por ID.
- [ ] `salidas/liquidacion_ranking.csv` está ordenado por total descendente.
- [ ] `salidas/liquidacion.xlsx` tiene 4 hojas y el recuadro de estadísticas.
- [ ] Sabés explicar 135 minutos → $4.000.
- [ ] Sabés explicar por qué el tope no recorta el lavado.
- [ ] Sabés explicar por qué `MOV031` se rechaza.
- [ ] Sabés decir que el Excel es opcional.
- [ ] Sabés decir que la recursión no usa `for` ni `while`.
- [ ] Tenés cerrado el Excel antes de ejecutar el lote.
