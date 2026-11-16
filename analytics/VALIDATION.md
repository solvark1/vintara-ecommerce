# Evidencia de implementación del ETL

Fecha local: 15 de noviembre de 2026, Costa Rica.

## Comprobaciones ejecutadas

- Siete pruebas unitarias pasaron en la VM Linux: exclusión de cancelados/pendientes, ceros mensuales y disminución del 100 %, división por cero, reseñas duplicadas y referencias inválidas, importes no finitos, columnas sin datos personales y preservación de la última carga correcta ante un fallo de subida.
- Primera carga real: tienda + CRM MySQL mediante el usuario de solo lectura y CSV privado alojado en Azure.
- 25 objetos de cada carga publicada descargados y comparados por SHA256; filas CSV e ingresos agregados reconciliados.
- Carga manual final `20261116T045444Z-5ae312f7` y carga automática de prueba `20261116T045602Z-50507d9e`: igual hash de entrada y los mismos hashes de los 16 archivos Silver/Gold, incluido el archivo vacío de cuarentena. Los snapshots son versiones completas; no se concatenaron ni duplicaron pedidos.
- El journal de `terranostra-etl-proof-final.service` registra inicio y final satisfactorios disparados por un temporizador de 15 segundos. No fue necesario iniciar la carga manualmente después de activar ese temporizador.
- Timer diario `terranostra-etl.timer` habilitado. Próximo disparo indicado por systemd al verificar: 16 de noviembre de 2026, 09:00 UTC (03:00 Costa Rica). La prueba automática transitoria no se presenta como si ya hubiera ocurrido ese disparo diario futuro.

## Volumen observado

| Elemento | Cantidad |
|---|---:|
| Clientes de la tienda | 40 |
| Pedidos fuente | 241 |
| Líneas fuente | 721 |
| Líneas incluidas por estado 2/3 | 653 |
| Líneas excluidas por estado | 68 |
| Registros CRM, incluidos prospectos | 60 |
| Interacciones CRM | 180 |
| Reseñas explícitamente ficticias válidas | 180 |
| Reseñas en cuarentena | 0 |
| Subtotales inconsistentes | 0 |
| Clientes de tienda sin cruce CRM | 0 |

Los ingresos netos de productos elegibles del historial sintético sumaron CRC 3.069.475; Q1–Q5 y el agregado por segmento coincidieron. No incluyen envío ni impuestos y no se presentan como ingresos reales de una empresa.

Se generó una exportación privada de 15 tablas CSV (siete Silver y ocho Gold). Los datos, manifiestos completos, evidencias JSON y ZIP permanecen fuera del repositorio público. El hash SHA256 de cada exportación se imprime al generarla; una exportación posterior puede tener otro run_id y hash aunque sus tablas sean iguales.

## Pendientes

Crear el reporte Power BI/Tableau, configurar su acceso y refresco si se publica, implementar ML/LLM y el valor agregado acordado con el profesor. Los archivos Gold y su guía no sustituyen a un dashboard terminado. Las preguntas requieren aval docente si no se ha obtenido por otra vía.

El servicio permanente terranostra-etl.service también se ejecutó con su configuración definitiva: Result=success, ExecMainStatus=0, carga 20261116T045806Z-112f1240. Esa ejecución se inició manualmente para validar el servicio; el disparo automático se verificó por separado mediante el temporizador de prueba descrito arriba.
