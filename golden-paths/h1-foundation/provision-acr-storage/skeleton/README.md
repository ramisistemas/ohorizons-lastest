# ${{values.name}}

${{values.description}}

Infraestructura Azure generada con Terraform: un **Azure Container Registry**
y una **Storage Account** con un **Blob Container**, desplegados dentro de un
**Resource Group existente** (no se crea uno nuevo — el Service Principal de
CI/CD de la organización no tiene permiso para crear Resource Groups, solo
para gestionar recursos dentro de uno ya existente).

## Recursos que crea

| Recurso | Nombre | Configuración |
|---|---|---|
| Resource Group | `${{values.resourceGroupName}}` | Existente, no se crea |
| Container Registry | `acr${{values.name}}${{values.environment}}` | SKU Basic, admin user deshabilitado |
| Storage Account | `st${{values.name}}${{values.environment}}` | Standard/LRS, TLS 1.2 mínimo |
| Blob Container | `data` | Acceso privado |

## Primeros pasos

1. Confirmar que los secrets `AZURE_CLIENT_ID` y `AZURE_CLIENT_SECRET` le
   llegan al repo (normalmente ya están configurados a nivel de organización).
2. Confirmar que ese Service Principal tiene rol `Contributor` sobre
   `${{values.resourceGroupName}}` (o el Resource Group que hayas indicado).
3. Copiar `terraform/terraform.tfvars.example` a `terraform/terraform.tfvars`
   y ajustar valores si es necesario.
4. (Opcional) Copiar `terraform/backend.tf.example` a `terraform/backend.tf`
   si quieres que el state de Terraform quede en un backend remoto en vez de
   local al runner (recomendado si vas a volver a correr el pipeline más de
   una vez).
5. Abrir un Pull Request: el workflow ejecuta `terraform plan` automáticamente.
6. Al hacer merge a `main`, el workflow ejecuta `terraform apply`.

## Estructura

```
terraform/
  main.tf                     # data "azurerm_resource_group" (existente) + ACR + Storage Account + Blob Container
  variables.tf
  outputs.tf
  backend.tf.example          # opcional: copiar a backend.tf para state remoto
  terraform.tfvars.example    # copiar a terraform.tfvars y ajustar
.github/workflows/terraform.yaml  # plan en PR, apply en main
```
