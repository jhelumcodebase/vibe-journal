# vibe-journal

Simple ReAct agent

Agent generated with `agents-cli` version `0.5.0`

VibeJournal is an interactive, enterprise-grade AI & Software Engineering mentoring application. Powered by a Google ADK 2.0 multi-agent workflow graph, the system dynamically audits user technical skills, provides tailored mock interview questions with grading keys, and tracks learning progress over time.

Key Features:
ADK 2.0 Multi-Agent Workflow: Sequential execution chain utilizing gemini-2.5-flash for mentor responses and gemini-2.5-pro for skill audit and interview coaching.
Thread-Safe Live Streaming: Decoupled async background execution thread ensuring zero event-loop conflicts with the Streamlit frontend.
Persistent Logging: Asynchronous FirestoreLoggerPlugin to log conversation details and structured Pydantic schemas without blocking UI performance.
Global Load Routing: Built-in exponential backoff retries and global location init to safely handle Gemini rate limits and Vertex AI quotas.

## Project Structure

```
vibe-journal/
├── app/         # Core agent code
│   ├── agent.py               # Main agent logic
│   ├── fast_api_app.py        # FastAPI Backend server
│   └── app_utils/             # App utilities and helpers
├── tests/                     # Unit, integration, and load tests
├── GEMINI.md                  # AI-assisted development guide
└── pyproject.toml             # Project dependencies
```

> 💡 **Tip:** Use [Gemini CLI](https://github.com/google-gemini/gemini-cli) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## 📐 Architecture & System Design

For a detailed look at VibeJournal's multi-agent graph design, thread-safe background streaming model, and database logging topology, see the [System Design Document](file:///Users/jhelumprakash/Documents/Personal%20Agentic%20Project/VibeJournal/vibe-journal/SYSTEM_DESIGN.md).

For the full history of prompts used to generate and deploy this project step-by-step, see the [Replication Prompt Log](file:///Users/jhelumprakash/Documents/Personal%20Agentic%20Project/VibeJournal/vibe-journal/PROMPTS.md).

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)


## Quick Start

Install `agents-cli` and its skills if not already installed:

```bash
uvx google-agents-cli setup
```

Install required packages:

```bash
agents-cli install
```

Test the agent with a local web server:

```bash
agents-cli playground
```

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more — see `agents-cli eval --help`) |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                                        |
| `agents-cli deploy`  | Deploy agent to Cloud Run                                                                   |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `app/agent.py` and test with `agents-cli playground` - it auto-reloads on save.

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.
