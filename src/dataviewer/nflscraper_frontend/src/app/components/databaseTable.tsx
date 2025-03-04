import { table } from "console";
import {useEffect, useState} from "react";
// DB table fields as returned from the API
interface Field {
    name: string;
    type: number; // Or whatever type `type` is
}

// DB Table Entries to store the table data after each request.
export interface TableData {
    rows: {[key: string]: unknown}[];
    fields: Field[];
}

interface DatabaseTableProps {
    data: TableData;
    tableName: string;  // Add tableName as a separate prop
}

export function DatabaseTable({tableName, data}: DatabaseTableProps) {
    // initialize filters as a state
    const [tableData, setTableData] = useState<TableData>(data);
    const [filters, setFilters] = useState<{[key: string]: string}>({});
    const [timeoutId, setTimeoutId] = useState<NodeJS.Timeout | null>(null);
    //const [timeoutCountdown, setTimeoutCountdown] = useState(0);

    function updateFilters(field: string, filter: string) {
        setFilters(prevFilters => ({
            ...prevFilters,
            [field]: filter,
        }));
    }

    useEffect(() => {
        if (timeoutId) {
            clearTimeout(timeoutId);
        }

        const requestDelay = setTimeout(async () => {
            let apiEndpoint = `http://localhost:3001/api/table/${tableName}?`

            let isFirst = true;
            for (const [key, value] of Object.entries(filters)) {
                if (value.length > 0) {
                    if (isFirst) {
                        apiEndpoint += "?";
                        isFirst = false;
                    } else {
                        apiEndpoint += "&";
                    }
                    apiEndpoint += `${key}=${value}`;
                }
            }
            // render API URL
            console.log(`Retrieving data from ${apiEndpoint}`);
            try {
                const response = await fetch(apiEndpoint);
                if(!response.ok) throw new Error(`Failed to fetch data: ${response.statusText}`);
                const data = await response.json();
                setTableData(data);
            } catch (error) {
                console.error(`There was an error updating the data (DatabaseTable)`);
            }
        }, 500);

        setTimeoutId(requestDelay);

    return () => clearTimeout(requestDelay);
}, [filters]);

useEffect(() => {
    data.fields.map((field: Field) => {
        updateFilters(field.name, "");
    });
    setTableData(data);
}, [data]);

let keyCounter = 0;
return (<table className="table table-zebra">
    <thead className="bg-base-200">
        <tr>
            {tableData.fields.map((field: Field) => {
                return (
                    <th key={field.name}>{field.name}</th>
                )
            })}
        </tr>
        <tr>
            {
                tableData.fields.map((field: Field) => {
                    return (
                        <td key={`filter_${field.name}_${field.type}`} className="p-1">
                            <input
                                type="text"
                                placeholder="filter"
                                onChange={(e) => updateFilters(field.name, e.target.value)}
                                className="input input-sm w-full placeholder:font-normal" />
                        </td>
                    )
                })
            }
        </tr>
    </thead>
    <tbody>
        {tableData.rows.map((row: object) => {
            return (<tr key={keyCounter++}>
                {Object.entries(row).map(([key, value]) => (
                    <td key={keyCounter++}>{value}</td>
                ))}
            </tr>);
        })}
    </tbody>
</table>);
}