# MCP Enterprise Template - Arquitectura

## Descripción General

El **MCP Enterprise Template** es un servidor Model Context Protocol (MCP) profesional construido siguiendo los principios de **Clean Architecture** y **Domain-Driven Design (DDD)**. Este proyecto sirve como plantilla para desarrollar servidores MCP escalables, mantenibles y seguros.

## Principios Arquitectónicos

### Clean Architecture

La arquitectura se organiza en capas independientes, cada una con responsabilidades específicas:

```
┌─────────────────────────────────────┐
│         DELIVERY LAYER              │
│    (MCP Server, Tools, Resources)   │
├─────────────────────────────────────┤
│      APPLICATION LAYER              │
│        (Use Cases/Services)         │
├─────────────────────────────────────┤
│        DOMAIN LAYER                 │
│  (Entities, Value Objects, Rules)   │
├─────────────────────────────────────┤
│     INFRASTRUCTURE LAYER            │
│  (External Services, HTTP Clients)  │
└─────────────────────────────────────┘
```

### Domain-Driven Design

- **Domain Models**: Entidades y Value Objects que representan conceptos del negocio
- **Repositories**: Interfaces para abstraer acceso a datos
- **Use Cases**: Lógica de negocio orquestada en la capa de aplicación
- **Exceptions**: Errores específicos del dominio

## Estructura de Carpetas

```
mcp-enterprise-template/
├── src/
│   ├── domain/                    # Capa de Dominio
│   │   ├── __init__.py
│   │   ├── models.py              # Entidades y Value Objects
│   │   ├── repositories.py        # Interfaces de repositorios
│   │   └── exceptions.py          # Excepciones del dominio
│   │
│   ├── application/               # Capa de Aplicación
│   │   ├── __init__.py
│   │   └── use_cases.py           # Casos de uso
│   │
│   ├── infrastructure/            # Capa de Infraestructura
│   │   ├── __init__.py
│   │   ├── config.py              # Configuración de la app
│   │   ├── logger.py              # Logging
│   │   ├── http_client.py         # Cliente HTTP async
│   │   └── repositories.py        # Implementación de repositorios
│   │
│   └── delivery/                  # Capa de Entrega
│       ├── __init__.py
│       └── mcp_server.py          # Servidor MCP
│
├── tests/
│   ├── unit/                      # Pruebas unitarias
│   │   ├── __init__.py
│   │   ├── test_use_cases.py
│   │   ├── test_models.py
│   │   └── test_http_client.py
│   │
│   ├── integration/               # Pruebas de integración
│   │   ├── __init__.py
│   │   └── test_policy_repository.py
│   │
│   └── conftest.py                # Configuración de pytest
│
├── docs/
│   └── architecture.md            # Esta documentación
│
├── .env.example                   # Plantilla de variables de entorno
├── pyproject.toml                 # Configuración de dependencias
├── main.py                        # Punto de entrada
└── README.md                      # Documentación del proyecto
```

## Componentes Principales

### 1. Capa de Dominio (`src/domain/`)

**Responsabilidades:**
- Definir entidades y valor objetos del negocio
- Establecer reglas de negocio
- Definir interfaces de acceso a datos

**Archivos:**
- `models.py`: Define `PolicyInfo` (política de seguros) y `SystemStatus`
- `repositories.py`: Define `IPolicyRepository` (interfaz)
- `exceptions.py`: Excepciones específicas del dominio

**Características:**
- Sin dependencias externas
- Código agnóstico del framework
- Fácil de testear

### 2. Capa de Aplicación (`src/application/`)

**Responsabilidades:**
- Orquestar la lógica de negocio
- Implementar casos de uso
- Coordinar entre capas

**Archivos:**
- `use_cases.py`: 
  - `GetPolicyUseCase`: Obtiene una política por ID
  - `GetCustomerPoliciesUseCase`: Obtiene todas las políticas de un cliente

**Características:**
- Casos de uso aislados y reutilizables
- Manejo de errores de dominio
- Logging de operaciones

### 3. Capa de Infraestructura (`src/infrastructure/`)

**Responsabilidades:**
- Implementar interfaces del dominio
- Gestionar conexiones externas
- Proveer configuración y logging

**Archivos:**
- `config.py`: Configuración centralizada con Pydantic Settings
- `logger.py`: Utilidades de logging
- `http_client.py`: Cliente HTTP async robusto
- `repositories.py`: Implementación de `PolicyRepository`

**Características:**
- Cliente HTTP con manejo de errores
- Configuración desde variables de entorno
- Logging detallado

### 4. Capa de Entrega (`src/delivery/`)

**Responsabilidades:**
- Implementar servidor MCP
- Definir Tools y Resources
- Manejar solicitudes del cliente

**Archivos:**
- `mcp_server.py`: Servidor MCP con:
  - **Tools**:
    - `get_policy_info`: Obtiene detalles de una política
    - `get_customer_policies`: Obtiene todas las políticas de un cliente
  - **Resources**:
    - `system://status`: Estado de salud del servidor

**Características:**
- Comunicación por stdio
- Manejo de errores robusto
- Inicialización de dependencias

## Flujo de Datos

### Ejemplo: Obtener Información de poliza 

```
MCP Client
    ↓
call_tool("get_policy_info", {"policy_id": "POL-001"})
    ↓
mcp_server.py → _handle_get_policy_info()
    ↓
GetPolicyUseCase.execute()
    ↓
PolicyRepository.get_policy()
    ↓
HttpClient.get("/policies/POL-001")
    ↓
Insurance Backend API
    ↓
Respuesta: PolicyInfo (dominio)
    ↓
JSON Response → MCP Client
```

## Patrones de Diseño Utilizados

### 1. **Dependency Injection**
- Los repositorios se inyectan en los casos de uso
- Facilita testing y cambio de implementaciones

### 2. **Repository Pattern**
- Abstrae el acceso a datos
- Permite cambiar fuentes de datos sin afectar lógica de negocio

### 3. **Use Case Pattern**
- Cada operación es un caso de uso independiente
- Facilita la reutilización y el testing

### 4. **Error Handling**
- Excepciones específicas del dominio
- Propagación de errores con contexto

## Configuración

### Variables de Entorno (.env)

```ini
# Server
SERVER_NAME=mcp-enterprise-template
SERVER_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# Insurance API
INSURANCE_API_BASE_URL=https://api.insurance-backend.example.com
INSURANCE_API_KEY=your-api-key-here
INSURANCE_API_TIMEOUT=30

# Cache (opcional)
ENABLE_CACHING=true
CACHE_TTL=3600
```

## Testing

### Pruebas Unitarias

```bash
pytest tests/unit/ -v
```

**Cobertura:**
- `test_use_cases.py`: Casos de uso con mocks
- `test_models.py`: Validación de modelos
- `test_http_client.py`: Cliente HTTP

### Pruebas de Integración

```bash
pytest tests/integration/ -v
```

**Cobertura:**
- `test_policy_repository.py`: Flujo completo de datos

### Reporte de Cobertura

```bash
pytest --cov=src --cov-report=html
```

## Extensión del Proyecto

### Agregar Nueva Tool

1. **Crear Use Case en `application/use_cases.py`**
```python
class NewFeatureUseCase:
    def __init__(self, repository):
        self.repository = repository
    
    async def execute(self, params):
        # Lógica
        return result
```

2. **Crear manejo en `delivery/mcp_server.py`**
```python
async def _handle_new_feature(param1: str) -> list[TextContent]:
    # Implementación
    pass

# Registrar en _process_tool_call
if name == "new_tool":
    return await _handle_new_feature(arguments.get("param1"))
```

3. **Agregar Tool a la lista de herramientas**
```python
Tool(
    name="new_tool",
    description="Descripción",
    inputSchema={...}
)
```

### Agregar Nuevo Resource

1. **Crear manejo en `_handle_resource_read()`**
```python
elif uri == "system://new_resource":
    return await _handle_new_resource()
```

2. **Registrar en lista de recursos**
```python
Resource(
    uri="system://new_resource",
    name="New Resource",
    mimeType="application/json",
)
```

## Consideraciones de Producción

1. **Manejo de Errores**
   - Todas las excepciones se capturan y registran
   - Se devuelven errores estructurados al cliente

2. **Logging**
   - Cada operación se registra con contexto
   - Niveles configurables por variable de entorno

3. **Timeouts**
   - HTTP client tiene timeout configurable
   - Previene cuelgues indefinidos

4. **Validación**
   - Pydantic valida todos los datos
   - Schemas JSON para inputs de tools

5. **Seguridad**
   - API keys en variables de entorno
   - HTTPS recomendado para APIs externas
   - Type hints para validación estática



