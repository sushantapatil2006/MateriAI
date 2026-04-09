# MateriAI 🧠

**MateriAI** is an advanced AI-powered educational tool that transforms massive texts and messy PDFs into structured, intelligent study materials instantly. It leverages ridiculously fast Llama 3 models (via [Groq](https://groq.com/)) and a secure Django backend to read, summarize, and quiz you on your reading material in seconds.

## ✨ Features

- **Document Ingestion**: Upload `.pdf` or `.txt` files or simply paste raw text.
- **Smart Chunking (Map-Reduce)**: Handled seamlessly in the backend to bypass token limitations of AI models. It chunks your document, summarizes each part, and combines them smoothly.
- **Executive Summary & Explanations**: Produces a fast, high-level summary and detailed breakdown of the document's concepts.
- **15-Question Interactive Quiz**: Uses `llama-3.3-70b-versatile` to autonomously create a comprehensive multiple-choice test. 
- **Anti-Cheat Secure Grading**: The Django backend persists your quiz securely to a database. The front-end only receives the questions and options. When you submit your exam, the backend calculates the grade and returns a detailed review of what you got wrong.
- **Premium Interface**: Built with React, Tailwind CSS, and stunning modern glassmorphism aesthetics.

## 🛠️ Tech Stack

### Frontend
- **React 18** (Vite)
- **Tailwind CSS** (Custom theme with `ink`, `mint`, `sky`, `coral`)
- **Axios** for API requests

### Backend
- **Python 3 / Django 4.2**
- **Django REST Framework (DRF)** 
- **SQLite3** for secure grading and persistence
- **pdfplumber** for reliable PDF text extraction
- **Groq API SDK** 

### AI Models
- `llama-3.1-8b-instant` for ultra-fast document chunk summarization.
- `llama-3.3-70b-versatile` for complex JSON schema enforcement and quiz generation.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- A [Groq API Key](https://console.groq.com/keys)

### 1. Clone the repository
```bash
git clone https://github.com/sushantapatil2006/MateriAI.git
cd MateriAI
```

### 2. Backend Setup
```bash
cd backend
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file inside the `backend/` directory:
```env
GROQ_API_KEY=your_groq_api_key_here
DJANGO_SECRET_KEY=your_django_secret_key_here
```

Run the server:
```bash
python manage.py makemigrations api
python manage.py migrate
python manage.py runserver 8000
```

### 3. Frontend Setup
Open a new terminal window inside the root `MateriAI` folder:
```bash
npm install
npm run dev
```

Visit `http://localhost:5173` in your browser!

## 💡 About The Architecture
MateriAI utilizes a powerful **Map-Reduce Pipeline**. Since AI models have limits on how much text they can read at once, the `ai_service.py` breaks massive PDFs into 1500-word blocks. It delegates the summarization of these chunks concurrently to a lower-latency model. Once complete, it passes the combined summary to a massive 70B parameter model to do complex reasoning and formal Quiz creation. 

## 🛡️ License
MIT License
