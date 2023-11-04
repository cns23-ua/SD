from coordenada import *
import socket
import sys
import math
import threading
import json
import secrets
import string
from confluent_kafka import Consumer, KafkaError
import pickle


HEADER = 64
FORMAT = 'utf-8'

class Dron:
    
    # *Constructor
    def __init__(self):
        self.id = 1
        self.alias = "test"
        self.color = "Rojo"
        self.coordenada =Coordenada(1,1)
        self.token = "prueba"
        self.destino = ""
        self.mapa = "mapa"
        
    # *Movemos el dron dónde le corresponde y verificamos si ha llegado a la posición destino
    def mover(self, pos_fin):
        self.posicion = self.siguiente_mov(pos_fin)
        if (self.posicion[0]==pos_fin[0] and self.posicion[1]==pos_fin[1]):
            self.estado = "Verde"  # Cambiar a estado final si ha llegado a la nueva posición
        
    def receive_message(self, client):
        msg_length = client.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            message = client.recv(msg_length).decode(FORMAT)

        return message
        
    # *Encontramos el siguiente movimiento que debe hacer
    def siguiente_mov(self, pos_fin):
         
        x = [-1,0,1]
        y = [-1,0,1]
        ini = self.coordenada
        anterior = 30.0
        optima = Coordenada(0,0)
        resul = Coordenada(0,0)
        
        for i in x:
            for j in y:
                optima[0] = ini[0]+i
                optima[1] = ini[1]+j
                if (optima[0]>20):
                    optima[0]=optima[0]-20
                if (optima[0]<1):
                    optima[0]=optima[0]+20
                if (optima[1]>20):
                    optima[1]=optima[1]-20
                if (optima[1]<1): 
                    optima[1]=optima[1]+20
                if math.sqrt((optima[0]-pos_fin[0])**2+((optima[1]-pos_fin[1]**2)))<anterior:    
                    anterior = math.sqrt((optima[0]-pos_fin[0])**2+((optima[1]-pos_fin[1]**2)))    
                    resul = optima                   
                    
        return optima
    
    # !Kafka:
    
     # * Funcion que recibe el destino del dron mediante kafka
    def recibir_destino(self, servidor_kafka, puerto_kafka):
        consumer = Consumer({
            "bootstrap.servers": f"{servidor_kafka}:{puerto_kafka}",
            "group.id": "drones",
            "auto.offset.reset": "earliest"
        })

        topic = "destinos_a_drones_topic"

        consumer.subscribe([topic])
        
        intentos = 10  # Número máximo de intentos
        contador = 0

        while contador < intentos:
            msg = consumer.poll(1.0)
            if msg is not None:
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f"Error al recibir mensaje: {msg.error()}")
                else:
                    mensaje = msg.value().decode('utf-8')
                    print("hola makina" + mensaje)
                    self.destino = json.loads(mensaje)
                    break  # Sale del bucle al recibir un mensaje exitoso
            contador += 1

        consumer.close()

    # * Función para recibir el mapa
    def recibir_mapa(self, servidor_kafka, puerto_kafka):
        consumer = Consumer({
        "bootstrap.servers": f"{servidor_kafka}:{puerto_kafka}",
        "group.id": "drones",
        "auto.offset.reset": "earliest"
        })

        topic = "destinos_a_drones_topic"

        consumer.subscribe([topic])

        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Error al recibir mensaje: {msg.error()}")
            else:
                print(f"Mensaje recibido: {pickle.loads(msg.value())}")
                self.mapa = pickle.loads(msg.value())
    
    # * Funcion que envia un mensaje al servidor
    def enviar_mensaje(self, cliente, msg): 
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        cliente.send(send_length)
        cliente.send(message)
    
        
    # *Función que comunica con el servidor(engine) y hace lo que le mande
    def conectar_verify_engine(self, SERVER_eng, PORT_eng):              
        #Establece conexión con el servidor (engine)
        try:
            ADDR_eng = (SERVER_eng, PORT_eng)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR_eng)
           
            print (f"Establecida conexión (engine) en [{ADDR_eng}]")          
            #Una vez establecida la conexión
            message = f"{self.alias} {self.id} {self.token}"      
            self.enviar_mensaje(client , message)
            orden = ""
            #me espero  que me den la orden o ser rechazado
            while  orden == "":
                orden = self.receive_message(client)
                print( "orden" + orden)
                orden_preparada=orden.split(" ")
            if orden=="Rechazado":
                print("Conexion rechazada por el engine")
                client.close()
            elif (orden_preparada[0]=="RUN"):
                pos_fin = Coordenada(int(orden_preparada[1]),int(orden_preparada[2]))
                while (self.estado=="Rojo"):
                    self.mover(pos_fin)
                    self.enviar_mensaje(client, self.posicion[0] + " " + self.posicion[1])
                client.send("Vuelvo a base")
            elif orden=="END":
                client.close()
        except:
            print("No se ha podido establecer conexión(engine)")
        return client
        
    # *Función que comunica con el servidor(registri)
    def conectar_registri(self, server, port):              
        #Establece conexión con el servidor (engine)
        try:
            ADDR = (server, port)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR)
            print (f"Establecida conexión (registri) en [{ADDR}]")
        except:
            print("No se ha podido establecer conexión(registri)")
        return client

    # *Menú del dron para interactuar con registry
    def menu(self, server_reg, port_reg, cliente , SERVER_eng , PORT_eng):
        token=""
        opc = 0
        while(opc>4 or opc<1):
            print("\nHola, soy un dron, qué operación desea realizar?")
            print("[1] Dar de alta")
            print("[2] Editar perfil")
            print("[3] Dar de baja")
            print("[4] Añadir al espectaculo")
            print("[5] Desconectar")
            opc=int(input())
            if(opc<1 or opc>5):
                print("Opción no válida, inténtelo de nuevo")
                
            
        
        if (opc==1):
                alias = ""
                print("\nIntroduce mi alias")
                alias = input()
                #Hasta aquí hemos recopilado los datos y vamos a conectarnos al registry
                message = f"{opc} {alias}"
                self.enviar_mensaje(cliente, message)
                #Hemos enviado los datos y esperamos respuesta con nuestro token 
                token =""              
                while (token==""):
                    print("Estamos dentro")
                    msg_length = cliente.recv(HEADER).decode(FORMAT)
                    if msg_length:
                        msg_length = int(msg_length)
                        token = cliente.recv(msg_length).decode(FORMAT)
                    #token = self.receive_message(cliente)
                print("Esta es la token" + token)    
                                               
                token_manejable=token.split(" ")
                #si nuestro token empieza con tkn hemos podido registrarnos, si no no y volvemos a introducir datos
            
                self.alias=token_manejable[0]
                self.id=token_manejable[1]
                self.token=token_manejable[2]
                print("Ya tengo mi token y estoy dado de alta")
                
                
                
        elif (opc==2):
                      
                print("Dime el Alias del dron que quieres modificar")
                alias = input()
                
                #Hasta aquí hemos recopilado los datos y vamos a conectarnos al registry
                message = f"{opc} {alias}"      
                self.enviar_mensaje(cliente, message)
                
                #Hemos enviado los datos y esperamos respuesta de si podemos editar              
                edit = ""           
                message = cliente.recv(HEADER).decode(FORMAT)
                message = int(message)
                message = cliente.recv(message).decode(FORMAT)
                
                if message != "No existe":              
                    print(message) 
                    alias = input()
                                            
                    message_bytes = alias.encode(FORMAT)
                    message_length = len(message_bytes)
                    cliente.send(str(message_length).encode(FORMAT))
                    cliente.send(message_bytes)
                       
                    edit = cliente.recv(HEADER).decode(FORMAT)
                    if edit:
                        
                        edit = int(edit)
                        edit = cliente.recv(edit).decode(FORMAT)
                
                if(edit == "ok"):
                    print("Sus credenciales han sido modificadas con éxito")
                else:
                    print("No hay registros en la base de datos, pruebe a registrarse")
                       
        elif (opc==3):
            print("Introduce el alias del dron que quieres eliminar")
            alias = input()
            #Hasta aquí hemos recopilado los datos y vamos a conectarnos al registry
            message = f"{opc} {alias}"
            self.enviar_mensaje(cliente, message)
            
            print("soy el cliente")
            
            message = cliente.recv(HEADER).decode(FORMAT)
            message = int(message)
            message = cliente.recv(message).decode(FORMAT)
            
            if(message == "ok"):
                print("El dron ", alias , " se ha eliminado con exito")
            else:
                print("No se ha encontrado al dron ", alias , " en la base de datos ")
                        
        elif (opc==5):
            cliente.close()
            sys.exit(1)

        elif (opc==4):
            cliente_eng = dron.conectar_verify_engine(SERVER_eng,PORT_eng)

        if(opc!=5):
            dron.menu(SERVER,PORT, cliente_reg , SERVER_eng , PORT_eng)
            
            


if (len(sys.argv) == 5):
    SERVER = sys.argv[1]
    PORT = int(sys.argv[2])
    ADDR = (SERVER, PORT)   
    dron = Dron()
    #cliente_reg = dron.conectar_registri(SERVER,PORT)
    SERVER_eng = sys.argv[3]
    PORT_eng = int(sys.argv[4])
    ADDR_eng = (SERVER, PORT)
    #dron.menu(SERVER,PORT, cliente_reg,SERVER_eng , PORT_eng)
    dron.conectar_verify_engine(SERVER_eng, PORT_eng)
    mensaje=""
    
    dron.recibir_destino("127.0.0.1", 9092)
    print(dron.destino)
