// to make server run, type node index.js
// example query: http://localhost:3000/getJobs?company=Dice 

// Import necessary dependencies / modules
const path = require('path');
const express = require('express')
const { initializeApp, cert } = require('firebase-admin/app');
const { getFirestore } = require('firebase-admin/firestore');

// Set up constants for API calls
const app = express()
const port = 3000

// Get the current directory of the running script
const currentDir = __dirname;

// Construct the path to firestoreCredentials.json
const credentialsPath = path.join(currentDir, '..', 'firestoreCredentials.json');
const serviceAccount = require(credentialsPath);

// Initialize database object
initializeApp({
  credential: cert(serviceAccount),
  projectId: serviceAccount.project_id
});

const db = getFirestore();

// Get list of all existing collections in database as well as their data
async function listCollections() 
{
  const usersCollection = db.collection('users');
  const results = await usersCollection.get();

  // Extract document IDs, which are the company names
  const companyNames = results.docs.map(doc => doc.id);

  console.log("Company Names:", companyNames);
}

// Test function to add sample data points
async function addJobs(company, title, link, location) {
  const usersCollection = db.collection('users');

  // Replace '/' with '_' in link to match your Python code logic
  const sanitizedLink = link.replace(/\//g, "_");

  await db.collection("users")
    .doc(company)                     // Company as document ID in 'users' collection
    .collection("jobs")
    .doc(sanitizedLink)               // Sanitized link as document ID in 'jobs' subcollection
    .set({
      title: title,
      link: link,
      company: company,
      location: location
    });

  console.log('Data added to Firestore successfully.');
  
}

async function deleteJobs() {
  const result = await db.collection('users').doc('AAAAAAAA').delete();
}

async function accessJobs(req, res) {
  const company = req.query.company;

  if (!company) {
    // Return a 400 response if the company query parameter is missing
    return res.status(400).send('Missing "company" query parameter');
  }

  try {
    // Access Firestore collection and document
    const companyRef = db.collection('users').doc(company);
    const doc = await companyRef.get();

    if (!doc.exists) {
      // Respond with 404 if no document found
      return res.status(404).send(`No document found for company: ${company}`);
    }

    // Respond with document data as JSON
    res.json({ message: 'Document data found', data: doc.data() });
  } catch (error) {
    // Handle any errors in Firestore access
    console.error('Error accessing Firestore:', error);
    res.status(500).send('Internal Server Error');
  }
}

app.get('/getJobs', accessJobs)

app.get('/', (req, res) => {
  res.send('Hello World!')
})

app.listen(port, () => {
  console.log(`Job Email Scraper API listening on port ${port}`)
})

// addJobs('Test Company', 'Software Engineer','https://www.google.com/','San Francisco');
// deleteJobs();
// listCollections();