import express from "express";
import pool from "../db";

const router = express.Router();

router.get("/tables", async (req, res) => {
    try {
        const result = await pool.query(`
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        `);
        res.json(result.rows.map(row => row.table_name));
    } catch (error) {
        res.status(500).json({ message: (error as Error).message });
    }
});

router.get("/table/:table_name", async (req, res) => {
    try {
        const query_string = `SELECT * FROM ${req.params.table_name}`;
        console.log(query_string);
        const result = await pool.query(`
            SELECT *
            FROM  ${req.params.table_name}
        `);
        res.send(`${result.rows.length} rows retrieved`);
        console.log(result.rows);
    } catch (error) {
        res.status(500).json({message: (error as Error).message});
    }
});

export default router;