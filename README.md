# BMO - Modular AI Assistant

BMO is a modular AI Assistant built with Python, using **LangGraph** for orchestration, **LiteLLM** for model abstraction, and a dynamic **Plugin Registry** for skills.

## 🚀 Features

- **Modular Architecture**: Easily extensible skill system.
- **LangGraph Orchestration**: Robust state management and agent workflows.
- **LiteLLM Integration**: Support for 100+ LLMs (OpenAI, Anthropic, Ollama, etc.).
- **Dynamic Plugin Registry**: Automatic skill discovery.

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/WandersonFontes/BMO.git
   cd BMO
   ```

2. **Install dependencies with Poetry:**
   ```bash
   poetry install
   ```

3. **Configure Environment:**
   Create a `.env` file in the root directory:
   ```ini
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4o
   OPENAI_API_KEY=sk-your-key-here
   # DATABASE_URL=postgresql://user:pass@localhost:5432/bmo (Optional, defaults to SQLite)
   ```

## 🏃 Usage

1. **Run the Assistant:**
   ```bash
   poetry run bmo
   ```

2. **Run with Persistence (Resume Conversations):**
   To continue a previous conversation, use the `--session` argument:
   ```bash
   poetry run bmo --session minha-conversa
   ```

### 🐳 Running with Docker

You can also run BMO inside a Docker container.

1. **Using Docker Compose (Recommended):**
   ```bash
   docker compose run --rm bmo
   ```

2. **Using Docker directly:**
   ```bash
   # Build the image
   docker build -t bmo .

   # Run the container
   docker run -it --env-file .env bmo
   ```

2. **Interact:**
   Type your query in the terminal.
   - Example: *"Hello, what is the OS of this machine?"*
   - Type `exit` or `quit` to stop.

## 🧩 Adding New Skills

BMO uses dynamic skill discovery. To add a new skill:

1. Create a new file in `src/BMO/skills/collection/` (e.g., `my_skill.py`).
2. Inherit from `BMO_skill`.
3. Implement the `run` method and define `args_schema` (a Pydantic model).
4. Register the skill instance at the end of your file:
   ```python
   from src.BMO.skills.registry import registry
   registry.register(MyNewSkill())
   ```
   *Note: BMO will automatically discover and load any skill file in the collection directory.*

## 📄 License

[MIT](LICENSE)
