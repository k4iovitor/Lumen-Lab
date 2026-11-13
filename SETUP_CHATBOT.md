# Lumia Chatbot — Guia de Setup

## Dependências que Precisam Ser Instaladas

Execute com conexão à internet ativa:

```bash
cd /home/KaioLima/Documentos/LumenLab/backend

# Pacotes do AI engine (ainda não instalados)
.venv/bin/pip install langchain-google-genai langchain-chroma flashrank

# Opcional: persistência de sessão em disco (SQLite)
.venv/bin/pip install langgraph-checkpoint-sqlite
```

## Configuração do `.env`

Adicione ao arquivo `/home/KaioLima/Documentos/LumenLab/.env`:

```env
GOOGLE_CLIENT_ID=seu_client_id_aqui
GEMINI_API_KEY=sua_chave_aqui
DJANGO_SETTINGS_MODULE=config.settings.development
```

> A chave pode ser obtida em: https://aistudio.google.com/app/apikey

## Passos para Iniciar o Chatbot

### 1. Executar as migrações (já feito, mas repita se resetar o banco)

```bash
cd /home/KaioLima/Documentos/LumenLab/backend
.venv/bin/python manage.py migrate
```

### 2. Ingerir os documentos PDF no ChromaDB

```bash
cd /home/KaioLima/Documentos/LumenLab/backend
.venv/bin/python ai_engine/vectorstore/ingest.py
```

Isso vai:
- Carregar o PDF condensado em `backend/ai_engine/knowledge/RelatoriosLumenLab.pdf`
- Dividir em chunks de 600 tokens com overlap de 120 e metadados por capítulo
- Gerar embeddings com `gemini-embedding-001` (Gemini)
- Persistir no ChromaDB em `backend/data/chroma_db/`

### 3. Iniciar o servidor backend

```bash
cd /home/KaioLima/Documentos/LumenLab/backend
.venv/bin/python manage.py runserver
```

### 4. (Opcional) Gerar dataset de avaliação QA

```bash
cd /home/KaioLima/Documentos/LumenLab/backend
.venv/bin/python scripts/generate_qa_evaluation.py
```

Resultados em `backend/data/qa_evaluation/`.

---

## Endpoints do Chatbot

| Método | URL | Descrição |
|--------|-----|-----------|
| `POST` | `/api/chatbot/message/` | Envia mensagem (SSE streaming) |
| `GET` | `/api/chatbot/sessions/` | Lista sessões do usuário |
| `GET` | `/api/chatbot/session/<uuid>/` | Histórico de uma sessão |

**Headers obrigatórios:** `Authorization: Bearer <jwt_token>`

**Body (POST):**
```json
{
  "message": "O que é phishing?",
  "session_id": "uuid-opcional-para-continuar-sessao"
}
```

**Resposta (SSE):**
```
data: {"type": "start", "session_id": "..."}

data: {"type": "token", "token": "O "}
data: {"type": "token", "token": "phishing "}
...
data: {"type": "done", "intent": "concept_question", "safety_level": "safe", "session_id": "..."}
```

---

## Arquitetura Implementada

```
Usuário
  |
  v
[POST /api/chatbot/message/]  ← SSE StreamingHttpResponse
  |
  v
[LangGraph: build_lumia_graph()]
  |
  ├── guardrail_node       → Classifica nível de risco (safe/warning/critical_danger)
  ├── intent_router_node   → Classifica intenção (5 categorias)
  |
  ├── [safety_risk]  → emergency_node       → Links SaferNet, Take It Down, CVV 188
  ├── [academic_cheat] → socratic_refusal_node → Perguntas socráticas
  ├── [concept_question] → rag_node         → ChromaDB + BM25 + FlashRank
  |                            ↓
  |                      generation_node    → Gemini Flash + contexto recuperado
  ├── [habit_query]   → habit_tool_node    → ScreenTimeGoal + Habit (Django ORM)
  |                            ↓
  |                      generation_node
  └── [casual_chat]  → chitchat_node      → Gemini Flash com persona Lumia
```

---

## Estrutura de Arquivos Criados

```
backend/
├── apps/chatbot/
│   ├── models.py          # ChatSession, ChatMessage
│   ├── views.py           # SSE streaming endpoint
│   ├── urls.py            # Roteamento do chatbot
│   ├── admin.py           # Admin Django
│   └── migrations/0001_initial.py
│
├── ai_engine/
│   ├── knowledge/
│   │   └── RelatoriosLumenLab.pdf # Base consolidada de conhecimento (60 págs)
│   ├── agents/
│   │   ├── lumia_graph.py  # Grafo LangGraph completo
│   │   ├── prompts.py      # Todos os prompts do sistema
│   │   └── tools.py        # Ferramentas Django (hábitos, emergência)
│   ├── rag/
│   │   ├── retriever.py    # Pipeline híbrido ChromaDB+BM25+FlashRank
│   │   └── hallucination.py # Verificação de fidelidade ao contexto
│   └── vectorstore/
│       ├── chroma_store.py  # Acesso ao ChromaDB + embeddings Gemini
│       └── ingest.py        # Script de ingestão de PDFs
│
├── scripts/
│   └── generate_qa_evaluation.py  # Geração e avaliação de dataset QA
│
└── apps/authentication/
    └── utils.py            # decode_jwt_token (utilitário compartilhado)

frontend/
└── src/
    ├── features/lumia-assistant/
    │   └── AIAssistantView.jsx  # UI do chat com SSE real
    └── services/api.js          # +askLumia, getChatSessions, getChatHistory
```
