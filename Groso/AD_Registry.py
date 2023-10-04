import socket
from django.utils.crypto import get_random_string

def generate_token():
    get_random_string(length=20) #genera un token de longitud 20

def save_drone(alias, token):
    
    with open("BD.txt", "a") as file: #El "a" es para que se ponga en modo append
        file.write(f"Alias: {alias}, Token: {token}\n")

def Registry(port):
    # Crea un socket TCP/IP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Enlaza el socket al puerto especificado
    server_address = ('localhost', port)
    server_socket.bind(server_address)

    # Escucha por conexiones entrantes
    server_socket.listen(1)
    print(f"AD_Registry escuchando en el puerto {port}...")

    try:
        while True:
            
            print("Esperando una solicitud de registro...")
            client_socket, client_address = server_socket.accept()
            print(f"Solicitud de registro recibida desde {client_address}")

          
            data = client_socket.recv(1024).decode() #se utiliza oara recibir los datos a traves del socket
            if data:
                alias, _ = data.split("|")  # se separa en el DB.txt de la siguienet manera Alias|Token
                token = generate_token()  #defino la funcion token arriba

              
                save_drone(alias, token)

                
                client_socket.send(token.encode()) #enviamos desde el servidor al cliente 

            # Cierra la conexión con el cliente
            client_socket.close()
    except KeyboardInterrupt:
        print("AD_Registry detenido.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Uso: python AD_Registry.py <puerto>")
        sys.exit(1)

    port = int(sys.argv[1])
    Registry(port)
