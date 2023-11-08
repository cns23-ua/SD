import socket

class AD_Weather:
    def __init__(self, puerto):
        self.puerto = puerto
        self.ciudades = {
            "Madrid": 25,
            "Londres": 20,
            "París": 22,
            # ... otras ciudades y sus temperaturas
        }

    def obtener_temperatura(self, ciudad):
        return self.ciudades.get(ciudad, "No disponible")

    def iniciar_servidor(self):
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.bind(('localhost', self.puerto))
        servidor.listen()

        print(f"Servidor de clima escuchando en el puerto {self.puerto}")

        while True:
            conn, addr = servidor.accept()
            print(f"Conexión establecida desde {addr}")

            ciudad = conn.recv(1024).decode('utf-8')

            temperatura = self.obtener_temperatura(ciudad)

            conn.send(str(temperatura).encode('utf-8'))
            conn.close()

if __name__ == "__main__":
    puerto = 10000  # Puerto de escucha
    weather_server = AD_Weather(puerto)
    weather_server.iniciar_servidor()
