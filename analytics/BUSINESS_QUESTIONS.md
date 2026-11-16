# Contrato de métricas y visualizaciones

Preguntas tomadas de la tabla de la sección 3 del documento de Luis: https://docs.google.com/document/d/120otnvGyS6ZUaEUQJacYdP4uynaR1PypY6e36geybCo/edit

CONTI es el proveedor tecnológico; Terra Nostra es la tienda. Las preguntas siguen pendientes del aval docente si no se ha obtenido por otra vía.

## Reglas comunes

- Fecha y mes: fecha local de compra en Costa Rica.
- Ventas incluidas: estados 2 (En preparación) y 3 (Entregado). Se excluyen 1 (Pendiente) y 4 (Cancelado). Son ventas confirmadas, no exclusivamente ingresos ya cobrados.
- Unidades: suma de cantidades de líneas elegibles. No equivale a demanda no atendida ni descuenta devoluciones que no están modeladas en la fuente.
- Ingreso de productos: `cantidad × final_price` de cada línea, en CRC. Excluye envío e impuestos. Se compara contra `ot_subtotal`; no se confunde con el total de la factura.
- Precio medio realizado: ingreso de productos / unidades, ponderado por cantidad. No es el precio de catálogo actual ni un promedio simple de precios.
- El mes en curso tiene `is_complete_month=0`. La bandera indica un mes cerrado en el calendario; no garantiza cobertura anterior al primer pedido observado (8 de mayo de 2026). Para comparar meses terminados filtrar `is_complete_month=1`.
- Las tablas Gold ya están agregadas. No sumar una medida Gold después de unirla a reseñas o interacciones (relaciones uno a muchos), porque multiplicaría el ingreso.

| # | Pregunta | Archivo Gold | Visual y campos |
|---|---|---|---|
| 1 | ¿Cómo varía la demanda de vinos según la temporada y cuáles categorías presentan mayores incrementos en ventas? | q01_monthly_category.csv | Líneas: eje month, leyenda category, valor units. Incluir cero ventas; distinguir mes parcial. change_units y change_pct permiten identificar los mayores incrementos. Con siete meses se muestra evolución mensual, no una estacionalidad anual demostrada. |
| 2 | ¿Qué categorías generan mayores ingresos y mayor volumen de ventas? | q02_category_sales.csv | Combinado: category, columnas revenue_crc y línea units. Unidades y CRC en ejes identificados por separado. |
| 3 | ¿Qué relación existe entre el precio de los vinos y su volumen de ventas? | q03_price_volume.csv | Dispersión por product_id: X average_realized_price_crc, Y units; tooltip current_catalog_price_crc. Asociación descriptiva, sin concluir causalidad. |
| 4 | ¿Qué vinos generan mayores ingresos, pero menor volumen de ventas? | q04_revenue_volume.csv | Dispersión por product_id: X units, Y revenue_crc. Bandera high_revenue_low_volume: ingreso ≥ mediana e unidades ≤ mediana, entre vinos con ventas. El criterio queda explícito; no se inventa un umbral comercial. |
| 5 | ¿Qué categorías concentran los ingresos totales de Terra Nostra? | q05_category_pareto.csv | Columnas revenue_crc ordenadas por rank; línea cumulative_pct en eje 0–100 %. Con solo cuatro categorías el Pareto es corto, pero responde a la pregunta acordada. |
| 6 | ¿Qué productos presentan una disminución de ventas frente al mes anterior? | q06_monthly_change.csv | Barras product y change_pct. Filtrar un único month, is_complete_month=1 y comparison=baja; para el historial actual usar el último mes terminado disponible. Antes=0 produce porcentaje vacío y comparison=sin_base, sin dividir por cero. Incluye productos que pasan de vender a cero (−100 %). |

`customer_segment_sales.csv` demuestra el cruce de ventas con segmentos del CRM. `review_summary.csv` integra las valoraciones del CSV con los vinos. La valoración media no se presenta como análisis de sentimiento ni como una predicción de IA.

## Modelo Silver para Power BI o Tableau

| Tabla | Grano / clave | Relaciones |
|---|---|---|
| dim_product | Una fila por product_id | 1 → muchas líneas y reseñas |
| dim_customer | Una fila por customer_id de la tienda | 1 → muchas líneas y reseñas; sin nombres ni correos |
| dim_date | Una fila por date | 1 → muchas líneas por date |
| fact_order_lines | Una fila por order_line_id, incluidos estados excluidos con bandera | Pedidos, productos y clientes; filtrar included_sale=1 para ventas |
| fact_reviews | Una fila por review_id | product_id, customer_id y order_line_id |
| crm_customers | Una fila por crm_customer_id; incluye prospectos | customer_id opcional; los prospectos no tienen compras |
| crm_interactions | Una fila por interaction_id | Muchas → un crm_customer_id |

Para usar hechos, crear relaciones de filtrado simple desde dimensiones. No unir físicamente ventas a cada reseña o interacción. Las tablas Gold se pueden importar por separado para construir las seis visualizaciones sin relaciones adicionales.

## Importación inicial

1. Exportar la carga verificada con `export_bi.py` y descargar el ZIP privado por SSH.
2. Descomprimir e importar CSV Gold (UTF-8 con BOM), usando coma como delimitador.
3. Definir identificadores como enteros, month como texto YYYY-MM, date como fecha y medidas CRC como decimal fijo. Los archivos usan punto decimal; si Power BI interpreta la configuración regional española de forma distinta, elegir explícitamente configuración regional Inglés (Estados Unidos) al convertir las medidas numéricas.
4. Crear los seis visuales de la tabla, títulos, unidad CRC, filtros de periodo para Q1/Q6 y una nota visible de datos académicos. Q2–Q5 cubren el historial completo de la carga; para filtrar esas medidas por fecha se debe usar el modelo Silver con medidas dinámicas.
5. Validar que los ingresos totales de las tablas Q1–Q5 y segmentos coincidan con el manifiesto. No sumar las filas de porcentajes para obtener el crecimiento de varios vinos.

El ZIP es una exportación manual de una versión; el ETL del lago sí queda programado diariamente. El refresco de un reporte publicado en Power BI/Tableau es una configuración posterior.
