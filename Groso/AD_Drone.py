from coordenada import *
import socket
import sys
import math
import threading
import json
import time
import secrets
from json import dumps
import tkinter as tk
import string
from kafka import KafkaProducer
from tablero import *
import pickle
#Consumidor.
from kafka import KafkaConsumer
from json import loads

HEADER = 64
FORMAT = 'utf-8'

class Dron:
    
    # *Constructor
    def __init__(self):
        self.id = 1
        self.alias = ""
        self.color = "Rojo"
        self.coordenada = Coordenada(1,1)
        self.token = ""
        self.destino = ""
        self.mapa = Tablero(tk.Tk(),20,20)
        
    # *Movemos el dron dónde le corresponde y verificamos si ha llegado a la posición destino
    def mover(self, pos_fin):
        self.coordenada = self.siguiente_mov(pos_fin)
        if (self.coordenada.x==pos_fin.x and self.coordenada.y==pos_fin.y):
            self.estado = "Verde"  # Cambiar a estado final si ha llegado a la nueva posición
        
    def receive_message(self, client):
        msg_length = client.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            message = client.recv(msg_length).decode(FORMAT)

        return message
        
    # *Encontramos el siguiente movimiento que debe hacer
    def siguiente_mov(self, pos_fin):
        x = [-1, 0, 1]
        y = [-1, 0, 1]
        ini = [self.coordenada.x, self.coordenada.y]  # Obtener las coordenadas de pos_ini
        anterior = 30.0
        resul = Coordenada(0, 0)  # Inicializar el resultado como una Coordenada

        for i in x:
            for j in y:
                optima = [ini[0] + i, ini[1] + j]

                # Ajusta las coordenadas si salen del rango 1-20
                for k in range(2):
                    if optima[k] > 20:
                        optima[k] -= 20
                    if optima[k] < 1:
                        optima[k] += 20

                distancia = math.sqrt(((optima[0] - pos_fin.x) ** 2) + ((optima[1] - pos_fin.y) ** 2))

                if distancia < anterior:
                    anterior = distancia
                    resul.x =optima[0]  # Actualiza el resultado como una Coordenada
                    resul.y =optima[1]
        return resul


    
    # !Kafka:
    
    # * Funcion que recibe el destino del dron mediante kafka
    def recibir_destino_con_timeout(self, servidor_kafka, puerto_kafka, timeout_segundos, cliente):
        consumer = KafkaConsumer(bootstrap_servers=f"{servidor_kafka}:{puerto_kafka}")
        topic = "destinos_a_drones_topic"
        consumer.subscribe([topic])

        try:
            msg = consumer.poll(timeout_ms=timeout_segundos * 1000)
            if msg:
                mensaje = loads(next(iter(msg.values()))[0].value.decode('utf-8'))
                self.destino = eval(mensaje)[self.id]
                x, y = map(int, self.destino.split(","))
                self.destino = Coordenada(x, y)
            else:
                print("Error: No se pudo recibir el destino. El engine no está operativo.")
                cliente.close()

        except KafkaTimeoutError:
            print("Error: Se agotó el tiempo de espera. El engine no está operativo.")
            cliente.close()

    # * Función para recibir el mapa
    def recibir_mapa(self, servidor_kafka, puerto_kafka):
        consumer = KafkaConsumer(bootstrap_servers= servidor_kafka + ":" + str(puerto_kafka))

        topic = "mapa_a_drones_topic"
        
        consumer.subscribe([topic])
        
        for msg in consumer:
            if msg.value:
                mensaje = pickle.loads(msg.value)
                
                break  # Sale del bucle al recibir un mensaje exitoso
            
        return mensaje
    # *Notifica del estado del mapa a los drones
    def enviar_tablero(self, servidor_kafka, puerto_kafka): # !KAFKA
        producer = KafkaProducer(bootstrap_servers= servidor_kafka + ":" + str(puerto_kafka))
        
        topic = "mapa_a_engine_topic"
                      
        time.sleep(0.3)
        producer.send(topic, pickle.dumps(self.mapa))
        producer.flush()
        
        # *Notifica los destinos a los drones y los pone en marcha
    def notificar_posicion(self, servidor_kafka, puerto_kafka, pos_vieja): # !KAFKA
        producer = KafkaProducer(bootstrap_servers= servidor_kafka + ":" + str(puerto_kafka))
        
        topic = "posicion_a_engine_topic"
           
        #cadena = f"Id: ({self.id}) vieja: ({pos_vieja.x},{pos_vieja.y}) nueva: ({self.coordenada.x },{self.coordenada.y})" 
        cadena = f"{self.id},{pos_vieja.x},{pos_vieja.y},{self.coordenada.x },{self.coordenada.y}"
        time.sleep(0.3)
        producer.send(topic, dumps(cadena).encode('utf-8'))
        producer.flush()
    
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
                orden_preparada = orden.split(" ")
                
            if orden == "Rechazado":
                print("Conexión rechazada por el engine")
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

    def dibujar_tablero_dron(self):
        root = tk.Tk()
        tablero = Tablero(root, 20, 20)
        tablero.cuadros=self.mapa.cuadros
        tablero.dibujar_tablero()
        

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
            
            opc=int(sys.stdin.readline())
            
            if(opc<1 or opc>5):
                print("Opción no válida, inténtelo de nuevo")
        
        if (opc==1):
                alias = ""
                print("\nIntroduce mi alias")
                alias = sys.stdin.readline()
                #Hasta aquí hemos recopilado los datos y vamos a conectarnos al registry
                message = f"{opc} {alias}"
                self.enviar_mensaje(cliente, message)
                #Hemos enviado los datos y esperamos respuesta con nuestro token 
                token =""              
                msg_length = cliente.recv(HEADER).decode(FORMAT)
                if msg_length:
                    msg_length = int(msg_length)
                    token = cliente.recv(msg_length).decode(FORMAT)
                
                    #token = self.receive_message(cliente)   
                                               
                token_manejable=token.split(" ")
                #si nuestro token empieza con tkn hemos podido registrarnos, si no no y volvemos a introducir datos

                self.alias=token_manejable[0]
                self.id=int(token_manejable[1])
                self.token=token_manejable[2]

                
                
                
        elif (opc==2):
                      
                print("Dime el Alias del dron que quieres modificar")
                alias = sys.stdin.readline()
                
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
                    alias = sys.stdin.readline()
                                            
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
            alias = sys.stdin.readline()
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
            
                cliente = self.conectar_verify_engine(SERVER_eng, PORT_eng)
                

                while True:
                    try:
                        self.recibir_destino_con_timeout("127.0.0.1", 9092,9,cliente)
                        mapa_actualizado_cuadros = self.recibir_mapa("127.0.0.1", 9092)
                        if mapa_actualizado_cuadros != self.mapa.cuadros:
                            self.mapa.cuadros = mapa_actualizado_cuadros
                            pos_vieja = self.coordenada
                            self.mover(self.destino)
                            self.notificar_posicion("127.0.0.1", 9092, pos_vieja)
                            print("Destino:", self.destino.x, ",", self.destino.y)
                            print("Posicion:", self.coordenada.x, ",", self.coordenada.y)
                    except:
                        print("Conexión con el servidor perdida.")
                        break
        
        if(opc!=5):
            self.menu(SERVER,PORT, port_reg , SERVER_eng , PORT_eng)


if (len(sys.argv) == 5):
    SERVER = sys.argv[1]
    PORT = int(sys.argv[2])
    ADDR = (SERVER, PORT)   
    dron = Dron()
    cliente_reg = dron.conectar_registri(SERVER,PORT)
    SERVER_eng = sys.argv[3]
    PORT_eng = int(sys.argv[4])
    ADDR_eng = (SERVER, PORT)
    dron.menu(SERVER, PORT, cliente_reg, SERVER_eng , PORT_eng)
    
            
            
            
            
        