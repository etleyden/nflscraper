// server.js
require('dotenv').config();
const express = require('express');
const { Pool } = require('pg'); // PostgreSQL client for Node.js

const app = express();
const port = 3001; // You can change the port if needed

// Set up PostgreSQL connection using credentials from .env
const pool = new Pool({
    host: process.env.NFL_DB_HOST,
    user: process.env.NFL_DB_USER,
    password: process.env.NFL_DB_PASS,
    database: process.env.NFL_DB_NAME,
    port: process.env.NFL_DB_PORT,
});

(async () => {
    try {
        let testConnection = await pool.connect();
        console.log("Connected to PostgreSQL database");
        testConnection.release();
    } catch (err) {
        console.error('Connection Error', err.stack);
    }
})();    

/**
 * Executes a query using the PostgreSQL connection pool and returns the result.
 * @param {string} queryText - The SQL query to execute.
 * @param {Array} queryParams - The parameters for the SQL query.
 * @returns {Promise<Object>} - Resolves with the query result or rejects with an error.
 */
async function executeQuery(queryText, queryParams = []) {
    try {
        const client = await pool.connect(); // Acquire a client from the pool
        try {
            const result = await client.query(queryText, queryParams);
            return result.rows; // Return the rows of the query result
        } finally {
            client.release(); // Release the client back to the pool
        }
    } catch (err) {
        console.error('Database query error:', err.message);
        throw err; // Rethrow the error to the caller
    }
}

// Example route
app.get('/', (req, res) => {
    res.send('Hello, world!');
});

app.get('/api/export/featurelist', async (req, res) => {
    try {
        const result = await executeQuery("select * from feature_support where pipeline > 2");
        console.log(result);
        res.send('Feature List!');
    } catch (err) {
        res.status(500).json({success: false, error: err.message });
    }
});

// Start the Express server
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});
