import socket
import sys
import json
import random

HEADER = 64
FORMAT = 'utf-8'
SERVER = "127.0.0.5"

class AD_Weather:
    def __init__(self, puerto, ciudades):
        self.puerto = puerto
        self.ciudades = ciudades

    def obtener_temperatura(self, ciudad):
        return self.ciudades[ciudad]
    
    def enviar_mensaje(self, cliente, msg): 
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        cliente.send(send_length)
        cliente.send(message)

    def iniciar_servidor(self):
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.bind((SERVER, self.puerto))
        servidor.listen()

        print(f"Servidor de clima escuchando en el puerto {self.puerto}")

        while True:
            conn, addr = servidor.accept()
            print(f"Conexión establecida desde {addr}")

            # Cargar el archivo JSON
            with open(self.ciudades) as file:
                datos = json.load(file)

            # Obtener una ciudad aleatoria
            ciudad_aleatoria = random.choice(list(datos.keys()))
            temperatura = str(datos[ciudad_aleatoria])
            self.enviar_mensaje(conn, temperatura)

if (len(sys.argv) == 3):
    puerto = int(sys.argv[1])
    fichero = sys.argv[2]
    weather_server = AD_Weather(puerto, fichero)
    weather_server.iniciar_servidor()
