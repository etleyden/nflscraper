const express = require('express');
const app = express();
const port = 3001

app.get('/', (req, res) => {
    res.send('It\'s working!!');
});

app.get('/api/get_tables', (req, res) => {

});

app.listen(port, () => {
    console.log(`Listening on port ${port}`)
});
