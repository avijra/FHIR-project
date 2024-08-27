const express = require('express');
const path = require('path');
const axios = require('axios');
const multer = require('multer');
const app = express();
const port = 8080;

const upload = multer({ dest: '/tmp/uploads/' });

app.use(express.json());
app.use(express.static('public'));

app.post('/upload', upload.array('jsonFiles'), async (req, res) => {
  try {
    const formData = new FormData();
    req.files.forEach((file) => {
      formData.append('files', fs.createReadStream(file.path));
    });
    const response = await axios.post('http://backend-service:5000/ingest', formData, {
      headers: formData.getHeaders()
    });
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/query', async (req, res) => {
  try {
    const response = await axios.post('http://backend-service:5000/query', req.body);
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(port, () => {
  console.log(`Frontend server running on port ${port}`);
});