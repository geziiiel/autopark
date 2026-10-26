# 2.º Parcial de Programación — AutoPark

- **Alumno:** Geziel
- **Modalidad:** individual
- **Entrega:** lunes 26/10/2026, 19:00
- **Estado:** funcionando y probado

## Documentos

- Enunciado completo: `ENUNCIADO.md`
- Desafíos de valor agregado: `DESAFIOS_VALOR_AGREGADO.md`
- Cómo ejecutar y decisiones: `README.md`

## Desafíos elegidos (NIVEL 1)

1. **N.º 2 — Reporte estadístico y métricas del negocio.**
2. **N.º 3 — Ordenamiento algorítmico (ranking en CSV).**

## Resultado con el JSON de ejemplo

- 30 movimientos procesados.
- 3 rechazados (MOV031, MOV032, MOV033).
- Total recaudado: **$129.000**.
- Categoría más rentable: **camioneta** ($64.900).
- Lavados: **13 de 30 (43,3 %)**.

## Salidas

- `liquidacion.csv` → movimientos válidos, ordenados por patente.
- `rechazados.csv` → rechazos, ordenados por ID.
- `liquidacion_ranking.csv` → ranking de mayor a menor total.
- `liquidacion.xlsx` → hojas ordenadas y recuadro de estadísticas (opcional,
  requiere `openpyxl`).

## Ejecución

```cmd
cd "C:\Users\Geziel\Documents\2 Parcial"
:: solo hace falta para el Excel
python -m pip install -r requirements.txt
python main.py
```

Pruebas:

```cmd
python pruebas.py
```
