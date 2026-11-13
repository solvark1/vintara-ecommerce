# Vintara en Azure

Consultar [VINTARA.md](../VINTARA.md) para inventario y verificaciones actuales.

Grupo: `rg-vintara`. Máquina: `vm-vintara`. IP: `20.3.229.69`.
Tienda: https://vintara-if6201-508832.westus2.cloudapp.azure.com/
Panel: https://vintara-if6201-508832.westus2.cloudapp.azure.com/admin/

El servidor guarda el proyecto en `/opt/vintara`. Docker Compose ejecuta `vintara-db-1`, `vintara-web-1` y `vintara-proxy-1`. Las bases son `phoenix` (motor de tienda) y `vintara_crm`. No se expone MySQL públicamente.

Red: `vnet-vintara`, `snet-vintara`, `nsg-vintara`, `nic-vintara`, `pip-vintara`. Disco: `disk-vintara`. Cuenta Data Lake Gen2: `stvintara508832`.

Los respaldos diarios a las 08:00 UTC (02:00 Costa Rica) se ejecutan mientras la VM esté encendida y se suben al contenedor privado `backups` mediante la identidad administrada de la VM. La identidad tiene Storage Blob Data Contributor únicamente sobre ese contenedor. No hay acceso por claves compartidas ni blobs públicos.

`Iniciar-VM.cmd` y `Detener-VM.cmd` usan el grupo y VM nuevos. Detener desasigna la VM y deja la tienda y tareas programadas fuera de servicio. Discos, almacenamiento e IP pueden generar cargos aunque la VM esté desasignada.

Para publicar código, usar `../Actualizar-Vintara-Azure.ps1`. No ejecutar `deploy.sh` sobre la instalación existente: corresponde a una restauración inicial. Las claves y variables necesarias están en `private/`, excluidas del repositorio público. No copiar secretos en issues, commits o capturas.

La tienda es académica: no realiza cobros ni envía correo real. ETL, BI e IA siguen pendientes; los respaldos no sustituyen al ETL.
