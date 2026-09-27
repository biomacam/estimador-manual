# Estimator CAG - Servicio de Estimacion de Software con IA

Servicio de estimacion de proyectos de software impulsado por IA, utilizando una arquitectura **Cache Augmented Generation (CAG)**.

## Que es CAG y por que lo usamos

CAG (Cache Augmented Generation) es un patron de arquitectura donde el contexto relevante se inyecta directamente en el prompt del LLM como texto estatico. En esta fase del proyecto, las estimaciones de referencia se incluyen como ejemplos dentro del prompt del sistema, sin necesidad de una base de datos vectorial ni busqueda semantica.

Este enfoque es ideal para empezar porque:
- Es simple de implementar y depurar
- No requiere infraestructura adicional (ni embeddings, ni vector stores)
- Funciona bien cuando el volumen de contexto es manejable (pocos ejemplos)

En modulos posteriores del master, este servicio evolucionara a una arquitectura **RAG** (Retrieval Augmented Generation) con base de datos vectorial para manejar un volumen mayor de ejemplos.

## Requisitos previos

- **Docker** y **Docker Compose** instalados
- Una **API key** de OpenAI o Anthropic
- Python **NO** es necesario localmente — todo se ejecuta dentro del contenedor

## Inicio rapido con Docker (recomendado)

1. Clonar el repositorio y entrar al directorio:
   ```bash
   cd estimator
   ```

2. Copiar el archivo de variables de entorno y configurar las API keys:
   ```bash
   cp .env.example .env
   # Editar .env y poner tu API key real
   ```

3. Construir y levantar el servicio:
   ```bash
   docker compose up --build
   ```

4. El servicio estara disponible en `http://localhost:8000`

## Alternativa: ejecucion local sin Docker

```bash
uv sync
# Configurar .env con tus API keys
uv run uvicorn app.main:app --reload
```

## Probar el servicio

```bash
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "transcription": "The client wants to build a mobile app for managing restaurant reservations. They need user registration, a restaurant search with filters by cuisine and location, a real-time reservation system with availability checking, push notifications for reservation confirmations and reminders, and an admin panel for restaurant owners to manage their listings and view analytics."
  }'
```

## Estructura del proyecto

```
estimator/
├── app/
│   ├── main.py            # Aplicacion FastAPI, health check, CORS
│   ├── config.py           # Configuracion con Pydantic Settings
│   ├── routers/
│   │   └── estimations.py  # Endpoint POST /api/v1/estimate
│   ├── services/
│   │   └── llm_service.py  # Logica de negocio, llamadas al LLM
│   ├── schemas/
│   │   └── estimation.py   # Modelos Pydantic (request/response)
│   └── context/
│       └── examples.py     # Ejemplos de estimacion (contexto CAG)
├── tests/
│   └── test_health.py      # Tests basicos
├── Dockerfile              # Build multi-stage con uv
├── docker-compose.yml      # Configuracion para desarrollo local
└── pyproject.toml          # Dependencias y configuracion
```

## Documentacion interactiva

Con el servicio corriendo, accede a la documentacion Swagger UI en:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

> Este proyecto forma parte del **Master en AI Engineering** y servira como base para evolucionar hacia una arquitectura RAG con base de datos vectorial en modulos posteriores.

## Arquitectura

Este proyecto sigue una arquitectura en capas (Layered Architecture) con un patrón CAG (Context Augmented Generation) en la capa de negocio.

```mermaid
graph TB
    subgraph L1["1. Bootstrap"]
        MAIN[main.py<br/>FastAPI app, lifespan, logging, CORS]
    end

    subgraph L2["2. Presentation"]
        ROUTER["routers/estimations.py<br/>POST /api/v1/estimate"]
    end

    subgraph L3["3. Contract / DTO"]
        SCHEMA["schemas/estimation.py<br/>EstimationRequest / EstimationResponse"]
    end

    subgraph L4["4. Business Logic"]
        SERVICE["services/llm_service.py<br/>generate_estimation / build_system_prompt"]
    end

    subgraph L5["5. Context (CAG)"]
        CONTEXT["context/examples.py<br/>ESTIMATION_EXAMPLES"]
    end

    subgraph L7["7. External Providers"]
        OPENAI[("OpenAI API")]
        ANTHROPIC[("Anthropic API")]
    end

    subgraph CROSS["6. Cross-cutting"]
        CONFIG["config.py<br/>Settings / get_settings()"]
    end

    MAIN --> ROUTER
    ROUTER --> SCHEMA
    ROUTER --> SERVICE
    SERVICE --> CONTEXT
    SERVICE --> OPENAI
    SERVICE --> ANTHROPIC
    ROUTER -.-> CONFIG
    SERVICE -.-> CONFIG
    MAIN -.-> CONFIG
```
## Versión añadiendo Streamlit

```mermaid
graph TB
    subgraph Clients["Driving Adapters (entry points)"]
        A1["Postman / curl"]
        A2["streamlit_app.py<br/>(st.chat_message, st.session_state)<br/><i>NUEVO</i>"]
    end

    subgraph API["API Layer — app/main.py + app/routers/"]
        B1["FastAPI app<br/>(main.py)"]
        B2["estimations.py<br/>POST /api/v1/estimate<br/>GET /health"]
    end

    subgraph Schemas["Schema Layer — app/schemas/"]
        C1["estimation.py<br/>EstimationRequest / EstimationResponse / UsageInfo"]
    end

    subgraph Services["Service Layer — app/services/"]
        D1["llm_service.py"]
        D2["build_system_prompt()"]
        D3["generate_estimation()<br/>(bloqueante)"]
        D4["stream_estimation()<br/><i>NUEVO — yield chunks</i>"]
        D5["_call_openai / _call_anthropic<br/>_stream_openai / _stream_anthropic"]
        D6["LLMServiceError"]
    end

    subgraph Context["Context/Config Layer"]
        E1["context/examples.py<br/>ESTIMATION_EXAMPLES<br/>format_examples_for_prompt()"]
        E2["config.py<br/>Settings + get_settings()<br/>@lru_cache"]
    end

    subgraph External["Proveedores externos"]
        F1["OpenAI API<br/>gpt-4o-mini"]
        F2["Anthropic API<br/>claude-haiku-4-5"]
    end

    subgraph EnvLayer["Configuración / Secretos"]
        G1[".env<br/>OPENAI_API_KEY / ANTHROPIC_API_KEY<br/>(nunca hardcodeado)"]
    end

    A1 -->|HTTP JSON| B1
    B1 --> B2
    B2 -->|valida request/response| C1
    B2 -->|llama servicio| D3
    B2 -.->|catch LLMServiceError| D6

    A2 -->|import directo, sin HTTP| D2
    A2 -->|import directo| D4
    A2 -->|lee para el sidebar| E1
    A2 -->|lee para el sidebar| E2

    D3 --> D2
    D4 --> D2
    D2 -->|inyecta ejemplos CAG| E1
    D3 --> D5
    D4 --> D5
    D1 --> E2

    D5 --> F1
    D5 --> F2

    E2 --> G1

    style A2 fill:#fff3cd,stroke:#856404
    style D4 fill:#fff3cd,stroke:#856404
    style D5 fill:#fff3cd,stroke:#856404
```

Puntos clave del diagrama:

streamlit_app.py es un nuevo adapter de entrada (igual que Postman/curl vía FastAPI), pero en lugar de pasar por HTTP importa directamente las funciones de llm_service.py — coherente con la arquitectura por capas, sin necesidad de un puerto/adapter formal.
build_system_prompt() se reutiliza sin cambios en ambos flujos (FastAPI y Streamlit) — cumple el requisito "mismo system prompt que el endpoint CAG".
stream_estimation() es la única pieza nueva en la capa de servicio: un generador que hace yield de chunks, usado solo por Streamlit (FastAPI sigue usando la versión bloqueante generate_estimation()).
config.py/.env siguen siendo el único punto de verdad para las API keys — tanto FastAPI como Streamlit leen get_settings(), nunca hardcodean la key.
El sidebar de Streamlit (requisito 3) lee directamente de context/examples.py y config.py, sin pasar por la capa de servicio.