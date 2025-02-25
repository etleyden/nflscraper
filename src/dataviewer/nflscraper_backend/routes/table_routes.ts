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

export default router;