import socket

def weather_server(port):
    # Crea un socket TCP/IP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # socket de flujo , es decir, bidireccional

    # Enlaza el socket al puerto especificado
    server_address = ('localhost', port)
    server_socket.bind(server_address)

    # Escucha por conexiones entrantes
    server_socket.listen(1)
    print(f"Servidor de clima escuchando en el puerto {port}...")

    try:
        while True:
            # Espera una conexión entrante
            print("Esperando una conexión...")
            client_socket, client_address = server_socket.accept()
            print(f"Conexión aceptada desde {client_address}")

            # Aquí debes implementar la lógica para manejar las solicitudes del cliente.
            # Recibir y procesar las solicitudes, buscar la temperatura y enviarla de vuelta.

            # Cierra la conexión con el cliente
            client_socket.close()
    except KeyboardInterrupt:
        print("Servidor de clima detenido.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Uso: python AD_Weather.py <puerto>")
        sys.exit(1)

    port = int(sys.argv[1])
    weather_server(port)
