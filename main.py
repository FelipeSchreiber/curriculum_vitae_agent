from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
import gradio as gr
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate

load_dotenv(override=True)

def push(text):
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

# A terse, factual QA prompt typical for RAG (keep concise, don’t hallucinate) 
RAG_QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a concise, factual assistant. Use ONLY the provided context. "
     "If the answer is not in the context, say you don't know."),
    ("human", "Context:\n{context}\n\nQuestion: {question}\nAnswer in <=3 sentences.")
])

llm = ChatOpenAI(temperature=0)

def rag_search(question: str) -> str:
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


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"{question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

rag_search_json = {
    "name": "rag_search",
    "description": "Use this tool to retrieve Felipe data about his thesis and academic/professional projects",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The user question"
            }
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json},
        {"type": "function", "function": rag_search_json}]


class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Felipe Schreiber Fernandes"
        self.linkedin = "https://www.linkedin.com/in/felipe-schreiber/"
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()


    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
Everytime someone asks you a question, use the rag_search tool to retrieve useful data.\
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    