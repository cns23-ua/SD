import socket 
import threading
import json
import secrets
import string

#Todo bien deberia funcionar

HEADER = 64
PORT = 5051
FORMAT = 'utf-8'
FIN = "FIN"
MAX_CONEXIONES = 8
JSON_FILE = "BD.json"
SERVER = "127.0.0.3"
ADDR = (SERVER, PORT)

def send_message(msg , cliente):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    cliente.send(send_length)
    cliente.send(message)

def eliminar_dron_por_nombre(alias, JSON_FILE):
    try:
        with open(JSON_FILE, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    if alias in data:
        del data[alias]  # Eliminar el dron con el nombre proporcionado

        with open(JSON_FILE, 'w') as archivo:
            json.dump(data, archivo, indent=4)

        return "ok", True  # Devuelve "ok" y True si el dron se eliminó con éxito
    else:
        return "Not existe", False

def save_drone_info(alias , id):
    try:
        with open(JSON_FILE, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}  

    if alias not in data:
        data[alias] = {
            "id": id
        }
    else:
        print(f"Alias '{alias}' ya existe en la base de datos. No se sobrescribirá.")

    with open(JSON_FILE, "w") as file:
        json.dump(data, file, indent=4)


def handle_client(conn, addr):
    print(f"[NUEVA CONEXION] {addr} connected.")
    connected = True
    try:
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
                    
                elif opc==1:
                    try:
                        with open(JSON_FILE, "r") as file:
                            data = json.load(file)
                    except FileNotFoundError:
                        data = {}

                    if not data :
                        id = 1
                        
                    else:
                    # Encuentra el ID más alto en el JSON
                        max_id = max(data.values(), key=lambda x: x["id"])["id"]
                        # Calcula el nuevo ID sumando 1 al ID más alto
                        id = max_id + 1
                           
                    save_drone_info(alias , id)
                    message_to_send = f"{alias} {id}" 
                    send_message(message_to_send, conn)
                               
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
                        message_to_send = "No existe"
                        send_message(message_to_send,conn)
                        
                elif opc==3:
                    try:
                        with open(JSON_FILE, "r") as file:
                            data = json.load(file)
                    except FileNotFoundError:
                        data = {}
                    
                    message_to_send, success = eliminar_dron_por_nombre(alias, JSON_FILE)
                    
                    if success:
                        send_message(message_to_send, conn)
                    else:
                        send_message(message_to_send, conn)
                
                elif opc==4:
                    conn.close()     
    except:
        conn.close()
    print("ADIOS. TE ESPERO EN OTRA OCASION")

    conn.close()
        
def start():
    with open(JSON_FILE, 'w') as archivo:
        json.dump({}, archivo)
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



