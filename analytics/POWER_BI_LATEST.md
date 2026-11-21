# Power BI: última carga de Terra Nostra

## Ruta fija

Cuenta: `stvintara508832`, contenedor privado `datalake`.

- `latest/gold/`: ocho CSV agregados, incluidas las seis preguntas de negocio.
- `latest/silver/`: siete CSV de dimensiones, hechos y CRM para construir un modelo relacionado.
- `latest/manifest.json`: ejecución de origen, fecha de los datos, conteos y SHA256 de cada tabla.

La carpeta contiene solo una carga completa y conserva los mismos nombres. Las ejecuciones anteriores siguen en `gold/runs/` y `silver/runs/`; no se deben combinar con `latest`. Para arrancar los gráficos conviene usar Gold. No unir sus agregados a las filas de hechos de Silver porque se duplicarían medidas.

## Conexión de Luis

1. En Power BI Desktop: Obtener datos → Azure → Azure Data Lake Storage Gen2.
2. Introducir la URL del **contenedor**:

   `https://stvintara508832.dfs.core.windows.net/datalake`

3. Elegir Cuenta organizativa e iniciar sesión con `luis.ballar@ucr.ac.cr`, que ya tiene Storage Blob Data Owner en el proyecto. No utilizar contraseña SSH/MySQL, clave compartida ni acceso anónimo.
4. En Transformar datos, filtrar `Folder Path` para conservar únicamente `latest/gold/` y elegir el CSV de la pregunta. Conservar el filtro en la consulta para futuras actualizaciones.
5. Crear una consulta independiente por tabla; no combinar los ocho CSV en una sola tabla porque tienen esquemas diferentes. Promover encabezados y definir tipos: identificadores enteros, unidades enteras, fechas como fecha, `month` como texto y medidas CRC como decimal. El delimitador es coma y la codificación UTF-8; los números usan punto decimal.

No introducir `/latest/gold/` como URL inicial del conector: Power BI Desktop tiene una limitación documentada con subcarpetas. Se conecta al contenedor y luego se filtra. Si usa el conector Azure Blob Storage, el endpoint equivalente de la cuenta es `https://stvintara508832.blob.core.windows.net/`, y debe seleccionar `datalake` y filtrar `latest/gold/`.

## Actualización diaria

`terranostra-etl.timer` sigue programado a las **03:00 de Costa Rica (09:00 UTC)**. Al terminar correctamente, el ETL publica de nuevo `latest`. Una carga con datos inválidos o una copia fallida no debe sustituir la publicación anterior; el diario permite recuperarla tras una interrupción.

Power BI debe actualizarse después, por ejemplo a las **03:15 de Costa Rica**. La publicación de la carpeta y el refresco del reporte son tareas distintas: este cambio no publica un reporte ni configura su horario en Power BI Service. La VM debe estar encendida para ejecutar el ETL.

Si el reporte publicado pertenece al directorio de la UCR y el almacenamiento al directorio del proyecto, revisar la autenticación del refresco: Microsoft no admite OAuth2 entre directorios distintos para el refresco de ADLS Gen2. No hace falta volver públicos los datos para resolverlo.

## Comprobación en la VM

```sh
sudo python3 /opt/vintara/analytics/verify.py
sudo systemctl list-timers terranostra-etl.timer --all --no-pager
```

La verificación debe indicar `verified: true` y `latest_tables_verified: 15`, con el mismo `run_id` en `latest/manifest.json` y `latest.json`. Los CSV de `latest` se cotejan por hash y contenido con el snapshot original.

Referencias: [conector ADLS Gen2 y limitaciones de Power BI](https://learn.microsoft.com/en-us/power-query/connectors/data-lake-storage), [renombrado de directorios en ADLS Gen2](https://learn.microsoft.com/en-us/rest/api/storageservices/datalakestoragegen2/path/create).
