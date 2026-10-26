# 2.º Examen Parcial: Sistema de Gestión de Estacionamiento "AutoPark"

**Materia:** Programación I / II  
**Carrera:** Tecnicatura Superior en Desarrollo de Software — 2.º Año  
**Instituto:** Instituto Roque González  
**Modalidad:** Individual  
**Tiempo estimado:** 2 horas  

---

## 1. Contexto General
La empresa de estacionamientos comerciales **AutoPark** necesita renovar su sistema operativo. Te solicitan desarrollar una aplicación modular de consola en Python que permita:
1. Simular y registrar en ventanilla el cobro manual de un vehículo (tiempo real), contemplando tanto salidas en el mismo día como estadías de varios días, guardando el comprobante en un archivo CSV.
2. Procesar por lote los movimientos del día desde un archivo JSON, validar los datos (patentes, tipos y horarios), aplicar las reglas de liquidación y exportar los reportes contables a formato CSV.

---

## 2. Reglas de Negocio y Esquema Tarifario

El importe final a cobrar se compone de: **Estacionamiento + Lavado (si aplica)**.

### A. Validación Obligatoria de Patentes
Toda patente ingresada (manual o desde JSON) debe ser normalizada (sin espacios, en mayúsculas) y validada. Solo se admiten dos formatos oficiales:
- **Formato Tradicional:** 3 letras seguidas de 3 números (ejemplo: `ABC123`).
- **Formato Mercosur:** 2 letras, 3 números y 2 letras (ejemplo: `AA123BB`).
*Si una patente no cumple con alguno de estos dos patrones, el registro es inválido.*

### B. Estadías en el Mismo Día (Días = 0)
Si el vehículo ingresó y se retira en el mismo día, el tiempo se mide en minutos entre la hora de entrada y la de salida (`HH:MM`):
- Toda fracción de tiempo se redondea hacia arriba al bloque siguiente.
- **Primeras 2 horas (hasta 120 minutos):** se cobra en bloques de **30 minutos**.
  - De 1 a 30 min $\rightarrow$ 1 bloque de 30 min.
  - De 31 a 60 min $\rightarrow$ 2 bloques de 30 min.
  - De 61 a 90 min $\rightarrow$ 3 bloques de 30 min.
  - De 91 a 120 min $\rightarrow$ 4 bloques de 30 min.
- **A partir del minuto 121 en adelante:** el tiempo excedente se cobra por **hora completa** (bloques de 60 minutos o fracción).
  - Ejemplo: 135 minutos equivalen a 4 bloques de 30 min + 1 hora adicional.
- **Tope diario:** no puede superar el `tope_dia` estipulado en la configuración para esa categoría.

### C. Estadías Prolongadas (Días > 0)
Si el vehículo permaneció uno o más días:
- Se cobra un **costo fijo por día completo** (equivalente al `tope_dia` por cada día transcurrido: $\text{días} \times \text{tope\_dia}$).
- **No se requiere hora de salida**, ya que la facturación se realiza por jornadas completas de 24 horas.

### D. Beneficio por Servicio de Lavado
El cliente puede contratar opcionalmente el servicio de lavado:
- **Si NO solicitó lavado:** abona la tarifa normal de estacionamiento.
- **Si SOLICITÓ lavado en estadía de hasta 120 minutos ($\le 2$ hs):** el estacionamiento está **100% bonificado**. Paga únicamente el valor fijo del lavado.
- **Si SOLICITÓ lavado en estadía de más de 120 minutos ($> 2$ hs):** abona el valor fijo del lavado **más** el estacionamiento correspondiente únicamente a las horas excedentes (las primeras 2 horas quedan bonificadas).
- **Si SOLICITÓ lavado en estadía prolongada (días > 0):** abona los días de estacionamiento más el servicio de lavado.

---

## 3. Arquitectura Modular del Proyecto (Separación en Archivos)

El proyecto debe estar correctamente modularizado respetando la separación de responsabilidades

---

## 4. Menú Principal de la Aplicación (ej)

```text
==================================================
   SISTEMA DE GESTIÓN DE ESTACIONAMIENTO AUTOPARK
==================================================
1. Registrar / Consultar cobro manual
2. Procesar lote de movimientos (JSON -> CSV)
3. Salir
Seleccione una opción: 
```

### Comportamiento de las Opciones:

#### Opción 1: Cobro Manual en Ventanilla
1. Solicita la patente y valida que sea `AAA000` o `AA000AA`.
2. Solicita el tipo de vehículo (`auto`, `moto`, `camioneta`).
3. Pregunta: `¿Cuántos días pasaron? (0 si se retira en el mismo día):`
   - **Si ingresa 0:** pide `Hora de entrada (HH:MM)` y `Hora de salida (HH:MM)`, calcula minutos.
   - **Si ingresa > 0:** informa que se liquidará por días completos a costo fijo (no pide hora de salida).
4. Pregunta si solicitó lavado (`S/N`).
5. Muestra en pantalla el desglose contable (minutos/días, base, bonificación, lavado y total a pagar).
6. **Guarda el registro en `liquidacion-manual.csv`** (acumulando las transacciones).

#### Opción 2: Procesamiento por Lote
1. Lee `tarifas.json` y `movimientos.json`.
2. Procesa y valida cada movimiento:
   - Patentes o tipos inválidos, o salidas anteriores a entradas se descartan.
3. Genera dos archivos CSV:
   - `liquidacion.csv`: registros válidos procesados.
   - `rechazados.csv`: movimientos descartados con su motivo de rechazo.
4. Muestra un resumen en consola: procesados, rechazados y total recaudado ($).
