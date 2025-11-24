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
   DATABASE_URL=postgresql://user:pass@localhost:5432/bmo
   ```

## 🏃 Usage

1. **Run the Assistant:**
   ```bash
   export PYTHONPATH=$PYTHONPATH:$(pwd)/src && poetry run python src/BMO/main.py
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

1. Create a new file in `src/BMO/skills/collection/`.
2. Inherit from `BMO_skill`.
3. Implement the `run` method and define `args_schema`.
4. Register the skill at the end of the file:
   ```python
   registry.register(MyNewSkill())
   ```
5. Import your new skill file in `src/BMO/core/orchestrator.py` to ensure it is loaded.

## 📄 License

[MIT](LICENSE)
