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

// this function takes a string encoding for a filter and a postgres data type (as a string) and 
// generates that part of the SQL query to match that filter. 
function interpretFilterString(column_name: string, filter: string, data_type: string) {
    let result = "(";
    switch(data_type) {
        case "integer":
        case "real":
            let filters = filter.split(','); // can have multiple, comma delimited filters

            // REGEX TO VALIDATE TERMS
            // for any numeric type, we'll use the syntax:
            //[[operator]?[number]]+
            const term_regex = /(<|>|<=|>=|=)?([0-9]+)(.[0-9]*)?/;
            let isFirst = true;
            for (const term of filters) {
                if(term_regex.test(term)) {
                    if (isFirst) {
                        isFirst = false;
                    } else {
                        result += " OR ";
                    }
                    if (!term.charAt(0).match(/^\d/)) {
                        result += `${column_name}${term}`;
                    } else { // if term starts with an integer, assume `=`
                        result += `${column_name}=${term}`;
                    }
                }
            }
            break;
        case "character":
        case "character varying":
            // for any character type we'll use the syntax
            result += `${column_name} ILIKE '%' || '${filter}' || '%'`
            break;
        case "date":
            // TODO
        default:
            return "";
    }
    return result + ")";

}
router.get("/table/:table_name", async (req, res) => {

    let limit = req.query.limit || 25;
    delete req.query.limit;
    let columns: {[key: string]: string} = {};
    
    // we'll also want to get a list of valid column names to avoid SQL injection
    try {
        const result = await pool.query(`
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='${req.params.table_name}'`);
        for (const column of result.rows) {
            columns[column.column_name] = column.data_type;
        }
    } catch (error) {
        console.log(error);
        res.status(500).json({message: (error as Error).message});
    }

    console.log(columns);
    let db_query = `SELECT * FROM ${req.params.table_name}`;
    let hasNoParams = true; // flag to add syntax for first where clause
    for (const filter in req.query) {
        // only add the filter if it is in the valid list of columns
        if (filter in columns) {
            if (hasNoParams) {
                db_query += ` WHERE`;
                hasNoParams = false;
            } else {
                db_query += ` AND`;
            }
            db_query += ` ${interpretFilterString(filter, req.query[filter] as string, columns[filter])}`;
        }
    }
    db_query += ` LIMIT ${limit}`;
    console.log(db_query);


    try {
        const result = await pool.query(db_query);
        res.json({
            rows: result.rows,
            fields: result.fields.map((field) => ({
                name: field.name,
                type: field.dataTypeID
            }))
        });
    } catch (error) {
        res.status(500).json({message: (error as Error).message});
    }
});

export default router;