# Terra Nostra en Azure

Tienda: https://vintara-if6201-508832.westus2.cloudapp.azure.com/
Panel: https://vintara-if6201-508832.westus2.cloudapp.azure.com/admin/
Las credenciales exclusivas de Azure se guardan en private/ACCESO-AZURE.txt. No son las del entorno local.

## Recursos
- Suscripción: Azure subscription 1 (Free Trial, límite de gasto conservado).
- Grupo: rg-vintara.
- Región de la VM y almacenamiento: West US 2.
- VM: vm-terra-nostra, tamaño Standard_B2s_v2 (2 vCPU, 8 GB RAM), Ubuntu 24.04.
- Disco del sistema: Standard SSD de 32 GiB; los volúmenes de Docker se guardan allí.
- Aplicación: Phoenix Cart + MySQL 8.0 + Caddy para HTTPS automático.
- Cuenta de almacenamiento: stterranostra508832, StorageV2 con Data Lake Gen2 habilitado.
- Contenedor privado backups para copias de MySQL.

## Conexión con el enunciado
La aplicación y la base transaccional están alojadas en Azure. MySQL no se expone públicamente.
Un futuro extractor ejecutado dentro de la VM puede leer MySQL y escribir en el Data Lake mediante identidad administrada, sin abrir el puerto 3306.
El CRM ya está creado como base separada terra_nostra_crm en el mismo servidor MySQL. Contiene 40 clientes vinculados a la tienda, 20 prospectos y 180 interacciones. Archivos CSV, ETL diario, Power BI e IA siguen pendientes. Consulta ../crm/README.md.
El respaldo diario no sustituye al proceso ETL del proyecto.

## Operación
- Abrir-Azure.cmd en la carpeta principal abre la tienda.
- Iniciar-VM.cmd en esta carpeta inicia la VM si fue detenida.
- Detener-VM.cmd desasigna la VM: la tienda deja de estar disponible y no se ejecutan sus tareas programadas.
- Los comandos de esta carpeta requieren Azure CLI y una sesión autorizada.
- Desasignar evita el cargo de cómputo; el disco y la IP pública pueden seguir generando cargos.
- No eliminar VM, disco, grupo o volúmenes si se quiere conservar esta instalación.

## Costos
Estimación orientativa de lista al desplegar: alrededor de USD 67/mes con cómputo encendido 24/7, disco Standard SSD de 32 GiB e IP pública Standard, más el uso de almacenamiento y tráfico. No es una factura ni una garantía del crédito restante; beneficios de cuenta y uso real pueden cambiar el cargo.
Se mantiene el límite de gasto de la prueba gratuita. No se realizó conversión a pago por uso.
Revisar saldo y fecha de vencimiento en Azure Cost Management. No asumir que los USD 200 se renuevan mensualmente.

## Archivos del servidor
Carpeta /opt/terra-nostra. Compose: azure/compose.yaml. Variables privadas: azure/cloud.env.
La clave SSH local está en private/terra-nostra y el host verificado en private/known_hosts.
SSH está limitado a la IP pública que tenía esta computadora al desplegar. Si cambia la conexión, actualizar la regla AllowSSHFromOwner desde Azure.
El acceso público a la tienda usa únicamente 80/443. La base permanece en la red de Docker.

## Respaldos
azure/backup.py usa la identidad administrada de la VM para subir una copia SQL comprimida de phoenix y terra_nostra_crm al contenedor privado backups.
La programación es a las 08:00 UTC (02:00 de Costa Rica) diariamente mientras la VM permanezca encendida.
Registros: /var/log/terra-nostra-backup.log. Se conserva una semana de copias locales; las de Azure se conservan fuera de la VM.
El permiso de la VM se limita a Storage Blob Data Contributor en ese contenedor.
Las imágenes de la migración también están conservadas en el respaldo local private/images.tar.gz; la programación diaria actual respalda MySQL, no imágenes nuevas que se carguen después.

## Reproducibilidad
cloud-init.yaml instala Docker. deploy.sh restaura la base y las imágenes y arranca la aplicación.
No volver a ejecutar deploy.sh sobre la tienda con actividad nueva: restaura la copia inicial y sobrescribe la base. Para cambios de código, reconstruir únicamente web con Docker Compose.
Los archivos de private/ y los dumps SQL contienen información privada y no deben publicarse.

## Verificación del despliegue
- URL HTTPS pública con certificado válido y respuesta HTTP 200.
- Cookies de sesión Secure, HttpOnly y SameSite=Lax.
- Conservados el catálogo, imágenes, diseño y datos locales migrados.
- Inicio de sesión de cliente y administrador comprobados con las contraseñas nuevas de Azure.
- Compra completa con el cliente ficticio cliente01@example.test y pago contra entrega: pedido 241 por ₡4.125, sin cobro ni correo real.
- 18 productos activos, 40 clientes y 241 pedidos (240 precargados más la compra de verificación).
- Copia privada descargada de Azure Storage, hash idéntico y restauración en una base aislada: cantidades y sumas coinciden.
- MySQL sin puerto público; entrada web por 80/443 y SSH restringido a la conexión del propietario.

El proyecto permanece como entorno académico. No se configuraron cobros reales ni correo saliente. El certificado HTTPS se renueva automáticamente mientras Caddy pueda acceder a los puertos públicos y la VM esté operativa.

- Reinicio real de la VM verificado: Docker y cron activos, servicios saludables, datos y acceso administrativo conservados.


