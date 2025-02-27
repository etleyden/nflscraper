"use client";
import "../globals.css";
import "./view.css";
import {JSX, useEffect, useState} from "react"; //importing JSX per IDE reco
import Menu from "@/app/components/menu";


// choose a table --> view all the data in the table
export default function View() {
    const [tableNames, setTableNames] = useState<string[]>([]);
    const [tableData, setTableData] = useState<{[key: string]: JSX.Element}>({});

    function updateTableData(key: string, value: JSX.Element) {
        setTableData(prevTable => ({
            ...prevTable,
            [key]: value,
        }));
    }
    async function getTableData(tableName: string) {
        try {
            const endpoint = `http://localhost:3001/api/table/${tableName}`;
            const response = await fetch(`http://localhost:3001/api/table/${tableName}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch data: ${response.statusText}`);
            }
            const data = await response.json();
            let keyCounter = 0;
            updateTableData(tableName,
                <table className="table table-zebra">
                    <thead className="bg-base-200">
                        <tr>
                            {data.fields.map((field: string) => {
                                return (
                                    <th key={field}>{field}</th>
                                )
                            })}
                        </tr>
                    </thead>
                    <tbody>
                        {data.rows.map((row: object) => {
                            return (<tr key={keyCounter++}>
                                {Object.entries(row).map(([key, value]) => (
                                    <td key={keyCounter++}>{value}</td>
                                ))}
                            </tr>);
                        })}
                    </tbody>
                </table>
            );
        } catch (error) {
            console.error(`Error fetching data: ${error}`);
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
                tableNames.map((table) => {
                    return (
                        <div className="collapse collapse-arrow m-3 w-fit" key={table}>
                            <input type="radio" name="tableView" onClick={() => getTableData(table)} />
                            <div className="collapse-title bg-base-300" >{table}</div>
                            <div className="collapse-content">
                                {(table in tableData) ?
                                    tableData[table]
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