# Vintara S.A. — estado del despliegue

Actualizado el 12 de noviembre de 2026 (Costa Rica).

Tienda: https://vintara-if6201-508832.westus2.cloudapp.azure.com/
Administración: https://vintara-if6201-508832.westus2.cloudapp.azure.com/admin/

## Publicado
- Identidad borgoña, crema y dorado; logo, portada y 18 vinos en cuatro categorías.
- Fichas con uva, añada, región, bodega, alcohol, conservación y maridaje.
- Catálogo anterior retirado de navegación y ofertas; registros archivados con nombres e imágenes de vino.
- Datos académicos de compras vinculados a los vinos. Se conservan identificadores, fechas, cantidades e importes históricos; estos importes son sintéticos y no representan precios históricos reales del vino.
- 40 clientes, 241 pedidos, 60 registros CRM y 180 interacciones. CRM con códigos VIN y notas sobre vinos.
- No se alteraron contraseñas ni se habilitaron cobros o correo real.

## Validación
- Sintaxis de 254 archivos PHP y migración del catálogo ejecutadas en Azure.
- 18 fichas, cuatro categorías, precios/stock e imágenes verificados.
- Relaciones de pedidos con vinos y clientes con CRM comprobadas.
- Nueva URL con certificado HTTPS y HTTP 200.
- Portada, ficha y adición al carrito comprobadas en navegador. No se completó una nueva orden después de esta actualización.
- Copias privadas previas al despliegue y a la migración en /opt/terra-nostra/backups/.

## Nombres internos pendientes
La VM, grupo de recursos, almacenamiento, carpeta del servidor, volúmenes y base terra_nostra_crm aún conservan identificadores técnicos anteriores. No aparecen en la tienda pública. La revisión automática rechazó una operación que incluía eliminar la base CRM antigua y renombrar usuarios. Esa operación no se ejecutó. No afirmar que ya no queda ningún rastro interno.
El CRM es una base simulada, no un panel web de CRM.

## Enunciado del curso
1. E-commerce y base en Azure: publicados.
2. Data Lake: cuenta de almacenamiento existente; no equivale a un DW integrado.
3-4. ETL de tienda + CRM + CSV y ejecución automática diaria: pendiente. El respaldo diario no es ETL.
5-6. Seis preguntas y visualizaciones en Power BI o Tableau: propuesta definida; implementación pendiente.
7. Predicción ML y sentimiento con LLM: pendientes; no se muestran resultados ficticios como IA real.
8. Valor agregado (QR, sommelier o maridaje inteligente): pendiente de implementación y aval docente. Las notas estáticas de maridaje no son un motor de IA.

## Operación
Actualizar-Vintara-Azure.ps1 publica código con respaldo. azure/rebrand-vintara-data.py documenta la migración única VINTARA_DATA_V2; es idempotente. No ejecutar azure/deploy.sh: restaura el estado inicial.
Los secretos permanecen en azure/private y en el servidor, fuera del contenido público.

Grupo de recursos actualizado: rg-vintara. Los siete recursos fueron trasladados desde el grupo anterior. Los scripts Iniciar-VM y Detener-VM apuntan al grupo nuevo.

Permiso de respaldos restaurado en rg-vintara y subida privada comprobada después del traslado. Repositorio de código: https://github.com/solvark1/vintara-ecommerce (privado, sin pipeline).
