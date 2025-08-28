<h1 align="center" style="color:#ffffff;background:#111;padding:20px;border-radius:12px;">
🚀 Recruiter Manager Agent  
<span style="font-size:0.7em;color:#ccc;">Automating Felipe’s recruiter interactions</span>
</h1>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/openai-gpt--4o--mini-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/FAISS-VectorStore-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge" />
</p>

---

<div style="background:#222;color:#eee;padding:20px;border-radius:12px;margin-bottom:20px;">
<h2>✨ Overview</h2>

The **Recruiter Manager Agent** is an AI-powered assistant that manages recruiter interactions for  
<strong><a href="https://www.linkedin.com/in/felipe-schreiber/" style="color:#4ea1ff;">Felipe Schreiber Fernandes</a></strong>.

It ensures that every recruiter who reaches out:
- 📲 Triggers a **push notification** via Pushover.  
- 📧 Receives an **automatic email with Felipe’s CV** attached.  
- 📚 Can ask questions about Felipe’s **thesis, academic, and professional projects** via Retrieval-Augmented Generation (RAG).  
- 🛡️ Has sensitive or inappropriate questions safely **logged** without leaking personal data.  
- ✨ All outgoing emails are **guarded and formatted** for professionalism and safety.
</div>

---

<div style="background:#111;color:#fff;padding:20px;border-radius:12px;">
<h2>⚙️ Features</h2>

- 🔔 **Pushover Integration** – Instant recruiter notifications to Felipe’s phone.  
- 📄 **Automatic CV Delivery** – Sends Felipe’s CV as a PDF attachment via SendGrid.  
- 🛡️ **Guardrail Agent** – Ensures email bodies are safe, polite, and professional.  
- ✨ **Formatter Agent** – Beautifies email bodies, adds salutations, line breaks, and proper closing.  
- 🔎 **RAG Search** – Provides fact-based answers about Felipe’s work (thesis, NLP projects, etc.) using FAISS + OpenAI embeddings.  
- 🛑 **Unknown Question Logging** – Records any irrelevant or unanswerable recruiter queries.  
- 🤝 **Multi-step Workflows** – When recruiters both introduce a job and ask project questions, the agent handles **both actions** in parallel.
</div>

---

<div style="background:#222;color:#eee;padding:20px;border-radius:12px;">
<h2>📐 Architecture</h2>

```mermaid
graph TD
    Recruiter[Recruiter Email/Message] -->|Triggers| CVAgent
    CVAgent -->|1. Notify| Pushover
    CVAgent -->|2. Draft Email| email_agent
    email_agent -->|3. Guardrail Check| guardrail_agent
    guardrail_agent -->|4. Formatting| formatter_agent
    formatter_agent -->|5. Send CV| Send_Email
    CVAgent -->|6. Answer Questions| RAG_Search
    CVAgent -->|7. Fallback| Record_Unknown

git clone https://github.com/yourusername/recruiter-manager-agent.git
cd recruiter-manager-agent
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env  # set your API keys and email credentials
python main.py
 