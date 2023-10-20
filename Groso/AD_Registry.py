import socket 
import threading
import json
import secrets
import string


HEADER = 64
PORT = 5051
FORMAT = 'utf-8'
FIN = "FIN"
MAX_CONEXIONES = 8
JSON_FILE = "BD.json"
SERVER = "127.0.0.1"
ADDR = (SERVER, PORT)

def send_message(message_to_send , conn):
    message_bytes = message_to_send.encode(FORMAT)
    message_length = len(message_bytes)
    conn.send(str(message_length).encode(FORMAT))
    conn.send(message_bytes)

def generate_random_token(length):
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for i in range(length))
    return token

def save_drone_info(alias , id , token):
    try:
        
        with open(JSON_FILE, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}  

    if alias not in data:
        data[alias] = {
            "id": id,
            "token": token
        }
    else:
        print(f"Alias '{alias}' ya existe en la base de datos. No se sobrescribirá.")

    with open(JSON_FILE, "w") as file:
        json.dump(data, file, indent=4)


def handle_client(conn, addr):
    print(f"[NUEVA CONEXION] {addr} connected.")

    connected = True
    while connected:
        opc=0
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            
            msg_length = int(msg_length)
            message = conn.recv(msg_length).decode(FORMAT)
            
            alias = message.split()[1]
            opc = int(message.split()[0])
           
            if message == FIN:
                connected = False
            elif opc == 1:           
                id = 1
                token = generate_random_token(64)
                save_drone_info(alias , id , token)
                message_to_send = f"{alias} {token}"
                              
                print(f" He recibido del cliente [{addr}] el mensaje: {alias}")
                
                send_message(message_to_send,conn)
                
            elif opc == 2:
                try:
                    with open(JSON_FILE, "r") as file:
                        data = json.load(file)
                except FileNotFoundError:
                    data = {}  
                    
                if alias in data:
                    message_to_send = "Dime el nuevo Alias del dron "
                    send_message(message_to_send,conn)
                    
                    new_alias = conn.recv(HEADER).decode(FORMAT)
                    if new_alias:
                        new_alias = int(new_alias)
                        new_alias = conn.recv(new_alias).decode(FORMAT)
                          
                    data[new_alias] = data.pop(alias)
                    
                    with open('BD.json', 'w') as archivo:
                        json.dump(data, archivo, indent=4)
                    
                    message_to_send = "ok"
                    send_message(message_to_send,conn)
                else:              
                    message_to_send = "Not existe"
                    send_message(message_to_send,conn)
                
            elif opc==3:
                print("dfd")
            
    print("ADIOS. TE ESPERO EN OTRA OCASION")
    conn.close()
    
        

def start():
    server.listen()
    print(f"[LISTENING] Servidor a la escucha en {SERVER}")
    CONEX_ACTIVAS = threading.active_count()-1
    print(CONEX_ACTIVAS)
    while True:
        conn, addr = server.accept()
        CONEX_ACTIVAS = threading.active_count()
        if (CONEX_ACTIVAS <= MAX_CONEXIONES): 
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[CONEXIONES ACTIVAS] {CONEX_ACTIVAS}")     
            print("CONEXIONES RESTANTES PARA CERRAR EL SERVICIO", MAX_CONEXIONES-CONEX_ACTIVAS)
        else:
            print("OOppsss... DEMASIADAS CONEXIONES. ESPERANDO A QUE ALGUIEN SE VAYA")
            conn.send("OOppsss... DEMASIADAS CONEXIONES. Tendrás que esperar a que alguien se vaya".encode(FORMAT))
            conn.close()
            CONEX_ACTUALES = threading.active_count()-1
        

######################### MAIN ##########################


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

print("[STARTING] Servidor inicializándose...")

start()



