# SmartBank AI Assistant

A multi-agent banking chatbot powered by LLM (Groq/Qwen). Features a **SuperAgent** that intelligently routes customer queries to specialized agents for loans, accounts, cards, and complaints.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  React UI   │────▶│  FastAPI      │────▶│   SuperAgent     │
│  (Tailwind) │◀────│  Backend      │◀────│   (Router)       │
└─────────────┘     └──────────────┘     └────────┬────────┘
                           │                       │
                           │              ┌────────┼────────┐
                           │              ▼        ▼        ▼
                    ┌──────────────┐  ┌───────┐ ┌──────┐ ┌──────────┐
                    │   Supabase   │  │ Loan  │ │ Card │ │Complaint │
                    │  (PostgreSQL)│  │ Agent │ │Agent │ │  Agent   │
                    └──────────────┘  └───────┘ └──────┘ └──────────┘
                                          │Account Agent│
                                          └─────────────┘
```

### Agents

| Agent | Responsibility |
|-------|---------------|
| **SuperAgent** | Routes queries to the right specialist, handles greetings |
| **LoanAgent** | Loan eligibility, EMI calculation, loan applications |
| **AccountAgent** | Balance inquiry, transactions, mini-statements |
| **CardAgent** | Card details, block/unblock cards, credit card statements |
| **ComplaintAgent** | File complaints, track status, escalate issues |

## Tech Stack

- **Frontend**: React 18 + Tailwind CSS + Vite
- **Backend**: Python FastAPI
- **Database**: Supabase (PostgreSQL)
- **LLM**: Groq (Qwen 3.8-27B, free tier)
- **Auth**: Supabase Auth

## Setup

### 1. Groq API Key (Free)

The Supabase database is already set up. You only need a Groq API key:

1. Go to [console.groq.com](https://console.groq.com) and create a free account (no credit card needed)
2. Go to **API Keys** → **Create API Key** → copy it

### 2. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Edit .env — replace "your-groq-api-key-here" with your Groq key
nano .env

# Run the server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Demo Credentials

After running `seed.sql`, you have 3 demo customers:
- **Rahul Sharma** (ID: 1) — has savings + current accounts, home loan, credit card
- **Priya Patel** (ID: 2) — has savings account, personal loan, credit card
- **Amit Kumar** (ID: 3) — has savings + FD accounts, education loan, blocked debit card

## Example Queries

- "What is my account balance?"
- "Am I eligible for a personal loan of 5 lakhs?"
- "Calculate EMI for a home loan of 30 lakhs at 8.5% for 20 years"
- "Show my credit card outstanding"
- "Block my debit card — I lost it"
- "I want to file a complaint about a failed transaction"
- "What's the status of my complaint?"

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── agents/          # Multi-agent system
│   │   │   ├── base.py      # Base agent with OpenAI tool-calling loop
│   │   │   ├── super_agent.py  # Router/orchestrator
│   │   │   ├── loan_agent.py
│   │   │   ├── account_agent.py
│   │   │   ├── card_agent.py
│   │   │   └── complaint_agent.py
│   │   ├── tools/           # Agent tools (DB operations)
│   │   │   ├── dispatch.py  # Generic tool dispatcher
│   │   │   ├── loan_tools.py
│   │   │   ├── account_tools.py
│   │   │   ├── card_tools.py
│   │   │   └── complaint_tools.py
│   │   ├── routes/          # FastAPI endpoints
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── domain.py
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/      # Chat UI components
│   │   ├── pages/           # Login, Signup, Chat
│   │   ├── context/         # Auth context
│   │   └── services/        # API client
│   └── package.json
└── schema/                  # SQL scripts for Supabase
    ├── bank.sql
    ├── agent.sql
    └── seed.sql
```

## License

MIT
