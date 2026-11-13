Estado actualizado: datos adaptados a Vintara (códigos VIN y notas sobre vinos). El identificador técnico de la base se conserva temporalmente. No hay panel web CRM. Ver ../VINTARA.md.

# CRM de Vintara en Azure

La base terra_nostra_crm está creada en el servidor MySQL que ya corre en la VM vm-terra-nostra.
No se creó otra VM ni un servicio adicional de base de datos. MySQL continúa sin acceso público.
La tienda sigue usando la base phoenix; el CRM no modifica sus clientes, productos ni compras.

## Datos cargados
- 60 registros CRM: 40 clientes de la tienda y 20 prospectos sin compras.
- 180 interacciones comerciales: 3 por registro CRM.
- Segmentos: Frecuente, Ocasional, Premium, Reactivación y Potencial.
- Canales de adquisición: Instagram, Facebook, Google, Recomendación, Feria local y Visita directa.
- Provincias, ciudades, canal preferido, etapa comercial y fechas de registro y contacto.
Todos los datos comerciales añadidos son ficticios. Los segmentos y canales son escenarios sintéticos para análisis, no inferencias sobre personas reales. No hay etiquetas DEMO en nombres o códigos visibles y no se envían correos ni mensajes.
El CRM guarda información comercial; no crea cuentas de acceso ni almacena contraseñas de clientes.

## Cómo se relaciona con las compras
terra_nostra_crm.customers.ecommerce_customer_id corresponde a phoenix.customers.customers_id.
Ese mismo identificador aparece en phoenix.orders.customers_id.
Los 40 clientes enlazados conservan exactamente el ID y el correo que ya tenían en la tienda.
Los prospectos tienen ecommerce_customer_id NULL y no necesitan una cuenta ni compras en la tienda.
No se copian pedidos al CRM ni se depende de una clave foránea entre fuentes: el cruce se comprueba mediante validación. Cada base mantiene su independencia para la futura extracción al data lake.
El CRM tiene su propia clave crm_customer_id, y las interacciones usan esa clave con una relación validada por MySQL.

Ejemplo del cruce:

```sql
SELECT c.crm_code, c.first_name, c.last_name, c.segment,
       c.acquisition_channel, o.orders_id, o.date_purchased,
       t.value AS total_crc
FROM terra_nostra_crm.customers AS c
JOIN phoenix.orders AS o
  ON o.customers_id = c.ecommerce_customer_id
JOIN phoenix.orders_total AS t
  ON t.orders_id = o.orders_id AND t.class = 'ot_total';
```

El cruce actual enlaza los 241 pedidos con los clientes correspondientes.
Para análisis de ingresos se deberán definir estados válidos y excluir pedidos cancelados según la pregunta de negocio.

## Tablas
- customers: datos comerciales y vínculo opcional con el e-commerce.
- interactions: historial de contactos comerciales con fecha, canal, resultado y notas.
- seed_runs: versión y fecha de la carga inicial.

## Accesos
Las credenciales están en ../azure/private/crm.env en esta computadora y en /opt/terra-nostra/azure/crm.env en la VM.
- terra_crm: leer y modificar únicamente el CRM; sin permiso sobre las compras de Phoenix.
- terra_etl: solo lectura del CRM y de phoenix, preparado para la futura extracción.
- Las tablas y versiones del esquema se mantienen con los scripts de administración, no con el usuario CRM.
Los usuarios existen dentro de MySQL; no son usuarios del panel web. No se añadió una aplicación CRM ni otra pantalla de administración.
No publicar las contraseñas, abrir 3306 ni subir archivos .env a repositorios.

## Cargar y verificar
Cargar-CRM.cmd ejecuta el seeder por SSH con la clave del proyecto. La regla SSH de Azure debe permitir la IP actual de esta computadora.
seed_crm.py se ejecuta en la VM con:

```sh
sudo python3 /opt/terra-nostra/crm/seed_crm.py
sudo python3 /opt/terra-nostra/crm/verify_crm.py
```

La versión terra-nostra-crm-v1 se carga una sola vez. Las siguientes ejecuciones conservan registros y ediciones, sin duplicarlos ni regenerarlos. Si se añaden clientes nuevos a la tienda posteriormente, no se insertarán automáticamente en el CRM: una futura sincronización deberá definir esa regla explícitamente.
No eliminar seed_runs para forzar una recarga; se debe crear otra versión de la carga si se requiere ampliar el conjunto.

## Persistencia y respaldo
Las dos bases se guardan en el volumen persistente de MySQL de la VM.
La copia diaria existente fue ampliada para incluir phoenix y terra_nostra_crm en un mismo dump, con los CREATE DATABASE y USE correspondientes.
Se sube al contenedor privado backups de Azure Storage a las 02:00 de Costa Rica mientras la VM esté encendida.
IMPORTANTE: ese dump completo debe tratarse como una restauración de ambas bases. El verificador de respaldo actualizado reescribe los nombres hacia bases temporales únicas y nunca importa el dump multibase directamente sobre phoenix para comprobarlo.

## Verificación realizada
- Cantidades, fechas, relaciones y ausencia de etiquetas visibles comprobadas.
- Inicio de sesión real con ambos usuarios MySQL y permisos de lectura/escritura comprobados.
- Las compras se cruzan con el CRM y los prospectos permanecen sin vínculo con la tienda.
- Segundo seeder: mismos registros y mismos hashes de contenido del CRM.
- Los datos de clientes, productos y pedidos de la tienda permanecieron idénticos durante la creación del CRM.
- Respaldo de las dos bases descargado y restaurado en bases temporales, con cantidades y sumas iguales al origen.

Siguiente etapa: incorporar CSV de comentarios y construir la extracción, transformación y carga diaria. La base CRM y su respaldo ya están listos; el ETL todavía no está implementado.

