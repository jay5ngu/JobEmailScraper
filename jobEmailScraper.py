import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from bs4 import BeautifulSoup 
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account.
fireCred = credentials.Certificate('firestoreCredentials.json')

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", 
          "https://mail.google.com/", "https://www.googleapis.com/auth/gmail.modify"]

class JobEmailScraper:
    def __init__(self):
        self.credentials = self.checkCredentials()

        # Firestore Application Default credentials are automatically created.
        self.app = firebase_admin.initialize_app(fireCred)
        self.db = firestore.client()
  
    def checkCredentials(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            # if creds and creds.expired and creds.refresh_token:
            #     creds.refresh(Request())
            # else:

            flow = InstalledAppFlow.from_client_secrets_file("googleCredentials.json", SCOPES)
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
                print(label["name"], label["id"])

        except HttpError as error:
            # TODO(developer) - Handle errors from gmail API.
            print(f"An error occurred: {error}")

    def parseEmails(self, delete):
        """Parse all the linkedin job alert emails"""
        try:
            service = build("gmail", "v1", credentials=self.credentials)

            # request a list of all linkedin job alert messages 
            results = service.users().messages().list(userId='me', labelIds=['CATEGORY_UPDATES'], q="from:jobalerts-noreply@linkedin.com").execute() # maxResults=5,
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
                    soup = BeautifulSoup(decoded_data , features="html.parser") 

                    # table with five rows (third row contains job listings)
                    jobTable = soup.body.table.tbody.tr.find_next_sibling("tr")
                    # self._writeToFile(jobTable.prettify(), "regularEmail.html")

                    # get all five rows from table
                    jobTable = jobTable.tr.find_next_siblings("tr")

                    # choose third row's table
                    jobTable = jobTable[1]
                    # self._writeToFile(jobTable.table.prettify(), "jobRows.html")

                    # process first job
                    self._parseJob(jobTable.tr)

                    # with that first job processed, can grab the rest of the row siblings
                    for row in jobTable.tr.find_next_siblings("tr"):
                        self._parseJob(row) 

                    # delete email once it is finished and user approves deletion
                    if delete:
                        self._deleteEmails(service, msg["id"])

                except Exception as error: 
                    print(f"Error when parsing {msg['id']}: {error}")

                    # tag emails with an error label
                    body = {"removeLabelIds": [], "addLabelIds": ["Label_2311042616538796578"]}  # Format: {A list IDs of labels to remove from this message, A list of IDs of labels to add to this message.}
                    service.users().messages().modify(userId="me", id=msg["id"], body=body).execute()

        except HttpError as error:
            print(f"An Https error occurred: {error}") 

    def parseErrorEmails(self, delete):
        """Parse all the error linkedin job alert emails"""
        try:
            service = build("gmail", "v1", credentials=self.credentials)

            # request a list of all linkedin job alert messages 
            results = service.users().messages().list(userId='me', labelIds=['Label_2311042616538796578'], q="from:jobalerts-noreply@linkedin.com").execute() #  maxResults=1, 
            messages = results.get('messages') # messages is a list of dictionaries where each dictionary contains a message id. 
        
            # iterate through all the messages 
            for msg in messages: 
                # Get the message from its id and returns dict object
                txt = service.users().messages().get(userId='me', id=msg['id']).execute() 
                jobStored = False

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
                    soup = BeautifulSoup(decoded_data , features="html.parser") 

                    # table with five rows (third row contains job listings)
                    jobTable = soup.body.table.tbody.tr.find_next_sibling("tr")

                    # get all rows from inner table
                    self._writeToFile(jobTable.prettify(), "testEmail.html")
                    jobTable = jobTable.tr.find_next_sibling("tr").find_next_siblings("tr")

                    # iterate through table until no more jobs left              
                    for row in jobTable :
                        stored = self._parseJob(row)
                        if stored:
                            jobStored = True

                # Error usually means there's no more jobs located in email
                except Exception as error:
                    # delete email once it is finished and user approves deletion
                    if delete and jobStored:
                        self._deleteEmails(service, msg["id"])
                    else:
                        print(f"Error when parsing Message {msg['id']}: {error}")

        except HttpError as error:
            print(f"An Https error occurred: {error}") 

    def _parseJob(self, row):
        """Parse the individual job in email"""
        try:
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
            
            # print data of job info
            # self._printJob(jobTitle, jobLink, jobCompany, jobLocation)

            # store data to firestore database
            self._storeJob(jobTitle, jobLink, jobCompany, jobLocation)

            return True
        
        except Exception as error:
            print(f"Error occur when trying to parse job: {error}")
            return False

    def _printJob(self, title, link, company, location):
        print(title)
        print(link)
        print(company)
        print(location)
        print()

    def _storeJob(self, title, link, company, location):
        """Save job information to firestore"""
        # sends job to firestore database (Users/Company/Jobs)
        self.db.collection("users").document(company).collection("jobs").document(link.replace("/","_")).set({"title": title, "link": link, "company": company, "location": location})
        
        # Other iterations to store data
        # self.db.collection("users").document(company).set({"title": title, "link": link, "company": company, "location": location})
        # self.db.collection("users").document(link.replace("/", "_")).set({"title": title, "link": link, "company": company, "location": location})
        # self.db.collection("users").add({"title": title, "link": link, "company": company, "location": location})

    def _deleteEmails(self, service, id):
        """Delete email from Gmail inbox"""
        trashed = service.users().messages().trash(userId="me", id=id).execute()
        if trashed:
            print(f"Email {id} has been deleted")

    def _writeToFile(self, text, filename):
        """Developer function to see what data looks like in HTML format"""
        # Writing to file
        with open(filename, "w", encoding="utf-8") as file:
            file.write(text)

    def listCompanies(self):
        results = self.db.collection("users").stream()

        for result in results:
            print(f"{result.id} => {result.to_dict()}")


if __name__ == "__main__":
  jobScraper = JobEmailScraper()

  # Gmail API tests
#   jobScraper.listLabels()
#   jobScraper.parseEmails(False)
#   jobScraper.parseErrorEmails(False)

  # Firestore test
  jobScraper.listCompanies()

