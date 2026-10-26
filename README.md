# AutoPark — Sistema de Gestión de Estacionamiento

2.º Examen Parcial de Programación I / II — Instituto Roque González  
Alumno: **Geziel** — Modalidad: **individual**

Aplicación de consola en Python, sin dependencias externas (solo biblioteca
estándar). Lee `tarifas.json` y `movimientos.json`, valida los datos, liquida
las estadías y genera los CSV.

---

## Cómo se ejecuta

```cmd
cd "C:\Users\Geziel\Documents\2 Parcial"
python main.py
```

Menú:

```text
1. Registrar / Consultar cobro manual
2. Procesar lote de movimientos (JSON -> CSV)
3. Salir
```

Las pruebas automáticas se corren aparte:

```cmd
python pruebas.py
```

Resultado esperado: `Todas las pruebas pasaron: 6 grupos OK.`

---

## Archivos del proyecto

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Menú, cobro manual en ventanilla y coordinación general |
| `datos.py` | Leer JSON, normalizar patentes/tipos/horas y validar tarifas |
| `tarifas.py` | Cálculo recursivo del estacionamiento y liquidación final |
| `validaciones.py` | Motivo de rechazo de cada movimiento del lote |
| `procesamiento.py` | Recorre el lote, valida y liquida |
| `reportes.py` | CSV de salida, ranking, métricas y resumen por consola |
| `pruebas.py` | Pruebas con `assert` de reglas y casos límite |
| `tarifas.json` | Configuración y precios (se puede modificar) |
| `movimientos.json` | Movimientos del día (se puede modificar) |

Archivos que genera el programa:

- `liquidacion.csv` → movimientos válidos del lote.
- `rechazados.csv` → movimientos descartados con su motivo.
- `liquidacion_ranking.csv` → desafío nivel 1 N.º 3 (ordenado por total).
- `liquidacion-manual.csv` → cobros manuales acumulados.

---

## Reglas implementadas

### Patentes
Se normalizan sacando espacios y pasando a mayúsculas. Se aceptan solo:

- Tradicional: `ABC123` (3 letras + 3 números).
- Mercosur: `AA123BB` (2 letras + 3 números + 2 letras).

### Mismo día (`dias = 0`)
- Los minutos se calculan entre `entrada` y `salida` (`HH:MM`).
- Hasta 120 minutos: bloques de 30 minutos, con fracción hacia arriba.
- Desde el minuto 121: 4 bloques + una hora por cada 60 minutos o fracción
  del excedente.
- El estacionamiento nunca supera el `tope_dia` de la categoría.

### Estadía prolongada (`dias > 0`)
- Se cobra `dias * tope_dia`.
- No se pide hora de salida.

### Lavado
- Sin lavado: estacionamiento normal.
- Con lavado y hasta 120 minutos: estacionamiento 100 % bonificado; se paga
  solo el lavado.
- Con lavado y más de 120 minutos: se bonifican las primeras 2 horas y se
  cobra lavado + horas excedentes.
- Con lavado y `dias > 0`: se cobra `dias * tope_dia` + lavado.

### Validaciones del lote
Se rechaza el movimiento (y se escribe el motivo en `rechazados.csv`) si:

- el ID está vacío o repetido;
- la patente no cumple ninguno de los dos formatos;
- el tipo de vehículo no existe en `tarifas.json`;
- `dias` no es un entero mayor o igual a 0;
- la hora de entrada o de salida no es `HH:MM` válida;
- la salida es anterior a la entrada;
- la salida es igual a la entrada (duración cero);
- `solicito_lavado` no se puede interpretar como sí/no.

---

## Resultado con el JSON de ejemplo

- **30 movimientos procesados**
- **3 rechazados**:
  - `MOV031` → salida anterior a la entrada.
  - `MOV032` → tipo de vehículo inválido (`tractor`).
  - `MOV033` → patente inválida (`PATENTE99`).
- **Total recaudado: $129.000**

Métricas (desafío nivel 1 N.º 2):

| Categoría | Recaudación | Vehículos | Estadía promedio |
|---|---:|---:|---:|
| auto | $49.500 | 13 | 113,0 min |
| camioneta | $64.900 | 9 | 138,3 min |
| moto | $14.600 | 8 | 66,9 min |

- Categoría más rentable: **camioneta** ($64.900).
- Vehículos con lavado: **13 de 30 (43,3 %)**.

---

## Desafíos de valor agregado (nivel 1)

Como el parcial es individual, la modalidad pide al menos un desafío de
**NIVEL 1**. Se implementaron dos:

1. **N.º 2 — Reporte estadístico y métricas del negocio:** al terminar el lote
   se imprime la categoría más rentable, el porcentaje de lavados y la estadía
   promedio por categoría.
2. **N.º 3 — Ordenamiento algorítmico:** se genera
   `liquidacion_ranking.csv` con los registros ordenados de mayor a menor total
   (se usa `sorted()` con una función lambda).

---

## Decisiones que conviene poder defender

### 1. La recursión no es literal al pseudocódigo del mensaje

El pseudocódigo de ejemplo decía: si quedan más de 120 minutos, sumar una hora
y restar 60; si quedan 120 o menos, sumar un bloque y restar 30. Copiado tal
cual, **135 minutos** terminan pagando **1 hora + 3 bloques** (para auto:
$3.300), porque al restar la hora también se descuenta parte de las dos primeras
horas.

Pero la regla escrita del punto B dice que 135 minutos son **4 bloques + 1 hora**
(para auto: $4.000). La implementación respeta el enunciado:

- `calcular_estacionamiento_recursivo(135, "auto", tarifas)` → `$4.000`.
- La función no usa `for` ni `while`: baja restando 30 o 60 minutos hasta el
  caso base.

En la defensa: *"el pseudocódigo era un ejemplo y restaba la hora del total;
eso cobraba de menos. Lo adapté para que las dos primeras horas siempre sean
4 bloques y el excedente se cobre por hora, como dice el punto B."*

### 2. El tope diario se aplica al estacionamiento, no al lavado
El enunciado dice que el importe final es **estacionamiento + lavado** y que el
tope limita el estacionamiento. Por eso un auto con tope de $16.000 y lavado de
$5.000 puede pagar $21.000: el tope no recorta el lavado.

### 3. Duración cero se rechaza
El enunciado solo habla de salidas anteriores, pero una estadía de 0 minutos no
encaja en ningún bloque (los bloques empiezan en 1 minuto). Se rechaza con
`"Duracion cero"` para no regalar estacionamiento.

### 4. Precios enteros
Los precios de `tarifas.json` se interpretan como pesos enteros, igual que en el
archivo de ejemplo.

### 5. `dias` es opcional en el lote
El JSON de ejemplo no trae `dias`, así que por defecto vale 0. Si en una prueba
agregan `"dias": 2`, el movimiento se liquida por días completos y no se le
exigen horas.

### 6. Las estadías prolongadas en las métricas
Para el promedio en minutos, una estadía de `dias > 0` se cuenta como
`dias * 1440` minutos. Así se puede comparar con las del mismo día.

### 7. No se implementó el cruce de medianoche
El desafío N.º 4 es opcional y cambiaría la regla base de "salida anterior a la
entrada se descarta". Se priorizaron dos desafíos que no alteran esa regla. Por
eso `MOV031` se rechaza. Si se quisiera agregar, se resolvería sumando
`24 * 60` minutos a la salida cuando es menor que la entrada.

---

## Repositorio

El proyecto ya está inicializado en Git, en la rama `main`, con dos commits:

```cmd
cd "C:\Users\Geziel\Documents\2 Parcial"
git status
git log --oneline
```

`liquidacion-manual.csv` está en `.gitignore` porque se va acumulando con cada
prueba manual. Los CSV del lote sí quedan versionados como ejemplo.

Para subirlo a GitHub, crear primero un repositorio vacío en la web y después:

```cmd
git remote add origin https://github.com/TU-USUARIO/autopark.git
git push -u origin main
```
