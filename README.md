# BMO - Assistente de IA Multi-Agente (A2A)

BMO é um Assistente de IA modular e multi-agente construído com Python, utilizando **Orquestração Hierárquica de Agentes (A2A)**. Ele aproveita o **LangGraph** para roteamento determinístico, **LiteLLM** para abstração de modelos e um **Registro de Plugins** dinâmico para habilidades (skills).

## 🚀 Principais Funcionalidades

- **Orquestração A2A Hierárquica**: Uma arquitetura poderosa de Planejador-Supervisor-Agente para resolução de tarefas complexas.
- **Agentes Especializados**:
  - 🔍 **Researcher**: Pesquisa web e verificação de fatos.
  - ✍️ **Writer**: Síntese, documentação e conversas amigáveis.
  - 💻 **Coder**: Operações de sistema, gerenciamento de arquivos e geração de código.
  - ⚖️ **Critic**: Loop contínuo de garantia de qualidade e autocorreção.
- **Otimização de Caminho Rápido (Fast Path)**: Respostas instantâneas para saudações e conversas simples, pulando o loop pesado de orquestração.
- **Sistema de Skills Modular**: Arquitetura de plugins facilmente extensível via `SkillRegistry`.
- **Integração LiteLLM**: Suporte para mais de 100 LLMs (OpenAI, Anthropic, Gemini, etc.).
- **Camada de API HTTP**: Construída com FastAPI para integração web/mobile.
- **Docker Pronto para Produção**: Builds multi-estágio, cache BuildKit e `tini` para gerenciamento robusto de processos.
- **Camada de Persistência**: Suporte para SQLite (desenvolvimento) e PostgreSQL (produção).
- **Atalhos de Automação**: `Makefile` abrangente para desenvolvimento rápido.

## 🧠 Como Funciona (Arquitetura A2A)

O BMO segue um modelo hierárquico **Agente-para-Agente (A2A)**:
1. **Planejador (Planner)**: Analisa sua entrada e cria um `ExecutionPlan` estruturado.
2. **Supervisor**: Um orquestrador LangGraph que gerencia a máquina de estados.
3. **Agentes Especializados**: Executam etapas específicas (pesquisa, código, escrita).
4. **Crítico (Critic)**: Revisa automaticamente cada saída dos agentes. Se não estiver perfeita, fornece feedback e envia o agente de volta para uma nova tentativa (até 3 vezes).

**Modo de Conversação**: Para saudações simples ou bate-papo, o BMO ativa um **Caminho Rápido (Fast Path)** que pula a revisão do Crítico, garantindo tempos de resposta de 0.5s-1s.

## 🛠️ Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/WandersonFontes/BMO.git
   cd BMO
   ```

2. **Instale as dependências:**
   ```bash
   make install
   ```

3. **Configure o ambiente:**
   ```bash
   cp template.env .env
   ```

## ⌨️ Atalhos (Makefile)

Use estes comandos para um desenvolvimento mais rápido:

- `make run`: Inicia a CLI.
- `make run-api`: Inicia o servidor da API.
- `make test`: Executa todos os testes.
- `make up`: Inicia o ambiente de produção (Postgres + API).
- `make down`: Para o ambiente de produção.
- `make logs`: Visualiza os logs do Docker.
- `make clean`: Limpa caches e arquivos temporários.
- `make help`: Mostra todos os comandos disponíveis.

## 🏃 Uso

### Modo CLI (Terminal)

1. **Execute o Assistente:**
   ```bash
   make run
   ```

2. **Execute com Persistência (Retomar Conversas):**
   ```bash
   make shell
   ```
   *Nota: Isso utiliza a sessão `interactive-shell` session.*

3. **Interaja:**
   Digite sua consulta no terminal. Use `/exit` para parar.

### Modo API (Servidor HTTP)

1. **Execute o Servidor API:**
   ```bash
   make run-api
   ```

2. **Documentação Interativa:**
   Abra `http://localhost:8000/docs` para a interface Swagger.

3. **Endpoints Principais:**
   - `POST /v1/chat`: Interação de mensagens.
   - `GET /v1/history/{session_id}`: Recuperação de contexto.

### 🐳 Produção com Docker

O BMO é otimizado para conteinerização em produção.

1. **Usando Docker Compose (PostgreSQL Persistente):**
   ```bash
   make up
   ```
   *Isso inicia o servidor API e uma instância saudável do PostgreSQL.*

2. **Ver Logs:**
   ```bash
   make logs
   ```

3. **Build Manual:**
   ```bash
   docker build -t bmo .
   ```

## 🧩 Adicionando Novas Skills

O BMO utiliza descoberta dinâmica de habilidades. Para adicionar uma nova skill:

1. Crie um novo arquivo em `src/BMO/skills/collection/` (ex: `minha_skill.py`).
2. Herde de `BMO_skill`.
3. Implemente o método `run` e o `args_schema`.
4. Registre a instância da skill:
   ```python
   from src.BMO.skills.registry import registry
   registry.register(MinhaNovaSkill())
   ```

## 📄 Licença

[MIT](LICENSE)
