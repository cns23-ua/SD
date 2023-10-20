import socket
import sys
import math
from coordenada import *
from tablero import *

class AD_Engine:
    
    # *Constructor
    def __init__(self, puerto_escucha, n_maxDrones, puerto_broker, puerto_weather):
        self.puerto_escucha = puerto_escucha
        self.n_maxDrones = n_maxDrones
        self.puerto_broker = puerto_broker
        self.puerto_weather = puerto_weather
        
    def consultar_clima(self, server, port):
         #Establece conexión con el servidor (weather)
        try:
            ADDR = (server, port)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR)
            print (f"Establecida conexión (weather) en [{ADDR}]")
            
        except:
            print("No se ha podido establecer conexión(weather)")
        
        return client
    
    def enviar_tablero(self, tablero, dron):
        Hay_que_rellenar = "Hay que rellenar"
        
    def procesar_fichero(self, fichero):
        Hay_que_rellenar = "Hay que rellenar"

    def notificar_posición(self, posicion, dron):
        Hay_que_rellenar = "Hay que rellenar"
    
     # *Inicia el sistema y contiene la estructura principal de funiconamiento
    def start(self, puerto): 
        Hay_que_rellenar = "Hay que rellenar"
