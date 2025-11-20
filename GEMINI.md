# Project Architecture Analysis Report

## 1. Executive Summary
This project is a robust backend application built with **FastAPI**, designed for high performance and scalability. It adheres to a strict **Layered Architecture (N-Tier)**, promoting separation of concerns, testability, and maintainability. The codebase is structured to clearly distinguish between the web interface (API), business logic (Services), and data access (Repositories).

## 2. Technology Stack
*   **Web Framework:** FastAPI (Asynchronous Python web framework)
*   **ORM / Data Layer:** SQLModel (Built on top of SQLAlchemy)
*   **Database Driver:** `asyncpg` (High-performance asynchronous PostgreSQL driver)
*   **Data Validation:** Pydantic (Integrated with FastAPI and SQLModel)
*   **Language:** Python 3.x

## 3. Architectural Patterns
The application implements a classic **Service-Repository Pattern**:

`Request` -> **API Layer** (Controller) -> **Service Layer** (Business Logic) -> **Repository Layer** (Data Access) -> **Database**

### Key Benefits observed:
*   **Decoupling:** The API layer does not know about the database. The Service layer does not know about HTTP concerns.
*   **Testability:** Services can be unit tested by mocking Repositories. API routes can be tested by mocking Services.
*   **Reusability:** Business logic in Services can be reused by different API endpoints or background tasks.

## 4. Detailed Module Analysis (`src/`)

### 4.1 Entry Point (`src/main.py`)
*   **Role:** Application bootstrapper.
*   **Responsibilities:**
    *   Initializes the `FastAPI` application instance.
    *   Configures Middleware (CORS, Authentication, Logging).
    *   Aggregates and includes routers from the `src/api` module.
    *   Manages application lifespan events (startup/shutdown).

### 4.2 API Layer (`src/api/`)
*   **Role:** The HTTP Interface (Controllers).
*   **Responsibilities:**
    *   Defines URL routes and HTTP methods (GET, POST, etc.).
    *   Handles Request/Response serialization using Pydantic schemas (`src/schemas`).
    *   Uses FastAPI's Dependency Injection (`Depends`) to acquire Service instances and Database sessions.
    *   **Example:** `src/api/conversation_routes.py` handles conversation-related endpoints.

### 4.3 Service Layer (`src/services/`)
*   **Role:** Business Logic Orchestrator.
*   **Responsibilities:**
    *   Contains the core domain logic and business rules.
    *   Calls one or more Repositories to fetch/save data.
    *   Performs data transformation and complex calculations.
    *   **Example:** `src/services/conversation_service.py` manages the lifecycle of a conversation flow.

### 4.4 Repository Layer (`src/repositories/`)
*   **Role:** Data Access Object (DAO).
*   **Responsibilities:**
    *   Encapsulates all direct database interactions (SQL queries).
    *   Uses SQLModel/SQLAlchemy sessions to perform CRUD operations.
    *   Returns Domain Models or ORM objects to the Service layer.
    *   **Example:** `src/repositories/conversation.py` handles SQL queries for conversation tables.

### 4.5 Data Models (`src/models/` & `src/schemas/`)
*   **`src/models/`:** Database Entities (ORM). Defines table structures, relationships, and column types. (e.g., `ConversationORM`).
*   **`src/schemas/`:** Data Transfer Objects (DTOs). Defines the shape of data entering and leaving the API (e.g., `CreateConversationRequest`).

### 4.6 Infrastructure (`src/db/`)
*   **Role:** Core infrastructure configuration.
*   **Responsibilities:**
    *   Database connection management (`engine`).
    *   Session factory and dependency provider (`get_async_session`).

## 5. Data Flow Example (Create Conversation)
1.  **Client** sends `POST /conversations` with JSON payload.
2.  **API Layer** (`conversation_routes.py`) receives request, validates JSON against `CreateConversationRequest` schema.
3.  **API Layer** injects `ConversationService`.
4.  **Service Layer** (`conversation_service.py`) `create_conversation` method is called.
5.  **Service Layer** applies business rules (e.g., check user limits) and calls `ConversationRepository`.
6.  **Repository Layer** (`conversation.py`) executes `INSERT` SQL statement via SQLModel session.
7.  **Database** commits the transaction.
8.  **Response** flows back up the stack, converted to `ConversationResponse` schema, and sent to Client.

## 6. Project Operational Context

### 6.1 Project Memory
*   **Active Memory**: `progress.md` (Records key decisions, task changes, completions).
*   **Archived Memory**: `progress.archive.md` (For older memory entries).
*   **Note**: Please refer to these files for the project's historical context and current status.

### 6.2 Key Project Information (from CLAUDE.md)
*   **Dependency Management**: **UV** is the recommended tool (preferred over Poetry).
    *   **Install**: `uv pip install -e ".[dev,test]"`
    *   **Test**: `uv run pytest tests/ -v`
    *   **Run**: `uv run uvicorn src.main:app --reload`
*   **Database**: PostgreSQL on Coolify with `pgvector` (Lantern) extension.
*   **Documentation Rules**: Update module docs (`docs/guides/MODULE_OVERVIEW.md`) immediately after modifying `src/` code.

### 6.3 Backend Module Documentation
For detailed backend code module explanations, please index and refer to:
`docs/guides/MODULE_OVERVIEW.md`