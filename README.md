# BMO - Modular AI Assistant

BMO is a modular AI Assistant built with Python, using **LangGraph** for orchestration, **LiteLLM** for model abstraction, and a dynamic **Plugin Registry** for skills.

## 🚀 Features

- **Modular Architecture**: Easily extensible skill system.
- **LangGraph Orchestration**: Robust state management and agent workflows.
- **LiteLLM Integration**: Support for 100+ LLMs (OpenAI, Anthropic, Ollama, etc.).
- **Dynamic Plugin Registry**: Automatic skill discovery.
- **HTTP API Layer**: Built with FastAPI for web/mobile integration.
- **Production-Ready Docker**: Multi-stage builds, BuildKit caching, and `tini` for robust process management.
- **Enterprise Persistence**: Support for both SQLite (local) and PostgreSQL (production).
- **Automation Shortcuts**: `Makefile` included for rapid development and orchestration.

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/WandersonFontes/BMO.git
   cd BMO
   ```

2. **Install dependencies:**
   ```bash
   make install
   ```

3. **Configure Environment:**
   ```bash
   cp template.env .env
   ```

## ⌨️ Shortcuts (Makefile)

Use these commands for faster development:

- `make run`: Starts the CLI.
- `make run-api`: Starts the API server.
- `make test`: Runs all tests.
- `make up`: Starts the production environment (Postgres + API).
- `make down`: Stops the production environment.
- `make docker-logs`: View container logs.
- `make clean`: Cleans up caches and temporary files.
- `make help`: Shows all available commands.

## 🏃 Usage

### CLI Mode (Terminal)

1. **Run the Assistant:**
   ```bash
   make run
   ```

2. **Run with Persistence (Resume Conversations):**
   ```bash
   make shell
   ```
   *Note: This uses the `interactive-shell` session.*

3. **Interact:**
   Type your query in the terminal. Use `/exit` to stop.

### API Mode (HTTP Server)

1. **Run the API Server:**
   ```bash
   make run-api
   ```

2. **Interactive Documentation:**
   Open `http://localhost:8000/docs` for the Swagger UI.

3. **Core Endpoints:**
   - `POST /v1/chat`: Message interaction.
   - `GET /v1/history/{session_id}`: Context retrieval.

### 🐳 Production with Docker

BMO is optimized for production containerization.

1. **Using Docker Compose (PostgreSQL Persistent):**
   ```bash
   make up
   ```
   *This starts the API server and a healthy PostgreSQL instance.*

2. **View Logs:**
   ```bash
   make docker-logs
   ```

3. **Manual Build:**
   ```bash
   docker build -t bmo .
   ```

## 🧩 Adding New Skills

BMO uses dynamic skill discovery. To add a new skill:

1. Create a new file in `src/BMO/skills/collection/` (e.g., `my_skill.py`).
2. Inherit from `BMO_skill`.
3. Implement the `run` method and `args_schema`.
4. Register the skill instance:
   ```python
   from src.BMO.skills.registry import registry
   registry.register(MyNewSkill())
   ```

## 📄 License

[MIT](LICENSE)
