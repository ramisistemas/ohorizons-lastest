# Arquitectura HTTP/SSE - Diagrama Visual

## 1. Vista General del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                  MCP Enterprise Template v1.0                    │
└─────────────────────────────────────────────────────────────────┘

         ┌─────────────────────────────────────────┐
         │      Transport Layer (Configurable)      │
         ├─────────────────────────────────────────┤
         │                                          │
         │  ┌──────────────┐     ┌──────────────┐  │
         │  │ MCP/stdio    │     │ HTTP/SSE     │  │
         │  │ (Original)   │     │ (Nuevo)      │  │
         │  └──────────────┘     └──────────────┘  │
         │                                          │
         └─────────────────────────────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │     Application Layer              │
         │  - FastAPI Server                  │
         │  - HTTP Adapter                    │
         │  - SSE Manager                     │
         └──────────────────────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │    Domain Layer (Shared)           │
         │  - Use Cases                       │
         │  - Models                          │
         │  - Repositories                    │
         └──────────────────────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │   Infrastructure Layer             │
         │  - Logger                          │
         │  - Config                          │
         │  - HTTP Client                     │
         │  - Repositories Implementation     │
         └──────────────────────────────────┘
```

## 2. Flujo de Comunicación HTTP/SSE

```
┌──────────────┐                        ┌──────────────┐
│              │                        │              │
│   Cliente    │                        │    Servidor  │
│   HTTP/SSE   │                        │   HTTP/SSE   │
│              │                        │              │
└──────────────┘                        └──────────────┘
      │                                       │
      │ (1) GET /api/v1/sse/connect          │
      ├──────────────────────────────────────>│
      │                                       │
      │                                 (2) Aceptar
      │                                 Crear conexión
      │                                       │
      │                                 (3) event: status
      │<──────────────────────────────────────┤
      │  {"status": "connected",              │
      │   "connection_id": "uuid"}            │
      │                                       │
      │                                       │
      │              ┌─────────────────────┐  │
      │              │ Heartbeat Loop      │  │
      │              │ Cada 30 segundos    │  │
      │              └─────────────────────┘  │
      │                                       │
      │                                 (4) event: heartbeat
      │<──────────────────────────────────────┤
      │                                       │
      │                                       │
      │ (5) POST /api/v1/sse/message          │
      │ {"connection_id": "uuid",             │
      │  "message": {...}}                    │
      ├──────────────────────────────────────>│
      │                                       │
      │                              (6) Procesar
      │                              mensaje en
      │                              adaptador
      │                                       │
      │                              (7) Llamar
      │                              use case
      │                                       │
      │                                 (8) event: tool_result
      │<──────────────────────────────────────┤
      │  {"type": "tool_result",              │
      │   "data": {...}}                      │
      │                                       │
      │                                       │
      │ (9) Desconectar                       │
      │  (Cerrar conexión o timeout)          │
      ├──────────────────────────────────────>│
      │                                       │
      │                                 (10) Limpiar
      │                                       │
```

## 3. Estructura de Módulos

```
src/
│
├── delivery/ ........................... Capas de entrega
│   ├── mcp_server.py .................. Servidor MCP/stdio (original)
│   ├── http_server.py ................. Servidor HTTP/FastAPI (NUEVO)
│   └── http_adapter.py ................ Adaptador HTTP/SSE (NUEVO)
│
├── application/ ....................... Lógica de aplicación
│   └── use_cases.py ................... Use cases (compartido)
│
├── domain/ ............................ Lógica de dominio
│   ├── models.py ...................... Modelos de dominio
│   ├── repositories.py ................ Interfaces de repositorio
│   └── exceptions.py .................. Excepciones personalizadas
│
└── infrastructure/ .................... Implementación técnica
    ├── config.py ...................... Configuración (Settings)
    ├── logger.py ...................... Logger
    ├── http_client.py ................. Cliente HTTP
    └── repositories.py ................ Implementación de repos
```

## 4. Flujo de Procesamiento de Mensaje

```
┌─────────────────────────────────────────────────────────────┐
│ Cliente envía: POST /api/v1/sse/message                     │
│ Payload: {"connection_id": "xxx", "message": {...}}         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ HTTP Server receive_sse_message()                            │
│ - Valida connection_id                                      │
│ - Parsea body HTTP                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ HTTPSSEAdapter.parse_http_request()                          │
│ - Convierte HTTP payload → MCPMessage                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ HTTPSSEAdapter.process_message()                             │
│ - Extrae tipo de mensaje                                    │
│ - Busca handler registrado                                  │
│ - Ejecuta handler async                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Handler: _handle_get_policy_info()                           │
│ o _handle_get_customer_policies()                            │
│ - Valida argumentos                                         │
│ - Llama use case                                            │
│ - Retorna resultado o error                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ HTTPSSEAdapter.get_next_message()                            │
│ - Retrieves respuesta de cola async                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ HTTPSSEAdapter.format_sse_message()                          │
│ Convierte MCPMessage → formato SSE                           │
│ Format:                                                      │
│   event: <tipo>                                              │
│   id: <request_id>                                           │
│   data: <json>                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ SSE Connection emite evento                                  │
│ Cliente recibe por EventSource listener                      │
└─────────────────────────────────────────────────────────────┘
```

## 5. Tipos de Mensajes (MessageType)

```
┌────────────────────────────────────────────┐
│         Tipos de Mensajes MCP              │
├────────────────────────────────────────────┤
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ TOOL_CALL                            │ │
│  │ Solicitud para ejecutar herramienta  │ │
│  │ {"tool": "xxx", "arguments": {...}}  │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ TOOL_RESULT                          │ │
│  │ Resultado de herramienta ejecutada   │ │
│  │ {"result": {...}, "success": true}   │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ RESOURCE_READ                        │ │
│  │ Lectura de recurso                   │ │
│  │ {"uri": "system://status"}           │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ RESOURCE_RESULT                      │ │
│  │ Contenido del recurso                │ │
│  │ {"content": "..."}                   │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ ERROR                                │ │
│  │ Mensaje de error                     │ │
│  │ {"error": "xxx", "code": "xxx"}      │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ HEARTBEAT                            │ │
│  │ Ping para mantener viva la conexión  │ │
│  │ {"message": "ping"}                  │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ STATUS                               │ │
│  │ Información de estado                │ │
│  │ {"status": "connected", ...}         │ │
│  └──────────────────────────────────────┘ │
│                                            │
└────────────────────────────────────────────┘
```

## 6. Ciclo de Vida de una Conexión SSE

```
  (1) Cliente                  (2) Servidor
      │                            │
      │ GET /sse/connect          │
      ├───────────────────────────>│
      │                        Aceptar
      │                        Crear SSEClientConnection
      │                        Iniciar event_generator
      │                            │
      │<──────────────────────────┤
      │ event: status (welcome)    │
      │ event: heartbeat (30s)     │
      │ event: heartbeat (30s)     │
      │                            │
      │ POST /sse/message          │
      ├───────────────────────────>│
      │ (tool call)            Procesar
      │                        Ejecutar use case
      │<──────────────────────────┤
      │ event: tool_result         │
      │                            │
      │ event: heartbeat (30s)     │
      │ event: heartbeat (30s)     │
      │                            │
      │ (Desconectar o timeout)    │
      ├───────────────────────────>│
      │                        Limpiar
      │                        Del dict _connections
      │                            │
      ✓ Conexión cerrada      ✓ Recursos liberados
```

## 7. Comparación MCP/stdio vs HTTP/SSE

```
┌────────────────────┬──────────────────┬──────────────┐
│ Característica     │ MCP/stdio        │ HTTP/SSE     │
├────────────────────┼──────────────────┼──────────────┤
│ Protocolo          │ MCP 1.0          │ HTTP/1.1     │
│ Streaming          │ JSONRPC 2.0      │ Server-Sent  │
│                    │ bidireccional    │ Events       │
├────────────────────┼──────────────────┼──────────────┤
│ Transporte         │ Stdin/Stdout     │ TCP/HTTP     │
│ Puerto             │ Ninguno          │ 8000 (configurable)
├────────────────────┼──────────────────┼──────────────┤
│ Clientes           │ Aplicaciones     │ Navegadores  │
│                    │ Python/Node      │ Web, cURL    │
│                    │ C/Rust           │ JavaScript   │
├────────────────────┼──────────────────┼──────────────┤
│ Comunicación       │ Bidi (full-duplex)  │ Asimétrica  │
│                    │                     │ (HTTP+SSE)  │
├────────────────────┼──────────────────┼──────────────┤
│ Firewalls/Proxies  │ Problemático     │ Compatible   │
├────────────────────┼──────────────────┼──────────────┤
│ CORS               │ N/A              │ Soportado    │
├────────────────────┼──────────────────┼──────────────┤
│ Formato Binario    │ Soportado        │ Texto (JSON) │
└────────────────────┴──────────────────┴──────────────┘
```

## 8. Endpoints HTTP - Árbol de Recursos

```
http://localhost:8000/
│
├── /health                           [GET]
│   └─ → {"status": "healthy", ...}
│
└── /api/
    └── /v1/
        ├── /status                   [GET]
        │   └─ → {"status": "healthy", ...}
        │
        ├── /tools                    [GET]
        │   └─ → {"tools": [...]}
        │
        ├── /tools/call               [POST]
        │   ├─ Body: {"tool": "...", "arguments": {...}}
        │   └─ → Resultado de herramienta
        │
        ├── /sse/connect              [GET]
        │   └─ → Stream de eventos SSE (HTTP 200 streaming)
        │
        ├── /sse/message              [POST]
        │   ├─ Body: {"connection_id": "...", "message": {...}}
        │   └─ → {"status": "accepted", "request_id": "..."}
        │
        ├── /connections              [GET]
        │   └─ → {"total": N, "connections": [...]}
        │
        └── /connections/{connection_id}  [GET]
            └─ → {"connection_id": "...", "uptime_seconds": N, ...}
```

---

Esta documentación visual complementa los archivos Markdown y proporciona una referencia rápida de cómo funciona el sistema.

