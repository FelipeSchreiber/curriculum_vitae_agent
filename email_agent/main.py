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

INSTRUCTIONS=("You are a curriculum vitae sender.\n"
               "Everytime a recruiter sends you her email, name and the subject is about a job offer,\
                you are going to call the tool send_email_with_attachment with her email,\
                the subject - which is the name of the opportunity -\
                and the body of email, informing the curriculum is attached and thanking her for the opportunity"
            )

email_agent = Agent(name="Email Manager",
                    tools=[send_email_with_attachment],
                    instructions=INSTRUCTIONS, 
                    model="gpt-4o-mini")

async def main():
    # Example: Ask agent to send CV
    messages="Hello, my name is Luiza and I would like to talk about Data Science Especialist\
        opportunity at McKinsey. Here is my email if you are interested: schreiber.felipe@gmail.com"

    with trace("Sending an email"):
        result = await Runner.run(email_agent,messages)
        print(result.final_output)
    
if __name__ == "__main__":
    asyncio.run(main())