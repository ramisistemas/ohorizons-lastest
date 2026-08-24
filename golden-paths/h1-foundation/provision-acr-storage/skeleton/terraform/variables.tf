variable "environment" {
  description = "Ambiente de despliegue (dev, staging, prod)"
  type        = string
}

variable "location" {
  description = "Región de Azure donde se crean los recursos"
  type        = string
  default     = "${{values.azureRegion}}"
}

variable "tags" {
  description = "Tags a aplicar a todos los recursos"
  type        = map(string)
  default     = {}
}
