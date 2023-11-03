import socket
import sys
import math
from coordenada import *
#from tablero import *
from AD_Drone import *
import re
JSON_FILE = "BD.json"
import json
from confluent_kafka import Producer
import pickle

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
FIN = "FIN"
MAX_CONEXIONES = 8
JSON_FILE = "BD.json"
SERVER = "127.0.0.3"


class AD_Engine:
        
    # *Constructor
    def __init__(self,puerto_escucha, n_maxDrones, ip_broker ,puerto_broker,ip_weather, puerto_weather):
        self.mapa = ""
        self.puerto_escucha = puerto_escucha
        self.n_maxDrones = n_maxDrones
        self.ip_broker = ip_broker
        self.puerto_broker = puerto_broker
        self.ip_weather = ip_weather
        self.puerto_weather = puerto_weather
        self.drones = []
        
    # * Funcion que envia un mensaje al servidor
    def enviar_mensaje(self, cliente, msg): 
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        cliente.send(send_length)
        cliente.send(message)
        
    # *Comunica con el servidor clima y notifica la temperatura en grados
    def consultar_clima(self, server, port, ciudad):
        try:
            #Establece conexión con el servidor (weather)
            ADDR = (server, port)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR)
            print (f"Establecida conexión (weather) en [{ADDR}]")
            
            #Enviamos la ciudad que queremos
            message = f"{ciudad}"
            self.enviar_mensaje(client, message)
            
            #Esperamos respuesta del servidor del clima
            tiempo = ""
            #Averigua el clima
            while (tiempo==""):
                    long = client.recv(HEADER).decode(FORMAT)
                    if long:
                        long = int(long)
                        tiempo = client.recv(long).decode(FORMAT)
                        print("Recibido tiempo, grados:" + tiempo)    
                        tiempo = int(tiempo)                          
        except:
            print("No se ha podido establecer conexión(weather)")
            
        return tiempo
    
    # *Notifica del estado del mapa a los drones
    def enviar_tablero(self, servidor_kafka, puerto_kafka): # !KAFKA
        producer = Producer({"bootstrap.servers": f"{servidor_kafka}:{puerto_kafka}"})
        topic = "mapa_a_drones_topic"

        # Enviar el destino a un topic de Kafka
        for dron in self.drones:
            producer.produce(topic, key=str(dron), value=pickle.dumps(self.mapa))
            
        producer.flush()
            
    # *Procesa el fichero de figuras
    def procesar_fichero(self, fichero):
        figuras = {}  
        figura_actual = {}  

        with open(fichero, 'r') as archivo:
            data = json.load(archivo)

        for figura in data['figuras']:
            nombre_figura = figura['Nombre'] 
            drones = figura['Drones']
                       
            print(f"Nombre de la figura: {nombre_figura}")
            
            for drone in drones:
                id_drone = (drone['ID'])
                posicion = drone['POS']
                pos_x = int(posicion.split(",")[0])
                pos_y = int(posicion.split(",")[1])
                Cord = Coordenada(pos_x,pos_y)
                figura_actual[id_drone] = Cord
                               
            figuras[nombre_figura] = figura_actual
            figura_actual = {}
            # *? Ejemplo de figuras ("Pollito" : [5 : {2,3} , 6 : {5,6} .... ], "Corazón" : [....] , ....)
        return figuras
        
    # *Autentica si el dron está registrado
    def autenticar_dron(self, conn):
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            message = conn.recv(msg_length).decode(FORMAT)
            #Spliteamos el mensaje en alias y token y leemos el json
            print("hola", message)
            alias = message.split()[0]
            id = int(message.split()[1])
            token = message.split()[2]  


            try:
                with open(JSON_FILE, "r") as file:
                    data = json.load(file)
            except FileNotFoundError:
                print("No se encontró el archivo")
                data = {}  
   
            # Comprobamos que el alias y el token están en el json
            for clave, valor in data.items():
                if "token" in valor and valor["token"] == token:
                    message_to_send = "Dron verificado"
                    self.enviar_mensaje(conn, message_to_send)
                    self.drones.append(id)
                    print(self.drones)
                    return True
                else:
                    message_to_send = "Rechazado"
                    self.enviar_mensaje(conn, message_to_send)
                    return False
            else:
                message_to_send = "Rechazado"
                self.enviar_mensaje(conn, message_to_send)
                return False
                
    # *Notifica los destinos a los drones y los pone en marcha
    def notificar_destinos(self, figura, servidor_kafka, puerto_kafka): # !KAFKA
        producer = Producer({"bootstrap.servers": f"{servidor_kafka}:{puerto_kafka}"})
        topic = "destinos_a_drones_topic"

        # Enviar los destinos a un topic de Kafka
        for id_dron, destino in figura.items():
            #Verificamos que los drones de la figura estén verificados
            if (id_dron in self.drones):
                producer.produce(topic, key=str(id_dron), value=pickle.dumps(destino))
            
        producer.flush()
        
    # *Acaba con la acción
    def stop(self):
        Hay_que_rellenar = "Hay que rellenar"
    
    
        
    def handle_client(self, conn, addr):
        print(f"[NUEVA CONEXION] {addr} connected.")
        connected = True
        while connected:
            self.autenticar_dron(conn)
                 
        print("ADIOS. TE ESPERO EN OTRA OCASION")
        conn.close()

    def start(self):
        server.listen()
        print(f"[LISTENING] Servidor a la escucha en {SERVER}")
        CONEX_ACTIVAS = threading.active_count()-1
        print(CONEX_ACTIVAS)
        while True:
            conn, addr = server.accept()
            CONEX_ACTIVAS = threading.active_count()
            if (CONEX_ACTIVAS <= MAX_CONEXIONES): 
                thread = threading.Thread(target= self.handle_client, args=(conn, addr))
                thread.start()
                print(f"[CONEXIONES ACTIVAS] {CONEX_ACTIVAS}")     
                print("CONEXIONES RESTANTES PARA CERRAR EL SERVICIO", MAX_CONEXIONES-CONEX_ACTIVAS)
            else:
                print("OOppsss... DEMASIADAS CONEXIONES. ESPERANDO A QUE ALGUIEN SE VAYA")
                conn.send("OOppsss... DEMASIADAS CONEXIONES. Tendrás que esperar a que alguien se vaya".encode(FORMAT))
                conn.close()
                CONEX_ACTUALES = threading.active_count()-1
        

######################### MAIN ##########################



if (len(sys.argv) == 8):
    fichero=""
    puerto_escucha = int(sys.argv[1])
    max_drones = int(sys.argv[2])
    ip_broker = sys.argv[3]
    puerto_broker = int(sys.argv[4])
    ip_weather= sys.argv[5]
    puerto_weather = int(sys.argv[6])
    ip_weather= sys.argv[7]
    
    ADDR = (SERVER, puerto_escucha) 
    print("[STARTING] Servidor inicializándose...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    print("[STARTING] Servidor inicializándose...")  
    engine = AD_Engine(puerto_escucha,max_drones, ip_broker ,puerto_broker,ip_weather, puerto_weather)
    if fichero != "":   
        engine.start()
        

if (len(sys.argv) == 2):
    engine = AD_Engine("","","","","","")
    fichero = sys.argv[1]
    figuras = engine.procesar_fichero(fichero)
    print(figuras['Triangulo'])
    
    engine = engine.notificar_destinos(figuras['Triangulo'],"127.0.0.1",8083)
    
    

#Las figuras ya funcionan
