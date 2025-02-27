import express from "express";
import cors from "cors";
import tableRoutes from "./routes/table_routes";

const app = express();
app.use(cors());
app.use(express.json());
const port = 3001

app.use("/api", tableRoutes);

app.get('/', (req, res) => {
    res.send('It\'s working!!');
});

app.listen(port, () => {
    console.log(`Listening on port ${port}`)
});
