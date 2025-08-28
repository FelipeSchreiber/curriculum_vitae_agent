from agents import Agent, Runner, trace, function_tool
import os
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from dotenv import load_dotenv
import asyncio

load_dotenv(override=True)
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

EMAIL_AGENT_INSTRUCTIONS=("You are a curriculum vitae sender.\n"
               "Everytime a recruiter sends you it's email, name and the subject is about a job offer,\
                you are going to call the tool send_email_with_attachment."
                "The email parameter is the recruiter's email"
                "The subject is the name of the opportunity she is recruiting for"
                "The email body informs that the curriculum is attached and thanks for the opportunity"
                "Always, at the end of the email, say 'Best regards, Felipe'.\n"
                "Always use the tool to send the email, never answer directly."
            )

EMAIL_AGENT2_INSTRUCTIONS = """You are the Email Agent.  
Your sole responsibility is to send Felipe Schreiber Fernandes' Curriculum Vitae (CV) to recruiters.  

You have access to a single tool: `send_email_with_attachment(to_email, subject, body)`.  
You must **always** use this tool when you are asked to send a CV.  

- The parameter `to_email` must be set to the recruiter's email address.  
- The parameter `subject` must be the name of the job opportunity or role mentioned by the recruiter.  
- The parameter `body` must be a polite message explaining that Felipe’s CV is attached and thanking the recruiter for the opportunity.  

Follow these guidelines:  
1. Be polite, formal, and concise in the body.  
2. Do not invent or modify information.  
3. Only call the tool once per recruiter request.  
4. Do not return text directly to the user — the tool call is your final action.  

Example:  
If the recruiter message is:  
*"Hi, I'm Maria from Deloitte, interested in a Data Analyst role. My email is maria.hr@deloitte.com"*  

You must call:  
`send_email_with_attachment(to_email="maria.hr@deloitte.com", subject="Data Analyst", body="Dear Maria, thank you for reaching out. Please find attached my Curriculum Vitae for your consideration. Best regards, Felipe Schreiber Fernandes.")`
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


EmailAgent = Agent(name="Email Agent",
                    tools=[send_email_with_attachment],
                    instructions=EMAIL_AGENT2_INSTRUCTIONS, 
                    handoff_description=handoff_description,
                    model="gpt-4o-mini")


async def main():
    # Example: Ask agent to send CV
    messages="Hello, my name is Luiza and I would like to talk about Data Science Especialist\
        opportunity at McKinsey. Here is my email if you are interested: schreiber.felipe@gmail.com"

    with trace("Sending an email"):
        result = await Runner.run(EmailAgent,messages)
        print(result.final_output)
    
if __name__ == "__main__":
    asyncio.run(main())