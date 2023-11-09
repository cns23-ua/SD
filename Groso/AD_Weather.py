import socket


HEADER = 64
FORMAT = 'utf-8'
SERVER = "127.0.0.4"

class AD_Weather:
    def __init__(self, puerto, ciudades):
        self.puerto = puerto
        self.ciudades = eval(ciudades)

    def obtener_temperatura(self, ciudad):
        return self.ciudades[ciudad]

    def iniciar_servidor(self):
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.bind((SERVER, self.puerto))
        servidor.listen()

        print(f"Servidor de clima escuchando en el puerto {self.puerto}")

        while True:
            conn, addr = servidor.accept()
            print(f"Conexión establecida desde {addr}")

            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                message = conn.recv(msg_length).decode(FORMAT)
                
                temperatura = self.obtener_temperatura(message)

            conn.send(str(temperatura).encode('utf-8'))

if __name__ == "__main__":
    puerto = 10000  # Puerto de escucha
    weather_server = AD_Weather(puerto, "ciudades.json")
    weather_server.iniciar_servidor()
