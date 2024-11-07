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
async function listCompanyNames(req, res) 
{
  try {
      // Access Firestore collection and document
    const results = await db.collectionGroup('Company Name').get();

    // Confirm that we received results from Firestore database
    if (results.empty) {
      // Respond with 404 if no document found
      return res.status(404).send(`No jobs found for company: ${company}`);
    }

    // Parse all company names into list type storage
    const companyNames = []
    results.forEach((name) => {
      companyNames.push(name.id);
    });

    // Respond with document data as JSON
    return res.status(200).json(companyNames);

  } catch (error) {
    // Handle any errors in Firestore access
    console.error('Error accessing Firestore:', error);
    res.status(500).send('Internal Server Error');
  }
}

async function allJobs(req, res) {
  // TODO: get all jobs and their info
}

async function getJob(req, res) {
  const company = req.query.company;

  if (!company) {
    // Return a 400 response if the company query parameter is missing
    return res.status(400).send('Missing "company" query parameter');
  }

  try {
    // Access Firestore collection and document
    const results = await db.collection('Job Listings').doc(company).collection('jobs').get();

    // Confirm that we received results from Firestore database
    if (results.empty) {
      // Respond with 404 if no document found
      return res.status(404).send(`No jobs found for company: ${company}`);
    }

    // Parse all jobs into list type storage
    const jobs = []
    results.forEach(job => {
      jobs.push(job.data());
    });

    // Respond with document data as JSON
    return res.status(200).json({ company, jobs });

  } catch (error) {
    // Handle any errors in Firestore access
    console.error('Error accessing Firestore:', error);
    res.status(500).send('Internal Server Error');
  }
}

// Test function to add sample data points
async function addJob(req, res) {
  const company = req.query.company;
  const title = req.query.title
  const link = req.query.link
  const location = req.query.location

  // Replace '/' with '_' in link to match your Python code logic
  const sanitizedLink = link.replace(/\//g, "_");

  try {
    // Add job to Firestore Database
    const jobListings = db.collection('Job Listings');
    await jobListings.doc(company).collection("jobs").doc(sanitizedLink).set({
      title: title,
      link: link,
      company: company,
      location: location
    });

    const companyNames = db.collection('Company Name');
    await companyNames.doc(company).set({});
    
    // Respond with document data as JSON
    return res.status(200).send("Data added successfully!");

  } catch (error) {
    // Handle any errors in Firestore access
    console.error('Error accessing Firestore:', error);
    res.status(500).send('Internal Server Error');
  }
  
}

async function deleteJob(req, res) {
  company = req.query.company;
  link = req.query.link;

  if (!company || !link) {
    return res.status(400).send('Missing query parameter');
  }

  try {
    await db.collection('Job Listings').doc(company).collection('jobs').doc(link).delete();

    return res.status(200).send("Data deleted successfully!");

  } catch (error) {
    // Handle any errors in Firestore access
    console.error('Error accessing Firestore:', error);
    res.status(500).send('Internal Server Error');
  }
}


app.get('/listCompanies', listCompanyNames)

app.get('/allJobs', allJobs)

app.get('/getJob', getJob)

app.post('/addJob', addJob)

app.post('/deleteJob', deleteJob)

app.get('/', (req, res) => {
  res.send('Hello World!')
})

app.listen(port, () => {
  console.log(`Job Email Scraper API listening on port ${port}`)
})

// addJobs('Test Company', 'Software Engineer','https://www.google.com/','San Francisco');
// deleteJobs();
// listCompanyNames();