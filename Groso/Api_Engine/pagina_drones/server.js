const express = require('express');
const app = express();
const path = require('path');

const PORT = process.env.PORT || 3002; // Puerto en el que se ejecutará el servidor

// Sirve archivos estáticos (HTML, CSS, JavaScript) desde la carpeta actual
app.use(express.static(path.join(__dirname)));

// Inicia el servidor
app.listen(PORT, () => {
  console.log(`Servidor iniciado en http://localhost:${PORT}`);
});