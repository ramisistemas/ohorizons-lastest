# ${{values.name}}

${{values.description}}

Infraestructura Azure generada con Terraform: un **Azure Container Registry**
y una **Storage Account** con un **Blob Container**, listos para usarse desde
otros servicios (por ejemplo, para publicar imágenes de contenedor o guardar
artefactos/archivos).

## Recursos que crea

| Recurso | Nombre | Configuración |
|---|---|---|
| Resource Group | `rg-${{values.name}}-${{values.environment}}` | Región: `${{values.azureRegion}}` |
| Container Registry | `acr${{values.name}}${{values.environment}}` | SKU Basic, admin user deshabilitado |
| Storage Account | `st${{values.name}}${{values.environment}}` | Standard/LRS, TLS 1.2 mínimo |
| Blob Container | `data` | Acceso privado |

## Primeros pasos

1. Copiar `terraform/backend.tf.example` a `terraform/backend.tf` y completar
   con el storage account de state ya existente en la plataforma (pedirlo al
   equipo de plataforma si no lo tienes).
2. Copiar `terraform/terraform.tfvars.example` a `terraform/terraform.tfvars`
   y ajustar valores si es necesario.
3. En GitHub, configurar los secrets del repo:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`
4. Abrir un Pull Request: el workflow ejecuta `terraform plan` automáticamente.
5. Al hacer merge a `main`, el workflow ejecuta `terraform apply`.

## Estructura

```
terraform/
  main.tf                     # Resource Group + ACR + Storage Account + Blob Container
  variables.tf
  outputs.tf
  backend.tf.example          # copiar a backend.tf y completar
  terraform.tfvars.example    # copiar a terraform.tfvars y ajustar
.github/workflows/terraform.yaml  # plan en PR, apply en main
```
