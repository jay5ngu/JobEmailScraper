import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import base64
from bs4 import BeautifulSoup 

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

class JobEmailScraper:
    def __init__(self):
        self.credentials = self.checkCredentials()
  
    def checkCredentials(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())
            
        return creds

    def listLabels(self):
        """Lists the user's Gmail labels."""
        try:
            # Call the Gmail API
            service = build("gmail", "v1", credentials=self.credentials)
            results = service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])

            if not labels:
                print("No labels found.")
                return
            
            print("Labels:")
            for label in labels:
                print(label["name"])

        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            print(f"An error occurred: {error}")

    def getEmails(self):
        """Get all the user's emails"""
        try:
            service = build("gmail", "v1", credentials=self.credentials)

            # request a list of all linkedin job alert messages 
            results = service.users().messages().list(maxResults=1, userId='me', labelIds=['CATEGORY_UPDATES'], q="from:jobalerts-noreply@linkedin.com").execute() 
            
            messages = results.get('messages') # messages is a list of dictionaries where each dictionary contains a message id. 
        
            # iterate through all the messages 
            for msg in messages: 
                # Get the message from its id and returns dict object
                txt = service.users().messages().get(userId='me', id=msg['id']).execute() 

                # Use try-except to avoid any Errors 
                try: 
                    # Get value of 'payload' from dictionary 'txt' 
                    payload = txt['payload'] 
        
                    # The Body of the message is in Encrypted format. So, we have to decode it. 
                    # Get the data and decode it with base 64 decoder. Decode to HTML
                    parts = payload.get('parts')[1] 
                    data = parts['body']['data'] 
                    data = data.replace("-","+").replace("_","/") 
                    decoded_data = base64.b64decode(data).decode('utf-8')   

                    # Now, the data obtained is in html. So, we will parse it with BeautifulSoup library 
                    soup = BeautifulSoup(decoded_data , features="html") 

                    # table with five rows (third row contains job listings)
                    jobTable = soup.body.table.tbody.tr.find_next_sibling("tr")

                    # get all five rows from table
                    jobTable = jobTable.tr.find_next_siblings("tr")

                    # choose third row's table
                    jobTable = jobTable[1]
                    self._writeToFile(jobTable.table.prettify(), "jobRows.html")

                    # process first job
                    self._parseJob(jobTable.tr)

                    # with that first job processed, can grab the rest of the row siblings
                    for row in jobTable.tr.find_next_siblings("tr"):
                        self._parseJob(row) 

                    # Printing the job info 
                    # print("Title: ", title) 
                    # print("Company: ", company) 
                    # print("Job Application URL: ", url) 
                    # print('\n') 

                except Exception as error: 
                    print("Error parsing", error)

        except HttpError as error:
            print(f"An error occurred: {error}") 

    def _parseJob(self, row):
        # traverse down the tree
        reduceRow = row.table.table.table.tbody.table.tbody

        # get tag containing job title and job application link
        jobPosition = reduceRow.tr.a
        jobTitle = jobPosition.get_text()
        jobLink = jobPosition.get("href")
        jobLink = jobLink[:jobLink.find("?")]

        # get company name and location
        jobCompany = reduceRow.tr.find_next_sibling("tr").p
        jobCompany, jobLocation = jobCompany.get_text().split("·")

        print(jobTitle)
        print(jobLink)
        print(jobCompany)
        print(jobLocation)
        print()

        # self._writeToFile(jobPosition.prettify(), "jobPosition.html")
        # self._writeToFile(jobCompany.prettify(), "jobCompany.html")

    def _writeToFile(self, text, filename):
        # Writing to file
        with open(filename, "w", encoding="utf-8") as file:
            file.write(text)


if __name__ == "__main__":
  jobScraper = JobEmailScraper()
#   jobScraper.listLabels()
  jobScraper.getEmails()