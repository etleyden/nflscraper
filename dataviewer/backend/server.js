// server.js
require('dotenv').config();  // Load environment variables from .env file
const express = require('express');
const { Client } = require('pg'); // PostgreSQL client for Node.js

const app = express();
const port = 3001; // You can change the port if needed

// Set up PostgreSQL connection using credentials from .env
const client = new Client({
    host: process.env.NFL_DB_HOST,
    user: process.env.NFL_DB_USER,
    password: process.env.NFL_DB_PASS,
    database: process.env.NFL_DB_NAME,
    port: process.env.NFL_DB_PORT,
});

client.connect()
    .then(() => {
        console.log('Connected to PostgreSQL database');
    })
    .catch(err => {
        console.error('Connection error', err.stack);
    });

// Example route
app.get('/', (req, res) => {
    res.send('Hello, world!');
});

// Start the Express server
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
