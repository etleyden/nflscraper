"use client";
import "../globals.css";
import "./view.css";
import {JSX, useEffect, useState} from "react"; //importing JSX per IDE reco
import Menu from "@/app/components/menu";
import {TableData, DatabaseTable} from "../components/databaseTable";

// choose a table --> view all the data in the table
export default function View() {
    const [tableNames, setTableNames] = useState<string[]>([]);
    // cache the table data upon initial retrieval
    const [tableData, setTableData] = useState<{[key: string]: TableData}>({}); // this is possibly redundant but could be used later to reduce overhead?

    //TODO 
    // IN PROGRESS: Allow for data filtering, and choosing how many rows get retrieved (right now, 25 by default)
    // refer to https://github.com/brianc/node-pg-types/blob/master/lib/builtins.js for types
    // Retrieve data only once
    // Cache these results to reduce requests, but also know when the request has changed
    // Smart types (if its a link, make it clickable, if its a color, give a swatch, if its the team name appears with the logo, then possibly combine them into the same row and render the image)
    // Collapse a table (why does this not work?)
    function updateTableData(key: string, value: TableData) {
        setTableData(prevTable => ({
            ...prevTable,
            [key]: value,
        }));
    }

    // get the initial data from the API endpoint
    async function getTableData(tableName: string) {
        if (tableName in tableData) {
            return;
        } else {
            console.log("Retrieving data...");
        }
        try {
            const endpoint = `http://localhost:3001/api/table/${tableName}`;
            const response = await fetch(`http://localhost:3001/api/table/${tableName}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch data (View Page): ${response.statusText}`);
            }
            const data = await response.json();
            updateTableData(tableName, data);
        } catch (error) {
            console.error(`Error fetching data (View Page): ${error}`);
        }
    }

    useEffect(() => {
        fetch("http://localhost:3001/api/tables")
            .then((response) => response.json())
            .then((data) => {
                setTableNames(data);
            })
            .catch((error) => console.log(error));
    }, []);

    return (
        <>
            <Menu></Menu>
            {
                tableNames.map((tableName) => {
                    return (
                        <div className="collapse collapse-arrow m-5 w-auto" key={tableName}>
                            <input type="checkbox" name="tableView" onClick={() => getTableData(tableName)} />
                            <div className="collapse-title bg-base-300" >{tableName}</div>
                            <div className="collapse-content">
                                {(tableName in tableData) ?
                                    <DatabaseTable tableName={tableName} data={tableData[tableName]}></DatabaseTable>
                                    :
                                    (<span className="loading loading-bars loading-lg"></span>)
                                }
                            </div>
                        </div>
                    );
                })
            }
        </>
    )
}