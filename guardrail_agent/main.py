from formatter_agent import formatter_agent
from agents import Agent, function_tool
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI()

EMAIL_GUARDRAIL_PROMPT = """
You are a guardrail filter for the email_agent. 
Your role is to check and rewrite the email body before it is sent. 

Strict rules:
- Be concise, polite, and professional. 
- Only mention Felipe Schreiber Fernandes in third person or as "I" (first person) if clearly responding on his behalf. 
- Never include private, speculative, or irrelevant personal details.
- Never include links unless explicitly provided in the tools or instructions. 
- Always confirm that the body thanks the recruiter and attaches the CV. 
- Do not generate promotional content, jokes, or unprofessional remarks. 
- Never insult or produce unsafe, discriminatory, or biased content.

If the draft is already professional and safe, return it unchanged. 
If it violates the rules, return a corrected version. 

Final output must ONLY be the cleaned email body, nothing else.
"""

handoff_description = """
The guardrail_agent ensures Felipe's CV emails are professional and safe.
It drafts a message to the recruiter, passes it through a guardrail filter
to enforce tone and content rules, and then sends the email with the CV attached.
Use this agent whenever recruiter contact details and job role are provided.
"""

@function_tool
def guardrail_filter_email_body(draft_body: str) -> str:
    """Apply guardrails to filter and clean the email body before sending"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": EMAIL_GUARDRAIL_PROMPT},
            {"role": "user", "content": draft_body},
        ],
        temperature=0,
    )
    return response.choices[0].message["content"].strip()


EMAIL_GUARDRAIL_INSTRUCTIONS=(
    "You are a protective layer for the email_agent."
    "Before any email is sent, you MUST call the tool guardrail_filter_email_body "
    "To ensure the message body is professional, polite, and safe."
    "Then, pass the cleaned body along to the formatter_agent."
)

# --- Guardrail Agent ---
guardrail_agent = Agent(
    name="Guardrail Agent",
    instructions=EMAIL_GUARDRAIL_INSTRUCTIONS,
    handoffs=[formatter_agent],
    handoff_description=handoff_description,
    tools=[guardrail_filter_email_body],  # guardrail tool available here
    model="gpt-4o-mini"
)