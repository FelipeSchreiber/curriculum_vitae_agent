from agents import Agent, Runner, trace, function_tool
from guardrail_agent import guardrail_agent
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
        to_emails=to_email,
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

EMAIL_AGENT_INSTRUCTIONS = """You are Felipe's email_agent. When a recruiter provides their name, email, and job role:
1. Draft a polite email body acknowledging the recruiter and the opportunity.
2. Pass the draft body to the guardrail_agent for cleaning.
3. Format the cleaned body using the format_email_body tool.
4. Send the cleaned body along with Felipe's CV to the recruiter.
Always ensure the CV is attached. Never bypass the guardrail step.

Example:  
If the recruiter message is:  
*"Hi, I'm Maria from Deloitte, interested in a Data Analyst role. My email is maria.hr@deloitte.com"*  

1. Write a polite draft, for example:
    Draft: "Dear Maria, thank you for reaching out. Please find attached my Curriculum Vitae for your consideration. \n\nBest regards,\n Felipe Schreiber Fernandes."
2. Call `guardrail_agent` for cleaning:
    Final Version: "Dear Maria, thank you for reaching out. Please find attached my Curriculum Vitae for your consideration. \n\nBest regards,\n Felipe Schreiber Fernandes."  
3. Call `format_email_body`:
    Formatted Body: "Dear Maria,\n\nThank you for reaching out. Please find attached my Curriculum Vitae for your consideration.\n\nBest regards,\nFelipe Schreiber Fernandes."
4. Call `send_email_with_attachment`:
    `send_email_with_attachment(to_email="maria.hr@deloitte.com", subject="Data Analyst", body="Dear Maria,\n\nThank you for reaching out. Please find attached my Curriculum Vitae for your consideration.\n\nBest regards,\nFelipe Schreiber Fernandes.")`
"""

handoff_description = """
The email_agent specializes in handling recruiter contacts.
It accepts recruiter details (email, role, and message context) and sends Felipe's Curriculum Vitae (CV) 
to the recruiter as a PDF attachment via SendGrid.

Inputs required:
- to_email (the recruiter's email address)
- subject (the role or opportunity name)
- body (the polite message body)

It ensures the CV is always attached and the response is professional.
"""

email_agent = Agent(name="Email Agent",
                    tools=[send_email_with_attachment],
                    instructions=EMAIL_AGENT_INSTRUCTIONS, 
                    handoffs=[guardrail_agent],
                    handoff_description=handoff_description,
                    model="gpt-4o-mini")




async def main():
    # Example: Ask agent to send CV
    messages="Hello, my name is Luiza and I would like to talk about Data Science Specialist\
        opportunity at McKinsey. Here is my email if you are interested: schreiber.felipe@gmail.com"

    with trace("Sending an email"):
        result = await Runner.run(email_agent,messages)
        print(result.final_output)
    
if __name__ == "__main__":
    asyncio.run(main())