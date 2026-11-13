# Vintara S.A. — despliegue y estado

Actualizado el 12 de noviembre de 2026 (Costa Rica).

Tienda: https://vintara-if6201-508832.westus2.cloudapp.azure.com/
Panel: https://vintara-if6201-508832.westus2.cloudapp.azure.com/admin/
Repositorio: https://github.com/solvark1/vintara-ecommerce (público, sin pipeline).

## Recursos Azure

Grupo `rg-vintara`, recursos en West US 2:
- `vm-vintara`: Ubuntu, Standard_B2s_v2, identidad administrada propia.
- `disk-vintara`: disco Standard SSD con los datos persistentes.
- `vnet-vintara` y subred `snet-vintara`.
- `nsg-vintara`: HTTP/HTTPS públicos y SSH limitado a la IP del propietario.
- `nic-vintara` y `pip-vintara` (20.3.229.69).
- `stvintara508832`: Data Lake Gen2; contenedor privado `backups`, sin acceso por claves compartidas.

El grupo anterior vacío y los siete recursos sustituidos fueron eliminados después de verificar sus reemplazos y copias. Los respaldos históricos se conservaron en el almacenamiento nuevo con nombres Vintara.

## Servidor y bases

Carpeta activa `/opt/vintara`, hostname `vm-vintara`, proyecto Docker Compose `vintara`, contenedores y volúmenes con prefijo `vintara`.
MySQL permanece dentro de Docker, sin puerto público:
- `phoenix`: base transaccional del motor Phoenix Cart, 40 clientes y 241 pedidos.
- `vintara_crm`: 60 registros y 180 interacciones; usuarios `vintara_crm` y `vintara_etl`.
Las credenciales se conservan privadas. No se modificaron contraseñas ni se habilitaron cobros o correo real.

## Validación de migración

- Copia del disco consistente con servicios detenidos antes de crear el servidor nuevo.
- 16 respaldos históricos copiados y verificados individualmente por SHA256.
- Contenido del CRM comparado íntegramente antes de retirar el esquema anterior; codificación UTF-8 conservada.
- Clientes, compras, interacciones y permisos de los usuarios CRM/ETL verificados.
- PHP validado en 254 archivos; 18 vinos activos, cuatro categorías e imágenes verificadas.
- Respaldo nuevo subido usando identidad administrada y descargado con hash idéntico.
- Restauración en bases aisladas: cantidades y suma de pedidos idénticas al origen.
- HTTPS externo respondió HTTP 200 en la nueva IP, conservando el dominio y certificado.

## Estado del curso

E-commerce y bases en Azure publicados. ETL diario de tienda + CRM + CSV, tableros Power BI/Tableau, ML/LLM y valor agregado tecnológico siguen pendientes. El respaldo diario no es ETL. El CRM es una base simulada; no tiene panel web propio.

El catálogo y el historial son académicos y sintéticos. Las compras se adaptaron al catálogo de vinos conservando importes históricos; no representan precios históricos reales de vino.

## Operación

`Actualizar-Vintara-Azure.ps1` publica código con respaldo. No ejecutar `azure/deploy.sh` sobre la instalación con actividad, pues restaura el estado inicial.
Los archivos privados de acceso, volcados y claves SSH están excluidos de Git. El acceso a GitHub y el acceso a Azure son independientes.
