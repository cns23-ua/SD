const express = require('express');
const https = require('https');
const fs = require('fs');
const router = express.Router();
const { exec } = require('child_process');
const { v4: uuidv4 } = require('uuid');

class Registry {
    constructor() {
        this.fileName = "/home/tooez/Escritorio/SD/Groso/BD.json";
        this.registryData = this.obtenerDatosGuardados();
    }

    obtenerDatosGuardados() {
        try {
            if (fs.existsSync(this.fileName)) {
                const data = fs.readFileSync(this.fileName, 'utf8');
                return JSON.parse(data);
            } else {
                console.error('El archivo JSON no existe o está vacío.');
                return {};
            }
        } catch (err) {
            console.error('Error al leer el archivo JSON:', err);
            return {};
        }
    }

    // Función para obtener el próximo ID basado en la cantidad de drones en el registro
    obtenerProximoId() {
        const cantidadDrones = Object.keys(this.registryData).length;
        return cantidadDrones + 1; // El próximo ID será la cantidad actual más uno
    }

    agregarDron(alias) {
        this.registryData = this.obtenerDatosGuardados();
        const droneId = this.obtenerProximoId(); // Obtener el próximo ID dinámicamente

        this.registryData[alias] = { id: droneId };
        this.guardarRegistro();

        return { id: droneId };
    }
    
    modificarDron(id, nuevoAlias) {
        this.registryData = this.obtenerDatosGuardados();
        let dronEncontrado = null;
    
        for (const key in this.registryData) {
            if (this.registryData[key].id == id) {
                dronEncontrado = this.registryData[key];
                break;
            }
        }
    
        this.registryData = this.obtenerDatosGuardados();
        if (!dronEncontrado) {
            return { error: "No se encontró el dron con el ID proporcionado" };
        }
    
        const aliasActual = Object.keys(this.registryData).find(key => this.registryData[key] === dronEncontrado);
    
        // Crear una nueva entrada con el nuevo alias y el mismo valor del dron encontrado
        this.registryData[nuevoAlias] = { ...this.registryData[aliasActual] };
        delete this.registryData[aliasActual]; // Eliminar la entrada con el antiguo alias
    
    
        this.guardarRegistro();
        return { id, alias: nuevoAlias };
    }
    
    obtenerListaDrones() {
        this.registryData = this.obtenerDatosGuardados();
        return Object.keys(this.registryData).map((alias) => ({
            alias,
            id: this.registryData[alias].id,
            token: this.registryData[alias].token
        }));
    }

    borrarDron(id) {  
        this.registryData = this.obtenerDatosGuardados();  
        let dronEncontrado = null;
    
        for (const key in this.registryData) {
            if (this.registryData[key].id == id) {
                dronEncontrado = key;
                break;
            }
        }
    
        if (!dronEncontrado) {
            return { error: "No se encontró el dron con el ID y alias proporcionados" };
        }
    
        delete this.registryData[dronEncontrado]; // Eliminar la entrada con el alias especificado
        
        this.guardarRegistro();
        return { id };
    }

    generarToken(alias) {
        this.registryData = this.obtenerDatosGuardados();
        if (!this.registryData[alias]) {
            return { error: "No se encontró el dron con el alias proporcionado" };
        }

        const token = uuidv4(); // Generar un token único
        this.registryData[alias].token = token;
        this.guardarRegistro();
        return { alias, token };
    }
    
    guardarRegistro() {
        fs.writeFileSync(this.fileName, JSON.stringify(this.registryData, null, 2));
    }

    reiniciarRegistro() {
        this.registryData = {};
        this.guardarRegistro();
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

router.put('/generar_token/:alias', (req, res) => {
    const { alias } = req.params;

    const resultado = registry.generarToken(alias);
    if (resultado.error) {
        return res.status(404).json(resultado);
    }

    res.json({ message: "Token generado correctamente", drone: resultado });
});

router.put('/borrar_token/:alias', (req, res) => {
    registry.registryData = registry.obtenerDatosGuardados();
    const { alias } = req.params;

    if (!alias) {
        return res.status(400).json({ error: "Falta el alias del dron" });
    }

    if (!registry.registryData[alias]) {
        return res.status(404).json({ error: "No se encontró el dron con el alias proporcionado" });
    }

    // Eliminar el atributo token del dron
    delete registry.registryData[alias].token;

    registry.guardarRegistro();
    res.json({ message: `Token eliminado del dron '${alias}'` });
});


router.delete('/borrar_todo', (req, res) => {
    registry.reiniciarRegistro();
    res.json({ message: "Se han borrado todos los drones y se ha reiniciado el registro" });
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