from email_agent.main import EmailAgent, send_email_with_attachment
from dotenv import load_dotenv
import json
import os
import requests
import gradio as gr
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from agents import Agent, Runner, trace, function_tool 

load_dotenv(override=True)

def push(text):
    """Send a push notification via Pushover"""
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )

def build_vectorstore() -> FAISS:
    # Load PDFs
    loader = DirectoryLoader(
        "me", glob="**/*.pdf", loader_cls=PyPDFLoader, show_progress=True
    )
    docs = loader.load()

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)

    # Embed + build FAISS index
    embeddings = OpenAIEmbeddings()
    vs = FAISS.from_documents(splits, embeddings)
    return vs

# Use FAISS (kept in memory, but you can persist manually if needed)
vectorstore = build_vectorstore()
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

def _format_docs(docs) -> str:
    return "\n\n".join(d.page_content for d in docs)

# A terse, factual QA prompt typical for RAG (keep concise, don't hallucinate) 
RAG_QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a concise, factual assistant. Use ONLY the provided context. "
     "If the answer is not in the context, say you don't know."),
    ("human", "Context:\n{context}\n\nQuestion: {question}\nAnswer in <=3 sentences.")
])

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

@function_tool
def rag_search(question: str) -> str:
    """Use this tool to retrieve Felipe data about his thesis and academic/professional projects"""
    docs = retriever.invoke(question)
    context = _format_docs(docs)
    messages = RAG_QA_PROMPT.format_messages(context=context, question=question)
    answer = llm.invoke(messages).content

    # Include lightweight sources (URIs or file names + page numbers if present)
    sources = []
    for d in docs:
        meta = d.metadata or {}
        src = meta.get("source") or meta.get("file_path") or "unknown"
        page = meta.get("page")
        sources.append(f"{src}" + (f" (p.{page})" if page is not None else ""))

    unique_sources = sorted(set(sources))
    # Return a compact JSON-like string so the agent can quote or rephrase as needed
    payload = {
        "answer": answer,
        "sources": unique_sources,
    }
    return json.dumps(payload, ensure_ascii=False)

@function_tool
def record_user_details(email: str, 
                        name: str = "Name not provided", 
                        notes: str = "not provided"):
    """Use this tool to record that a user is interested in being in touch and provided an email address"""
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


@function_tool
def record_unknown_question(question: str):
    """Always use this tool to record any question that couldn't be answered as you didn't know the answer"""
    push(f"{question}")
    return {"recorded": "ok"}

# --- Assemble all tools ---
tools = [record_user_details, record_unknown_question, rag_search] 


# --- Define Agent instructions ---
INSTRUCTIONS = """
You are the Recruiter Manager Agent. Felipe Schreiber Fernandes Linkedin Profile is **https://www.linkedin.com/in/felipe-schreiber/**. 

You have access to three tools and one handoff:
Tools:  
1. `record_user_details` → send Felipe a mobile notification about a recruiter's contact.  
2. `record_unknown_question` → record any question you couldn't answer as you didn't know the answer.
3. `rag_search` → retrieve Felipe's thesis, academic, and professional project information.  

Handoff:
- `EmailAgent` → send Felipe's CV as a PDF attachment to a recruiter's email address.

Your responsibilities:  
- **When a recruiter sends their name, email, and a role/job opportunity:**  
  1. Call `record_user_details` with the recruiter's name, email, and role.  
  2. Call `EmailAgent` with the recruiter's email, the role as the subject, and a polite body explaining the CV is attached.  

- **When asked about Felipe's thesis, academic, or professional projects:**  
  - Use the `rag_search` tool with the recruiter's question.  
  - Return the result from `rag_search` directly to the recruiter, possibly rephrased politely. Always include references from the `sources` field to indicate credibility.  

Guidelines:  
- Do not invent details. Always use tools to answer or act.  
- Always use polite, professional, and concise wording.  
- If a recruiter message mixes both (job opportunity + question about Felipe's background), you must **do both actions**:  
  - Notify via Pushover and send CV.  
  - Answer using `rag_search`.  

Example A — if recruiter says:  
*"Hi, I'm Maria from Deloitte, interested in a Data Analyst role. My email is maria.hr@deloitte.com"*  

You must:  
1. Call `record_user_details(email="maria.hr@deloitte.com", name="Maria", role="Data Analyst")`.  
2. Call `EmailAgent(to_email="maria.hr@deloitte.com", subject="Data Analyst", body="Dear Maria, thank you for reaching out. Please find attached my Curriculum Vitae for your consideration. Best regards, Felipe Schreiber Fernandes.")`.  

Example B — if recruiter says:  
*"Can you tell me more about Felipe's thesis?"*  

You must:  
- Call `rag_search(question="Tell me more about Felipe's thesis")` and return the answer and sources.  

Example C — if recruiter says:  
*"I'm João from Google hiring for an ML Engineer role. My email is joao@google.com. Also, what kind of NLP projects has Felipe done?"*  

You must:  
1. Call `record_user_details(email="joao@google.com", name="João", role="ML Engineer")`.  
2. Call `EmailAgent(to_email="joao@google.com", subject="ML Engineer", body="Dear João, thank you for reaching out. Please find attached my Curriculum Vitae for your consideration. Best regards, Felipe Schreiber Fernandes.")`.  
3. Call `rag_search(question="What kind of NLP projects has Felipe done?")` and return the answer with sources.

Example D — if recruiter says:
What is Felipe's girlfriend's name?
You must:
- Call `record_unknown_question(question="What is Felipe's girlfriend's name?")`.
"""

# --- Instantiate the agent ---
cv_agent = Agent(
    name="Felipe Schreiber Fernandes' Assistant",
    tools=tools,
    instructions=INSTRUCTIONS,
    handoffs=[EmailAgent],
    model="gpt-4o-mini"
)

async def chat_with_agent(message, history=None):
    if history is None:
        history = []

    with trace("Agent answering"):
        result = await Runner.run(cv_agent, message)
    return result.final_output

if __name__ == "__main__":
    gr.ChatInterface(chat_with_agent, type="messages").launch()
    