import os
from openai import OpenAI
from dotenv import load_dotenv
from agents import Agent

load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI()

EMAIL_FORMATTER_INSTRUCTIONS = """
Beautify and standardize an email body:
- Add proper salutations (e.g., "Dear [Name],") if missing.
- Proper line breaks between greeting, body, closing.
- Ensure professional, polite tone.
- Closing should be "Best regards, Felipe Schreiber Fernandes".
- Remove extra spaces and repeated newlines.
Return formatted email body only.
"""

handoff_description = """
The Formatter Agent takes a draft email body and beautifies it for professional presentation. 
It adds proper salutations, ensures correct line breaks, enforces a polite and concise tone, 
and appends a proper closing ("Best regards, Felipe Schreiber Fernandes"). 
Use this agent whenever an email body needs to be polished before sending.
Then, pass the polished body along to the send_email_with_attachment tool.
"""

# --- formatter Agent ---
formatter_agent = Agent(
    name="formatter_agent",
    instructions=EMAIL_FORMATTER_INSTRUCTIONS,
    handoff_description=handoff_description,  # guardrail tool available here
    model="gpt-4o-mini"
)

formatter_tool = formatter_agent.as_tool(tool_name="formatter_agent", tool_description=handoff_description)
