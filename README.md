<div align="center">

# LumenLab

**Plataforma educacional de letramento digital para jovens de 10 a 14 anos**

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)](https://python.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1-FF6B35?style=for-the-badge)](https://www.langchain.com/langgraph)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-FF4D4D?style=for-the-badge)](https://www.trychroma.com/)

</div>

---

## Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Arquitetura](#arquitetura)
- [Lumia — Assistente de IA](#lumia--assistente-de-ia)
- [Stack Tecnológica](#stack-tecnológica)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e Configuração](#instalação-e-configuração)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Endpoints da API](#endpoints-da-api)
- [Testes e Avaliação](#testes-e-avaliação)

---

## Sobre o Projeto

O **LumenLab** é uma plataforma web educacional voltada ao **letramento digital crítico** de adolescentes entre 10 e 14 anos. O projeto aborda temas urgentes e frequentemente ignorados no currículo escolar tradicional:

- **Cibersegurança** — phishing, engenharia social, senhas seguras e privacidade online
- **Higiene Digital** — tempo de tela, rotina consciente e bem-estar tecnológico
- **Desafios de IA** — jogos interativos para identificar deepfakes, desinformação e vieses algorítmicos
- **Lumia** — assistente socrática com IA que guia o estudante pela descoberta, sem entregar respostas prontas

A proposta pedagógica central é o **Método Socrático aplicado à IA**: a Lumia nunca fornece respostas diretas a conteúdo educacional, mas formula perguntas que levam o estudante a raciocinar de forma independente e crítica.

---

## Telas

### Dashboard — Painel do Estudante
![Dashboard do LumenLab](docs/screenshots/dashboard.png)

### Trilhas & Módulos
![Módulos do LumenLab](docs/screenshots/modules.png)

### Higiene Digital — Agenda & Metas de Tela
![Higiene Digital](docs/screenshots/digital-hygiene.png)

### Lumia — Assistente Socrática
![Chat com a Lumia](docs/screenshots/lumia-chat.png)

---

## Funcionalidades

### Autenticação
- Login com **Google OAuth 2.0** (fluxo completo via backend)
- Tokens **JWT** com expiração de 24h
- Cadastro e gerenciamento de perfil do estudante

### Módulos Educacionais
- **Cibersegurança**: conteúdos sobre ataques comuns, proteção de dados e privacidade
- **Higiene Digital**: registro de hábitos diários, controle de tempo de tela e metas semanais
- **Desafios de IA**: quiz interativo com visão computacional (OpenCV) para identificar imagens manipuladas por IA
- **Painel de Progresso**: telemetria de módulos visitados, pontuação e evolução do estudante

### Lumia — Assistente Socrática
- Pipeline **RAG** completo com busca híbrida (semântica + léxica)
- Respostas em **streaming SSE** em tempo real
- Memória de conversa persistida por sessão
- Guardrails de segurança e recusa ética para conteúdos inapropriados
- Roteamento inteligente de intenção (conceitual, hábito, emergência, chitchat)

---

## Arquitetura

O LumenLab é composto por três camadas independentes que se comunicam via API REST:

```
┌─────────────────────────────────────────────────────┐
│                   CLIENTE (React SPA)                │
│  Auth · Dashboard · Módulos · Chat SSE (Lumia)       │
└──────────────────────┬──────────────────────────────┘
                       │  HTTP / SSE
┌──────────────────────▼──────────────────────────────┐
│              BACKEND (Django REST Framework)          │
│  Authentication · Progress · Digital Hygiene         │
│  AI Challenges · Chatbot (Lumia)                     │
└──────────────────────┬──────────────────────────────┘
                       │  Python calls
┌──────────────────────▼──────────────────────────────┐
│               AI ENGINE (LangGraph + LangChain)      │
│  Guardrail → Intent Router → RAG → Lumia Generator  │
│  ChromaDB · BM25 · FlashRank · Gemini API            │
└─────────────────────────────────────────────────────┘
```

---

## Lumia — Assistente de IA

A Lumia é construída sobre um **grafo LangGraph** com nós especializados e um pipeline RAG avançado.

### Pipeline do Grafo LangGraph

```mermaid
flowchart TD
    A([Entrada do Estudante]) --> B[Guardião de Segurança\nNível de Risco]
    B -->|cola_academica| C[Recusa Socrática\nPerguntas Reflexivas]
    B -->|risco_seguranca| D[Resposta de Emergência\nCanais de Apoio]
    B -->|seguro / safe| E[Roteador de Intenções]

    E -->|pergunta_conceitual| F[Recuperador RAG]
    E -->|consulta_habito| G[Ferramentas de Hábitos]
    E -->|conversa_casual| H[Conversa Informal]

    F --> F1[MultiQuery Retriever\n3 reescritas da pergunta]
    F1 --> F2[Busca Híbrida\nChromaDB 60% + BM25 40%]
    F2 --> F3[FlashRank Reranker\nTop-3 chunks TinyBERT]
    F3 --> I[Geração Socrática\nGemini 2.5 Flash]

    G --> I
    H --> I

    I --> J([Resposta em Streaming SSE])
```

### Estratégias do Pipeline RAG

| Componente | Implementação | Finalidade |
|---|---|---|
| **Embedding** | `gemini-embedding-001` | Vetorização semântica dos documentos pedagógicos |
| **Vector Store** | ChromaDB (332 chunks) | Busca por similaridade cosseno persistida |
| **Lexical Search** | BM25 (`rank_bm25`) | Busca por palavras-chave e termos exatos |
| **Fusion** | `EnsembleRetriever` (60/40) | Combina busca semântica e busca léxica |
| **Reranker** | FlashRank `ms-marco-TinyBERT-L-2-v2` | Reordena trechos por relevância factual real |
| **Query Expansion** | `MultiQueryRetriever` (3 variantes) | Reformula dúvidas coloquiais de adolescentes |
| **Memória** | `SqliteSaver` (LangGraph) | Histórico conversacional persistente por sessão |
| **Streaming** | Django `StreamingHttpResponse` + SSE | Respostas reativas palavra por palavra |
| **LLM** | `gemini-2.5-flash` | Geração socrática das respostas reflexivas |

### Roteamento de Intenção

```
pergunta_conceitual (concept_question) → RAG híbrido + geração socrática
consulta_habito     (habit_query)      → Ferramentas de rotina/tela + LLM
conversa_casual     (casual_chat)      → Diálogo amigável sem RAG
risco_seguranca     (safety_risk)      → Protocolo de emergência imediato (SaferNet, 188, 100)
cola_academica      (academic_cheat)   → Recusa socrática com perguntas instigantes
```

---

## Stack Tecnológica

### Backend

| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.14 | Linguagem principal |
| Django | ≥ 5.0 | Framework web e ORM |
| Django REST Framework | ≥ 3.15 | API REST |
| PostgreSQL | — | Banco de dados principal |
| django-cors-headers | ≥ 4.3 | Controle de CORS |
| python-dotenv | ≥ 1.0 | Gerenciamento de variáveis de ambiente |
| uvicorn + channels | ≥ 0.29 / ≥ 4.1 | Servidor ASGI para streaming |

### Inteligência Artificial

| Tecnologia | Versão | Uso |
|---|---|---|
| LangGraph | ≥ 0.1 | Grafo de agente socrático |
| LangChain | ≥ 0.2 | Orquestração de LLM e RAG |
| langchain-google-genai | ≥ 1.0 | Integração com Gemini API |
| ChromaDB | ≥ 0.5 | Banco de dados vetorial persistente |
| FlashRank | ≥ 0.2 | Reranker local (ms-marco-TinyBERT) |
| rank_bm25 | ≥ 0.2 | Busca léxica BM25 |
| langchain-text-splitters | ≥ 0.2 | Chunking de documentos |
| pypdf | ≥ 4.0 | Leitura e extração de PDFs |

### Frontend

| Tecnologia | Versão | Uso |
|---|---|---|
| React | 19 | Interface do usuário (SPA) |
| Vite | 6.x | Bundler e dev server |
| Lucide React | ≥ 1.16 | Biblioteca de ícones |
| JavaScript (ESM) | — | Linguagem principal do frontend |

### Infraestrutura

| Tecnologia | Uso |
|---|---|
| Docker + Docker Compose | Containerização completa do ambiente |
| PostgreSQL (container) | Banco de dados em produção |
| SQLite | Fallback e persistência de sessões LangGraph |

---

## Estrutura do Projeto

```
LumenLab/
├── backend/
│   ├── ai_engine/                   # Motor de IA — LangGraph + RAG
│   │   ├── agents/
│   │   │   ├── lumia_graph.py       # Grafo LangGraph da Lumia
│   │   │   ├── prompts.py           # Prompts de sistema (guardrail, router, etc.)
│   │   │   └── tools.py             # Ferramentas LangChain (hábitos, histórico)
│   │   ├── knowledge/
│   │   │   └── RelatoriosLumenLab.pdf  # Base de conhecimento
│   │   ├── rag/
│   │   │   ├── retriever.py         # Pipeline híbrido EnsembleRetriever + FlashRank
│   │   │   └── hallucination.py     # Checagem de alucinações
│   │   └── vectorstore/
│   │       ├── chroma_store.py      # Cliente ChromaDB
│   │       └── ingest.py            # Ingestão e indexação de documentos
│   ├── apps/
│   │   ├── authentication/          # Google OAuth 2.0 + JWT
│   │   ├── chatbot/                 # Lumia — views SSE, models, urls
│   │   ├── progress/                # Telemetria de progresso pedagógico
│   │   ├── digital_hygiene/         # Hábitos e metas de tempo de tela
│   │   ├── cybersecurity/           # Módulo de cibersegurança
│   │   └── ai_challenges/           # Desafios com visão computacional
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py              # Configurações compartilhadas
│   │   │   ├── development.py       # Configurações de desenvolvimento
│   │   │   └── production.py        # Configurações de produção
│   │   └── urls.py                  # Roteamento principal da API
│   ├── data/
│   │   ├── chroma_db/               # Vetores persistidos do ChromaDB (332 chunks)
│   │   ├── flashrank_cache/         # Cache local do modelo de reranking
│   │   └── lumia_sessions.db        # Sessões LangGraph (SqliteSaver)
│   ├── scripts/
│   │   └── generate_qa_evaluation.py  # Geração de pares QA para avaliação do RAG
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── features/
│   │   │   ├── auth/                # Telas de login e OAuth
│   │   │   ├── dashboard/           # Painel principal do estudante
│   │   │   ├── lumia-assistant/     # Chat SSE com a Lumia
│   │   │   ├── cybersecurity/       # Módulo de cibersegurança
│   │   │   ├── social-hygiene/      # Módulo de higiene digital
│   │   │   ├── ai-hub/              # Desafios de IA
│   │   │   └── modules/             # Listagem dos módulos
│   │   ├── services/
│   │   │   └── api.js               # Serviço HTTP + SSE para a API
│   │   └── App.jsx                  # Roteamento SPA principal
│   ├── package.json
│   └── vite.config.js
├── docker/
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── postgres/
│       └── init.sql
├── docker-compose.yml
├── docs/
├── .env.example
├── SETUP_CHATBOT.md
└── README.md
```

---

## Pré-requisitos

Certifique-se de ter instalado em sua máquina:

- **Python** ≥ 3.11 (preferencialmente 3.14)
- **Node.js** ≥ 18 e **npm** ≥ 9
- **PostgreSQL** ≥ 15 (opcional — SQLite funciona para desenvolvimento)
- Uma **chave de API do Google Gemini** (obtenha em [Google AI Studio](https://aistudio.google.com/))
- Credenciais de **Google OAuth 2.0** (console do Google Cloud)

---

## Instalação e Configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/lumenlab.git
cd lumenlab
```

### 2. Configurar o Backend

```bash
cd backend

# Criar e ativar o ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp ../.env.example ../.env
```

Edite o arquivo `.env` na raiz do projeto (veja a seção [Variáveis de Ambiente](#variáveis-de-ambiente)).

Crie também um `.env` dentro de `backend/` com:

```env
DJANGO_SETTINGS_MODULE=config.settings.development
```

### 4. Aplicar migrações do banco de dados

```bash
# Dentro de backend/, com .venv ativo
python manage.py migrate
```

### 5. Indexar a base de conhecimento no ChromaDB

> **Atenção:** Este passo consome a cota da API Gemini para gerar embeddings. Execute apenas uma vez (ou quando a base de conhecimento mudar).

```bash
python ai_engine/vectorstore/ingest.py
```

A ingestão processa o PDF em `ai_engine/knowledge/`, divide em chunks de 500 tokens com overlap de 50 e indexa tudo no ChromaDB em `data/chroma_db/`.

### 6. Iniciar o servidor backend

```bash
python manage.py runserver
# API disponível em http://localhost:8000
```

### 7. Configurar e iniciar o Frontend

```bash
cd ../frontend

# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm run dev
# Frontend disponível em http://localhost:5173
```

### 8. (Opcional) Executar com Docker Compose

Para subir todo o ambiente (backend + frontend + PostgreSQL) de uma só vez:

```bash
# Na raiz do projeto
docker compose up --build
```

---

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | Chave da API do Google Gemini (chat + embeddings) |
| `GOOGLE_CLIENT_ID` | ✅ | Client ID do Google OAuth 2.0 |
| `GOOGLE_CLIENT_SECRET` | ✅ | Client Secret do Google OAuth 2.0 |
| `SECRET_KEY` | ✅ | Chave secreta do Django (gerada automaticamente em dev) |
| `DEBUG` | ⬜ | `True` para desenvolvimento, `False` para produção |
| `DATABASE_URL` | ⬜ | URL de conexão PostgreSQL (ex: `postgresql://user:pass@localhost:5432/lumenlab`) |
| `ALLOWED_HOSTS` | ⬜ | Hosts permitidos (ex: `localhost,127.0.0.1`) |
| `CORS_ALLOWED_ORIGINS` | ⬜ | Origens CORS permitidas (ex: `http://localhost:5173`) |
| `DJANGO_SETTINGS_MODULE` | ✅ | Módulo de settings ativo (ex: `config.settings.development`) |

> **Nunca** versione o arquivo `.env` com suas credenciais reais. O arquivo `.gitignore` já está configurado para ignorá-lo.

---

## Endpoints da API

A API oferece roteamento bilíngue (português brasileiro e inglês):

### Autenticação — `/api/autenticacao/` (ou `/api/auth/`)

| Método | Endpoint | Descrição | Autenticação |
|---|---|---|---|
| `POST` | `/api/autenticacao/google/` ou `/api/auth/google/` | Login via token Google OAuth 2.0 | Pública |
| `POST` | `/api/autenticacao/cadastro/` ou `/api/auth/register/` | Cadastro de novo estudante | Pública |
| `GET` | `/api/autenticacao/perfil/` ou `/api/auth/profile/` | Perfil do estudante autenticado | JWT |
| `GET` | `/api/autenticacao/configuracao/` ou `/api/auth/config/` | Configurações públicas do OAuth | Pública |

### Progresso & Navegação — `/api/progresso/` (ou `/api/`)

| Método | Endpoint | Descrição | Autenticação |
|---|---|---|---|
| `GET` | `/api/progresso/estado/` ou `/api/state/` | Progresso geral do estudante nas trilhas | Pública |
| `POST` | `/api/progresso/navegacao/alternar/` ou `/api/navigation/switch/` | Telemetria de mudança de seção | Pública |
| `POST` | `/api/progresso/assistente/dialogo/` ou `/api/assistant/chat/` | Diálogo socrático inicial | Pública |

### Higiene Digital — `/api/higiene-digital/` (ou `/api/digital-hygiene/`)

| Método | Endpoint | Descrição | Autenticação |
|---|---|---|---|
| `GET` | `/api/higiene-digital/habitos/` ou `/api/digital-hygiene/habits/` | Listar hábitos do estudante (filtro ?data=) | JWT |
| `POST` | `/api/higiene-digital/habitos/criar/` ou `/api/digital-hygiene/habits/create/` | Criar novo hábito de foco ou online | JWT |
| `POST` | `/api/higiene-digital/habitos/alternar/` ou `/api/digital-hygiene/habits/toggle/` | Alternar conclusão do hábito | JWT |
| `POST` | `/api/higiene-digital/habitos/excluir/` ou `/api/digital-hygiene/habits/delete/` | Remover hábito da agenda | JWT |
| `GET` | `/api/higiene-digital/tempo-tela/` ou `/api/digital-hygiene/screen-time/` | Consultar metas de tempo de tela | JWT |
| `POST` | `/api/higiene-digital/tempo-tela/` ou `/api/digital-hygiene/screen-time/` | Definir/atualizar limites e proporções | JWT |

### Lumia Chatbot — `/api/chatbot/`

| Método | Endpoint | Descrição | Autenticação |
|---|---|---|---|
| `POST` | `/api/chatbot/mensagem/` ou `/api/chatbot/message/` | Enviar dúvida → streaming SSE | JWT |
| `GET` | `/api/chatbot/sessoes/` ou `/api/chatbot/sessions/` | Listar sessões de chat do usuário | JWT |
| `GET` | `/api/chatbot/sessao/<id_sessao>/` ou `/api/chatbot/session/<id_sessao>/` | Histórico completo da sessão | JWT |

#### Exemplo — Enviar mensagem para a Lumia com Streaming SSE

```bash
curl -X POST http://localhost:8000/api/chatbot/mensagem/ \
  -H "Authorization: Bearer <seu_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"mensagem": "O que é engenharia social?", "id_sessao": "opcional-uuid"}' \
  --no-buffer
```

> **Nota de compatibilidade:** O corpo da requisição aceita tanto `{"mensagem": "..."}` quanto `{"message": "..."}`, e o evento de streaming retorna identificadores em português e inglês (`tipo` / `type`, `id_sessao` / `session_id`).

---

## Testes e Avaliação

### Geração de Pares QA para Avaliação do RAG

O script `scripts/generate_qa_evaluation.py` utiliza o próprio Gemini para gerar automaticamente pares de perguntas e respostas esperadas a partir da base de conhecimento, criando um benchmark de avaliação da qualidade do pipeline RAG:

```bash
cd backend
python scripts/generate_qa_evaluation.py
```

Os resultados são salvos em `data/qa_evaluation/` no formato JSON, com campos:
- `question` — pergunta gerada
- `expected_answer` — resposta esperada (ground truth)
- `intent` — intenção classificada
- `retrieved_chunks` — trechos recuperados pelo RAG

### Verificação do sistema Django

```bash
python manage.py check
```

### Build de produção do Frontend

```bash
cd frontend
npm run build
# Artefato gerado em frontend/dist/
```

---

<div align="center">

</div>
