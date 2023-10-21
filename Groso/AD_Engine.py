import socket
import sys
import math
from coordenada import *
from tablero import *
from AD_Drone import *
import re
JSON_FILE = "BD.json"
import json


HEADER = 64
FORMAT = 'utf-8'

class AD_Engine:
    
    
    #! HAY QUE GESTIONAR EN DRON LA CONEXIÓN AL ENGINE Y EL PASE DE PARÁMETROS DE ID Y TOKEN EN MENSAJE
    
    # *Constructor
    def __init__(self, mapa, puerto_escucha, n_maxDrones, puerto_broker, puerto_weather):
        self.mapa = mapa
        self.puerto_escucha = puerto_escucha
        self.n_maxDrones = n_maxDrones
        self.puerto_broker = puerto_broker
        self.puerto_weather = puerto_weather
        
        # *Función que envia mensaje
    def send_message(message_to_send , conn):
        message_bytes = message_to_send.encode(FORMAT)
        message_length = len(message_bytes)
        conn.send(str(message_length).encode(FORMAT))
        conn.send(message_bytes)
        
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
            self.send_message(message, client)
            
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
    def enviar_tablero(self, dron, addr): # !KAFKA
        Hay_que_rellenar = "Hay que rellenar"
            
    # *Procesa el fichero de figuras
    def procesar_fichero(self, fichero):
        figuras = []  # Lista que contendrá las figuras que haya en el fichero
        figura_actual = []  # Inicialmente no hay figura actual

        with open(fichero, 'r') as file:
            for linea in file:
                if "><" in linea:
                    # Extraemos los valores de la linea
                    valores = [int(numero) for numero in re.findall(r'<(\d+)>', linea)]
                    if len(valores) == 3:
                        id_dron, coord_x, coord_y = valores
                    posicion = Coordenada(coord_x,coord_y) 
                    #Si dron autenticado añadimos    
                    if self.autenticar_dron(id_dron):
                        #Diccionario que asigna un id(int) a una coordenada(objeto)                   #* <-Aquí
                        figura_actual[id_dron]=posicion
                elif "</" in linea:
                    #Almacenamos la figura en el diccionario de figuras y limpiamos la figura actual
                    nombre_figura = linea.replace("</", "").replace(">", "")
                    #Diccionario que asigna un nombre(string) a una figura_actual(especificado arriba) # *^
                    figuras[nombre_figura] = figura_actual
                    figura_actual.clear()
        # *? Ejemplo de figuras ("Pollito" : [5 : {2,3} , 6 : {5,6} .... ], "Corazón" : [....] , ....)
        return figuras
        
    # *Autentica si el dron está registrado
    def autenticar_dron(self, conn):
        print(f"[NUEVA CONEXION] {conn} connected.")
        verifed = False
        while verifed == False:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                token = conn.recv(msg_length).decode(FORMAT)
                msg_length = int(msg_length)
                message = conn.recv(msg_length).decode(FORMAT)
            #Spliteamos el mensaje en id y token y leemos el json
            id = int(message.split()[0])
            token = message.split()[1]
            try:
                with open(JSON_FILE, "r") as file:
                    data = json.load(file)
            except FileNotFoundError:
                print("No se encontró el archivo")
                data = {}  
            # Comprobamos que el id y el token están en el json
            if id in data:
                if token in data:
                    message_to_send = "Dron verificado"
                    self.send_message(message_to_send, conn)
                    verifed = True
                else:
                    message_to_send = "Verificación fallida"
                    self.send_message(message_to_send, conn)
                    verifed = True
            else:
                message_to_send = "Verificación fallida"
                self.send_message(message_to_send, conn)
                verifed = True
                
    # *Notifica los destinos a los drones y los pone en marcha
    def notificar_destinos(self, drones): # !KAFKA
         for dron in drones:
            if dron.identificador in self.destinos:
                destino = drones[dron.identificador]     #!Para que esto drones tiene que ser 
                dron.recibir_destino(destino)                   #!un diccionario del tipo id_dron : destinos(coordenada)
   
    # *Acaba con la acción
    def stop(self):
        Hay_que_rellenar = "Hay que rellenar"
    
    # *Inicia el sistema y contiene la estructura principal de funiconamiento
    def start(self, puerto): 
        Hay_que_rellenar = "Hay que rellenar"
