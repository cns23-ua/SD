const express = require('express');
const https = require('https');
const fs = require('fs');
const router = express.Router();
const { exec } = require('child_process');
const { v4: uuidv4 } = require('uuid');

class Registry {
    constructor() {
        this.registryData = {};
        this.lastId = 0; // Variable para el último token asignado
        this.fileName = 'registro_drones.json';
    }

    // Función para añadir un nuevo dron
    agregarDron(alias) {
        const droneId = ++this.lastId;
        const droneToken = uuidv4();

        this.registryData[alias] = { id: droneId, token: droneToken };
        this.guardarRegistro();

        return { id: droneId, token: droneToken };
    }
    
    // Función para modificar un dron existente
    modificarDron(id, alias) {
        if (!this.registryData[id]) {
            return { error: "No se encontró el dron con el ID proporcionado" };
        }

        this.registryData[id].alias = alias;
        this.guardarRegistro();

        return { id, alias };
    }

    obtenerListaDrones() {
        return Object.keys(this.registryData).map((alias) => ({
            alias,
            id: this.registryData[alias].id,
            token: this.registryData[alias].token
        }));
    }

    // Función para borrar un dron existente
    borrarDron(id) {
        if (!this.registryData[id]) {
            return { error: "No se encontró el dron con el ID proporcionado" };
        }

        delete this.registryData[id];
        this.guardarRegistro();

        return { message: "Dron eliminado correctamente" };
    }

    guardarRegistro() {
        fs.writeFileSync(this.fileName, JSON.stringify(this.registryData, null, 2));
    }

    cargarRegistro() {
        try {
            const data = fs.readFileSync(this.fileName);
            this.registryData = JSON.parse(data);

            // Encontrar el último ID asignado
            const ids = Object.keys(this.registryData).map(Number);
            this.lastId = Math.max(...ids);
        } catch (err) {
            console.error("Error al cargar el registro:", err);
        }
    }
}

const registry = new Registry();

router.post('/agregar_dron', (req, res) => {
    const { alias } = req.body;
    if (!alias) {
        return res.status(400).json({ error: "Falta el alias del dron" });
    }

    const nuevoDron = registry.agregarDron(alias);
    const droneData = {
        [alias]: {
            id: nuevoDron.id
        }
    };

    res.status(201).json(droneData);
});

router.get('/listar_drones', (req, res) => {
    const listaDrones = registry.obtenerListaDrones();
    res.json(listaDrones);
});

router.put('/modificar_dron/:id', (req, res) => {
    const { id } = req.params;
    const { alias } = req.body;
    if (!alias) {
        return res.status(400).json({ error: "Falta el alias del dron" });
    }

    const resultado = registry.modificarDron(id, alias);
    if (resultado.error) {
        return res.status(404).json(resultado);
    }

    res.json({ message: "Dron modificado correctamente", drone: resultado });
});

router.delete('/borrar_dron/:id', (req, res) => {
    const { id } = req.params;

    const resultado = registry.borrarDron(id);
    if (resultado.error) {
        return res.status(404).json(resultado);
    }

    res.json(resultado);
});

const options = {
    key: fs.readFileSync('key.pem'),
    cert: fs.readFileSync('cert.pem')
};

const app = express();
app.use(express.json());
app.use('/', router);

const PORT = process.env.PORT || 3000;

const server = https.createServer(options, app);

server.on('error', (error) => {
    console.error('Error al iniciar el servidor:', error);
});

server.listen(PORT, () => {
    console.log(`Servidor HTTPS escuchando en el puerto ${PORT}`);
});