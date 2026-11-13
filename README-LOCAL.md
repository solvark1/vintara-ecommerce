# Terra Nostra · Proyecto IF6201

## Abrir la tienda
- Tienda: http://localhost:8082/
- Panel administrativo: http://localhost:8082/admin/
- Usuario del panel: admin
- Contraseña: valor de ADMIN_PASSWORD en el archivo .env de esta carpeta. No es la palabra «password».

Docker Desktop debe estar abierto. Haz doble clic en Iniciar.cmd para iniciar la tienda y abrirla.
Detener.cmd detiene solamente este proyecto. Los datos se conservan en los volúmenes de Docker.

## Qué incluye
- Phoenix Cart v1.1.0.8, PHP 8.3 con Apache y una base MySQL 8.0 independiente.
- Identidad Terra Nostra: logo propio en SVG, colores verdes y crema, nueva portada y textos principales en español.
- 18 productos activos con fotos ilustrativas y 3 categorías. Los 9 ejemplos originales se conservan inactivos.
- 40 clientes ficticios de las 7 provincias de Costa Rica.
- 240 pedidos ficticios en un período de 180 días, con productos, cantidades, envío, total e historial.
- Estados: Pendiente, En preparación, Entregado y Cancelado.
- Los pedidos y clientes aparecen en el panel y alimentan las gráficas nativas de Phoenix Cart.
- Precios y pedidos expresados en colones (CRC); son cifras sintéticas. La conversión inicial usa un factor fijo de 500 colones por cada dólar anterior; no representa el tipo de cambio vigente. Impuestos simulados en cero, sin interpretación fiscal.
- En los pedidos generados el envío es de ₡1.750 o gratis desde ₡15.000; es una regla del simulador, no una configuración de tarifa de checkout.

## Dónde ver los datos
1. Entra al panel con el usuario admin.
2. La pantalla inicial muestra ventas diarias, ventas mensuales, pedidos y clientes recientes.
3. Pedidos: http://localhost:8082/admin/orders.php
4. Clientes: http://localhost:8082/admin/customers.php
5. Abre un pedido y consulta Summary, Products y Status History para ver sus detalles.

## Repetir la carga
Haz doble clic en Cargar-Datos-Demo.cmd con la tienda encendida.
La carga se ejecuta automáticamente en el primer inicio y queda registrada como terra-nostra-v1.
Volver a ejecutarla informa que ya fue cargada: no duplica registros, no altera tus ediciones y no repone registros eliminados manualmente.
Las fechas quedan ancladas al día de la primera carga (registrado en demo_seed_runs); no se inventan nuevas ventas cada día.
Para generar otra temporada o cambiar el volumen de datos se debe preparar otra versión del seeder, conservando esta carga.

## Acceso de cliente de prueba
- Correo: cliente01@example.test (también cliente02@example.test hasta cliente40@example.test).
- Contraseña: valor DEMO_CUSTOMER_PASSWORD del archivo .env.
- No confundir esta contraseña con la del administrador.
Los datos visibles no llevan etiquetas DEMO. Los correos y direcciones siguen siendo ficticios. No se envían mensajes ni se realizan cobros reales.

## Archivos y personalización
- docker/seed-demo.php: carga transaccional de los datos ficticios.
- docker/customize.php: identidad y ajustes iniciales de la tienda.
- docker/refine.php: conversión a CRC y limpieza de etiquetas visibles, aplicada una sola vez.
- branding/assets/logo.svg: logo editable.
- branding/overlay/: portada, estilos y traducciones; el código original descargado permanece en source/.
- branding/localize.py y branding/finish-localization.py: regeneran las traducciones y el menú sobre el código original.
- docker/verify-demo.php: comprueba relaciones entre tablas, totales de pedidos y cantidades esperadas.
- backups/antes-personalizacion.sql: respaldo previo a esta personalización.
- backups/terra-nostra-demo.sql: respaldo posterior con datos ficticios e identidad aplicada.

El panel y algunas pantallas de Phoenix Cart conservan textos en inglés; se personalizaron los textos principales de la tienda.
La configuración de identidad se aplica una sola vez por versión, para conservar cambios que hagas luego en el panel.
Para aplicar cambios en archivos: docker compose up -d --build --wait
Los archivos del volumen de imágenes se gestionan aparte; el logo de Terra Nostra se sincroniza en cada inicio.

## Comandos útiles desde esta carpeta
- Iniciar o reconstruir: docker compose up -d --build --wait
- Estado: docker compose ps
- Registros: docker compose logs --tail 100
- Cargar demo: docker compose exec -T web php /opt/phoenix/seed-demo.php
- Verificar demo: docker compose exec -T web php /opt/phoenix/verify-demo.php
- Detener: docker compose stop

## Persistencia y alcance
La base, imágenes, temporales y respaldos del panel se almacenan en volúmenes de Docker.
No ejecutar docker compose down -v: elimina los datos del proyecto.
La carpeta del escritorio por sí sola no incluye los datos actuales de los volúmenes; los archivos SQL en backups/ son respaldos puntuales.
.env y los respaldos contienen credenciales o hashes: no publicarlos ni subirlos a repositorios.
La tienda se publica únicamente en 127.0.0.1:8082. La base no expone un puerto de Windows.
El instalador está fuera del directorio público. Los correos están deshabilitados en la configuración local.
Antes de Azure: ajustar URL, HTTPS, secretos, respaldos y decidir si se conserva la carga demo. No es aún una tienda de producción.
El CRM, el data lake, ETL diario, Power BI e IA se implementarán en etapas posteriores.

## Verificación realizada
- Contenedores healthy, catálogo y carrito comprobados en navegador.
- Acceso administrativo, ficha de cliente, detalle y estados de pedido comprobados.
- Gráficas de ventas con datos verificadas visualmente.
- Totales de pedidos consistentes con cantidades y precios; relaciones válidas entre clientes, direcciones, pedidos y productos.
- Segunda ejecución del seeder: mismas cantidades y mismos hashes de contenido de las tablas verificadas.

