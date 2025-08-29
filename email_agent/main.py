from agents import Agent, Runner, trace, function_tool
from guardrail_agent import guardrail_agent, guardrail_filter_email_body
from formatter_agent import formatter_agent, formatter_tool
import os
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import asyncio

# Load keys from environment variables
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
CV_FILE_PATH=os.getenv("CV_FILE_PATH")

@function_tool
def send_email_with_attachment(to_email: str, subject: str, body: str):
    """Send an email via SendGrid with an attachment"""
    message = Mail(
        from_email="schreiber.felipe@poli.ufrj.br",
        to_emails=[to_email,"schreiber.felipe@gmail.com"],
        subject=subject,
        plain_text_content=body
    )

    # Encode file
    with open(CV_FILE_PATH, "rb") as f:
        data = f.read()
        encoded_file = base64.b64encode(data).decode()

    # Create attachment
    attached_file = Attachment(
        FileContent(encoded_file),
        FileName(os.path.basename(CV_FILE_PATH)),
        FileType("application/pdf"),
        Disposition("attachment")
    )

    message.attachment = attached_file

    # Send via SendGrid
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    return response.status_code

EMAIL_AGENT_INSTRUCTIONS = """
You are Felipe's email_agent. YOU ALWAYS CALL email_pipeline TOOL TO SEND EMAILS.
Your sole purpose is to send Felipe's Curriculum Vitae (CV) to recruiters who contact him about job opportunities.
When a recruiter provides their name, email, and job role:
    You extract the recruiter's email, role, and any context about the opportunity from their message.
    You call the email_pipeline function with:
    - name: the recruiter's name
    - to_email: the recruiter's email address
    - subject: the role or opportunity name

Example:  
If the recruiter message is:  
*"Hi, I'm Maria from Deloitte, interested in a Data Analyst role. My email is maria.hr@deloitte.com"*  
You extract:  
- recruiter_name = "Maria"
- to_email = "maria.hr@deloitte.com"
- subject = "Data Analyst role"
You then call:
email_pipeline(to_email=to_email, recruiter_name=recruiter_name, opportunity=subject)
"""

handoff_description = """
The email_agent specializes in handling recruiter contacts.
It accepts recruiter details (email, role, and message context) and sends Felipe's Curriculum Vitae (CV) 
to the recruiter as a PDF attachment via SendGrid.
"""

# ---------- EMAIL AGENT (workflow enforced here) ----------
@function_tool
def email_pipeline(recruiter_name: str, to_email: str,  subject: str) -> str:
    """Strict workflow: draft → guardrail → format → send"""

    # Step 1: Draft body
    drafter = Agent(name="Drafter", model="gpt-4.1-mini")
    draft_runner = Runner(drafter)
    with draft_runner.run(
        f"Draft a polite email acknowledging the recruiter {recruiter_name} and the {subject} opportunity."
    ) as stream:
        draft = "".join([e.delta for e in stream if e.type == "response.output_text.delta"])

    # Step 2: Guardrail filter
    clean_body = guardrail_filter_email_body(draft)

    # Step 3: Format
    formatted_body = formatter_tool(clean_body)

    # Step 4: Send
    status = send_email_with_attachment(to_email, subject, formatted_body)
    return f"Email sent with status: {status}"

# Wrap pipeline as an agent so it can be handed off
email_agent = Agent(
    name="email_agent",
    model="gpt-4.1-mini",
    tools=[email_pipeline],
    instructions=EMAIL_AGENT_INSTRUCTIONS,
    handoff_description=handoff_description
)

async def main():
    # Example: Ask agent to send CV
    messages="Hello, my name is Luiza and I would like to talk about Data Science Specialist\
        opportunity at McKinsey. Send an email to schreiber.felipe@gmail.com if you are interested. Thank you!"

    with trace("Sending an email"):
        result = await Runner.run(email_agent,messages)
        print(result.final_output)
    
if __name__ == "__main__":
    asyncio.run(main())