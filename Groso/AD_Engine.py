import socket
import sys
import math
from coordenada import *
from tablero import *
from AD_Drone import *

class AD_Engine:
    
    # *Constructor
    def __init__(self, mapa, puerto_escucha, n_maxDrones, puerto_broker, puerto_weather):
        self.mapa = mapa
        self.puerto_escucha = puerto_escucha
        self.n_maxDrones = n_maxDrones
        self.puerto_broker = puerto_broker
        self.puerto_weather = puerto_weather
        self.drones = []
        self.destinos = []
        
    # *Comunica con el servidor clima y notifica el clima
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
    
    # *Notifica del estado del mapa a los drones
    def enviar_tablero(self, drones):
        for dron in drones:
            dron.recibir_mapa(self.mapa)
        
    # *Procesa el fichero de figuras
    def procesar_fichero(self, fichero):
        Hay_que_rellenar = "Hay que rellenar"
        
    # *Autentica si el dron está registrado
    def autenticar_dron(self, dron):
        Hay_que_rellenar = "Hay que rellenar"

    # *Notifica los destinos a los drones y los pone en marcha
    def notificar_destinos(self):
         for dron in self.drones:
            if dron.identificador in self.destinos:
                destino = self.destinos[dron.identificador]     #!No sé si esto está bien 
                dron.recibir_destino(destino)
   
    # *Acaba con la acción     
    def stop(self):
        Hay_que_rellenar = "Hay que rellenar"
    
    # *Inicia el sistema y contiene la estructura principal de funiconamiento
    def start(self, puerto): 
        Hay_que_rellenar = "Hay que rellenar"
