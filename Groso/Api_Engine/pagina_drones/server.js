const express = require('express');
const https = require('https');
const fs = require('fs');
const path = require('path');

const app = express();

const PORT = process.env.PORT || 3002;

const opcionesSSL = {
  key: fs.readFileSync('/home/lpv24/Escritorio/SD/SD/Groso/Api_Engine/key.pem'),
  cert: fs.readFileSync('/home/lpv24/Escritorio/SD/SD/Groso/Api_Engine/cert.pem')
};

app.use(express.static(path.join(__dirname)));

// Crea el servidor HTTPS
https.createServer(opcionesSSL, app).listen(PORT, () => {
  console.log(`Servidor iniciado en https://localhost:${PORT}`);
});
