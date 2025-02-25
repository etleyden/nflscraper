import { Pool } from "pg";
require("dotenv").config();

const pool = new Pool({
    user: process.env.NFL_DB_USER,
    host: process.env.NFL_DB_HOST,
    database: process.env.NFL_DB_NAME,
    password: process.env.NFL_DB_PASS,
    port: process.env.NFL_DB_PORT ? Number(process.env.NFL_DB_PORT) : 5432
});


export default pool;