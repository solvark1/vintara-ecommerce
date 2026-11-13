# Vintara — e-commerce de vinos

Proyecto académico IF6201: adaptación de Phoenix Cart para Vintara S.A., propuesta de R&R Technology.

Tienda publicada: https://vintara-if6201-508832.westus2.cloudapp.azure.com/

## Desarrollo local

Requiere Docker con Compose. Copiar `.env.example` a `.env`, reemplazar los cuatro valores con contraseñas propias y ejecutar:

```sh
docker compose up -d --build
```

Abrir http://localhost:8082 y http://localhost:8082/admin/ (usuario `admin`, contraseña elegida en `.env`). La primera ejecución instala la base, carga datos académicos y aplica el catálogo Vintara. No conectar este entorno de desarrollo a las bases de producción.

## Estructura

- `source/`: código base Phoenix Cart y licencia original.
- `branding/`: identidad, traducciones e imágenes de Vintara.
- `docker/`: inicialización, migraciones y verificaciones del catálogo.
- `azure/`: infraestructura y scripts operativos del despliegue actual.
- `crm/`: simulación de CRM y verificaciones.
- `VINTARA.md`: estado real, comprobaciones y pendientes del curso.

## Trabajo en equipo y Azure

Este repositorio contiene código, no acceso al servidor. Cada colaborador debe usar su propia cuenta Microsoft y permisos autorizados en `rg-vintara`; el acceso a GitHub se concede por separado. Los scripts de Azure incluyen referencias a la instalación actual y requieren claves y archivos privados que deliberadamente no se incluyen. Revisarlos antes de ejecutarlos; no ejecutar `azure/deploy.sh` sobre la tienda existente, ya que restaura el estado inicial.

No hay pipeline de despliegue ni secretos configurados en GitHub. Los cambios publicados en GitHub no se despliegan automáticamente a Azure.

## Datos y secretos

No se incluyen contraseñas, claves SSH, configuraciones generadas, copias SQL de clientes ni respaldos. Los SQL originales del instalador sí se incluyen para permitir una instalación nueva. No subir archivos de `azure/private/`, `.env`, `cloud.env` ni `crm.env`.

El catálogo y las semillas son datos ficticios para demostración. ETL diario, visualizaciones Power BI/Tableau y módulos ML/LLM siguen pendientes. Se conserva la licencia de Phoenix Cart; revisar sus condiciones antes de distribuir derivados.
