// to make server run, type node index.js

const express = require('express')
const app = express()
const port = 3000

// const { initializeApp, applicationDefault, cert } = require('firebase-admin/app');
// const { getFirestore, Timestamp, FieldValue, Filter } = require('firebase-admin/firestore');

const serviceAccount = require('/');
console.log(serviceAccount)

initializeApp({
  credential: cert(serviceAccount)
});

const db = getFirestore();

function accessJobs(req, res) {
    console.log(req)
    // res.send('Getting Jobs')
    // const companyRef = db.collection('users').doc('company');
    // const doc = await companyRef.get();

    // if (!doc.exists) {
    //     console.log('No such document!');
    // } else {
    //     console.log('Document data:', doc.data());
    // }
}

app.get('/getJobs', accessJobs)

app.get('/', (req, res) => {
  res.send('Hello World!')
})

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})