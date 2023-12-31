import socket
import tkinter as tk
import sys
import math
import time
from json import dumps
from coordenada import *
from tablero import *
from AD_Drone import *
import re
JSON_FILE = "BD.json"
import json
from confluent_kafka import Producer
import pickle
from kafka import KafkaProducer
from kafka import KafkaConsumer
from json import loads
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import datetime

import ssl

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from base64 import b64encode, b64decode

# Desactivar las advertencias de solicitud no segura debido a certificados autofirmados
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


HEADER = 64 
FORMAT = 'utf-8'
FIN = "FIN"
JSON_FILE = "BD.json"
SERVER = "127.0.0.2"
CONEX_ACTIVAS = 0

CERT = 'certServ.pem'
KEY = "clave_secreta_32b".ljust(32, ' ').encode('utf-8') 


class AD_Engine:
        
    # *Constructor
    def __init__(self,puerto_escucha, n_maxDrones, ip_broker ,puerto_broker,ip_weather, puerto_weather):
        self.mapa = Tablero(tk.Tk(),20,20)
        self.puerto_escucha = puerto_escucha
        self.n_maxDrones = n_maxDrones
        self.ip_broker = ip_broker
        self.puerto_broker = puerto_broker
        self.ip_weather = ip_weather
        self.puerto_weather = puerto_weather
        self.figuras = ""
        self.drones = []
        self.ciudad = ""
        self.url_api_eng = "https://localhost:3001"
        self.mostrar_mapa = False
        
        
        
        
    def encrypt_message(self, message, key):
        iv = b'\x00' * 12  # Vector de inicialización (puedes generar uno de forma segura)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(message.encode()) + encryptor.finalize()

        # Obtén el tag de autenticación
        tag = encryptor.tag

        return b64encode(iv + ciphertext + tag).decode('utf-8')

    def decrypt_message(self, ciphertext, key):
        # Decodifica la cadena base64
        ciphertexta = b64decode(ciphertext.encode('utf-8'))

        # Extrae el IV y el tag
        
        iv = ciphertexta[:12]
        ciphertext = ciphertexta[12:-16]
        tag = ciphertexta[-16:]

        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()

        # Desencripta el mensaje
        decrypted_message = decryptor.update(ciphertext) + decryptor.finalize()
        return decrypted_message.decode('utf-8')
    
    
    # * Funcion que envia un mensaje al servidor
    def enviar_mensaje(self, connstream, msg): 
        mensaje_bytes = msg.encode('utf-8')
        connstream.send(mensaje_bytes)
        
    
    # *Notifica del estado del mapa a los drones
    def enviar_tablero(self, servidor_kafka, puerto_kafka): # !KAFKA
        producer = KafkaProducer(bootstrap_servers= servidor_kafka + ":" + str(puerto_kafka))
        
        topic = "mapa_a_drones_topic"
                      
        time.sleep(0.3)
        producer.send(topic, pickle.dumps(self.mapa.cuadros))
        producer.flush()
        
        # *Notifica los destinos a los drones y los pone en marcha
    def notificar_destinos(self, figuras, n_fig, servidor_kafka, puerto_kafka): # !KAFKA
        producer = KafkaProducer(bootstrap_servers= servidor_kafka + ":" + str(puerto_kafka))
        
        topic = "destinos_a_drones_topic"
        
        drones_figura=""
        
        cont=1
        for clave in figuras:
            if cont == n_fig:
                drones_figura = figuras[clave]
                break
            cont=cont+1
           
        cadena = str(drones_figura)
        time.sleep(0.3)
        cadena = self.encrypt_message(cadena,KEY)
        producer.send(topic, dumps(cadena).encode('utf-8'))
        producer.flush()
        
    def notificar_motivo_vuelta_base(self, servidor_kafka, puerto_kafka, razon):
        producer =KafkaProducer(bootstrap_servers= servidor_kafka + ":" + str(puerto_kafka))
        topic = "motivo_a_drones_topic"
        
        time.sleep(0.3)
        razon = self.encrypt_message(razon,KEY)
        producer.send(topic, dumps(razon).encode('utf-8'))
        producer.flush()
        
    # * Funcion que recibe el destino del dron mediante kafka
    def recibir_posiciones(self, servidor_kafka, puerto_kafka, figura):
        consumer = KafkaConsumer(bootstrap_servers= servidor_kafka + ":" + str(puerto_kafka),
                                 consumer_timeout_ms=1400)
        id_recibidos=[]
        dron_menos=0
        
        topic = "posicion_a_engine_topic"
        
        consumer.subscribe([topic])
        
        for msg in consumer:
            if msg.value:
                mensa = loads(msg.value.decode('utf-8'))
                mensaje = self.decrypt_message(mensa,KEY) 
                
                separado = mensaje.split(',')
                id = int(separado[0])
                viejax = int(separado[1])
                viejay = int(separado[2])
                nuevax = int(separado[3])
                nuevay = int(separado[4])  
                
                id_recibidos = id_recibidos + [id]
                
                cont=1
                for clave in self.figuras:
                    if cont == figura:
                        drones_figura = self.figuras[clave]
                        break
                    cont=cont+1
                finalx=int(drones_figura[id].split(",")[0])
                finaly=int(drones_figura[id].split(",")[1])
                
                color = "red"
                if(finalx==nuevax and finaly==nuevay):
                    color = "green"
                    
                self.mapa.mover_contenido(id,(viejax,viejay),(nuevax,nuevay), color)
        
        #print("IDs recibidos: ", id_recibidos)
        #print("Mis drones :", self.drones)
        for id_s in self.drones:
            if id_s not in id_recibidos:
                print("Hemos perdido el dron: ", id_s)
                self.actualizar_logs_json(f"Ha caido el dron {id_s}.\n")
                self.mapa.borrar_del_mapa(id_s)
                self.drones = [x for x in self.drones if x != id_s]
                dron_menos=-1
                
        
        return dron_menos
                
        
    # *Acaba con la acción
    def stop(self):
        Hay_que_rellenar = "Hay que rellenar"
        
        
    
            
    # *Función que comunica con el servidor(engine) y hace lo que le mande
    def contactar_weather(self, ip_weather, port_weather):              
        #Establece conexión con el servidor (weather)
        try:
            ADDR_wth = (ip_weather, port_weather)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR_wth)

            print (f"Establecida conexión (weather) en [{ADDR_wth}]")
            self.actualizar_logs_json("Situaciones climáticas adversas, los drones vuelven a casa.\n")  
            
            self.enviar_mensaje(client, self.ciudad)
                    
            #Una vez establecida la conexión
            temperatura = ""
            while temperatura == "":
                long = client.recv(HEADER).decode(FORMAT)
                if long:
                    long = int(long)
                    temperatura = client.recv(long).decode(FORMAT) 
            return int(temperatura)
        except:
            print("No se ha podido establecer conexión(engine)")
            return "Fallo"
            
    # *Procesa el fichero de figuras
    def procesar_fichero(self, fichero):
        figuras = {}  
        figura_actual = {}  

        with open(fichero, 'r') as archivo:
            data = json.load(archivo)

        for figura in data['figuras']:
            nombre_figura = figura['Nombre'] 
            drones = figura['Drones']
                       
            
            for drone in drones:
                id_drone = (drone['ID'])
                Cord = str(drone['POS'])
                #pos_x = int(posicion.split(",")[0])
                #pos_y = int(posicion.split(",")[1])
                #Cord = pickle.dumps(Coordenada(pos_x,pos_y))
                figura_actual[id_drone] = Cord
                               
            figuras[nombre_figura] = figura_actual
            figura_actual = {}
            # *? Ejemplo de figuras ("Pollito" : [5 : {2,3} , 6 : {5,6} .... ], "Corazón" : [....] , ....)
        self.figuras = figuras
        
    # *Autentica si el dron está registrado
    def autenticar_dron(self, connstream):
        
        messag = connstream.recv(1024)
        
        print("el messag es:",messag)
        message = messag.decode('utf-8')
        
        print("el mensaje que me llega es:",message)
            #Spliteamos el mensaje en alias y token y leemos el json
        alias = message.split()[0]
        id = int(message.split()[1])
        token = message.split()[2]  
        
        print("la id es:" , id)
        print("el token es:", token)

        if token != "API":
            try:
                with open('BD.json', 'r') as file:
                    data = json.load(file)
            except FileNotFoundError:
                print("No se encontró el archivo")
                data = {}  

            # Comprobamos que el alias y el token están en el json
            for clave, valor in data.items():
                if "token" in valor and valor["token"] == token:
                    message_to_send = "Dron verificado"
                    self.enviar_mensaje(connstream, message_to_send)
                    print("He entrado jefote")
                    self.drones.append(int(id))
                    return True
                elif valor["id"] == id:
                    message_to_send = "Rechazado"
                    self.enviar_mensaje(connstream, message_to_send)
                    print("Me he equivocado de camino jefote")
            return False
        else:
            url = f"{self.url_api_eng}/ids_verificados"  # Reemplaza esto con la URL de tu API Engine
            try:
                response = requests.get(url, verify=False)
                if response.status_code == 200:
                    data = response.json()  # Obtener el diccionario desde la respuesta JSON
                    ids_verificados = data.get('idsVerificados', [])  # Obtener la lista de IDs verificados del diccionario                        print(ids_verificados)
                    if id in ids_verificados:
                        print(f"El ID {id} está en la lista de IDs verificados.")
                        message_to_send = "Dron verificado"
                        self.enviar_mensaje(connstream, message_to_send)
                        self.drones.append(int(id))
                        return True
                    else:
                        print(f"El ID {id} no está en la lista de IDs verificados.")
                        message_to_send = "Rechazado"
                        self.enviar_mensaje(connstream, message_to_send)
                        return False                    
                else:
                    print(f"Error al obtener la lista de IDs verificados. Código de estado: {response.status_code}")
                    message_to_send = "Rechazado"
                    self.enviar_mensaje(connstream, message_to_send)
                    return False
            except requests.RequestException as e:
                print(f"Error de conexión: {e}")
            
    def dibujar_tablero_engine(self):
        root = tk.Tk()
        tablero = Tablero(root, 20, 20)
        tablero.cuadros=self.mapa.cuadros
        tablero.dibujar_tablero()
        
        
    def acabada_figura(self, n_fig):
    # Busca la figura correspondiente al número proporcionado (n_fig)
        cont = 1
        for clave in self.figuras:
            if cont == n_fig:
                figura = self.figuras[clave]
                break
            cont = cont + 1

        # Verifica cada posición de la figura en el mapa
        for clave in figura:
            if clave in self.drones:
                x = int(figura[clave].split(",")[0]) - 1
                y = int(figura[clave].split(",")[1]) - 1

                
                if self.mapa.cuadros[x][y] != 0:
                
                    if clave != self.mapa.cuadros[x][y][0][0]:
                        return False  
                else:
                    return False  

       
        return True  
    
    def acabado_espectaculo(self, n_fig, n_drones):
        acabada=False
        if(self.mapa.cuadros[0][0]!=0):
            if len(self.mapa.cuadros[0][0][0]) == n_drones:
                acabada=True

        return acabada  

    def volver_a_base(self, n_fig):
        self.figuras = {figura: {punto: '1,1' for punto in coordenadas} for figura, coordenadas in self.figuras.items()}
        self.notificar_destinos(self.figuras, n_fig, self.ip_broker, 9092)
        
    def figura_completada(self):
        print("Figura completada.")
        root = tk.Tk()
        tablero = Tablero(root, 20, 20)
        tablero.cuadros=self.mapa.cuadros
        if self.mostrar_mapa == True:
            tablero.dibujar_tablero()

    def obtener_temperatura(self, api_key):
        # Cargar el archivo JSON
        with open("ciudades.json") as file:
            datos = json.load(file)

        self.ciudad = str(datos["ciudad"])
        
        url = f'http://api.openweathermap.org/data/2.5/weather?q={self.ciudad}&appid={api_key}&units=metric'
        # 'units=metric' para obtener la temperatura en grados Celsius


        response = requests.get(url)
        if response.status_code == 200:
            datos_clima = response.json()
            temperatura = datos_clima['main']['temp']
            return temperatura
        else:
            print("Error al obtener la temperatura:", response.status_code)
            return "Fallo"
            
    def actualizar_mapa_json(self):
        # Cargar el archivo JSON existente
        with open('BD.json', 'r') as file:
            data = json.load(file)
                    
        # Actualizar los datos existentes con los nuevos datos
        data["mapa"] = self.mapa.cuadros

        # Guardar los cambios en el archivo
        with open('BD.json', 'w') as file:
            json.dump(data, file)
            
    def actualizar_tem_ciudad_json(self, ciudad, temp):
        # Cargar el archivo JSON existente
        with open('BD.json', 'r') as file:
            data = json.load(file)
                    
        # Actualizar los datos existentes con los nuevos datos
        data["clima"] = [ciudad, temp]

        # Guardar los cambios en el archivo
        with open('BD.json', 'w') as file:
            json.dump(data, file)
            
    def actualizar_logs_json(self, newlog):
        # Cargar el archivo JSON existente
        with open('BD.json', 'r') as file:
            data = json.load(file)
            
        newlog = f"[{self.obtener_ip()}][{self.obtener_fecha_hora()}] {newlog}"
                    
        if 'logs' in data:
            logs = data["logs"]
            # Actualizar los datos existentes con los nuevos datos
            logs.append(newlog)
            data["logs"] = logs
        else:
            data["logs"] = [newlog]
            
        # Guardar los cambios en el archivo
        with open('BD.json', 'w') as file:
            json.dump(data, file)
            
    def obtener_ip(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    
    
    def obtener_fecha_hora(self):
        # Obtiene la fecha y hora actuales
        fecha_hora_actual = datetime.now()
        
        # Convierte la fecha y la hora en strings
        fecha_actual = fecha_hora_actual.strftime("%Y-%m-%d")  # Formato: Año-Mes-Día
        hora_actual = fecha_hora_actual.strftime("%H:%M:%S")  # Formato: Hora:Minutos:Segundos
        
        return f"{fecha_actual} {hora_actual}"
    
            
    def handle_client(self, connstream, addr):
        print(f"[NUEVA CONEXION] {addr} connected.")
        global CONEX_ACTIVAS
        CONEX_ACTIVAS = CONEX_ACTIVAS + 1
        if self.autenticar_dron(connstream) == False:
            CONEX_ACTIVAS = CONEX_ACTIVAS - 1
            connstream.close()
            return False
        self.mapa.introducir_en_posicion(1,1,([self.drones[len(self.drones)-1]],1,"red"))
        #weather = self.contactar_weather(ip_weather, puerto_weather)
        weather = self.obtener_temperatura("73d22518c7b690c635b670eb9a918309")
        
        for n_fig in range(len(self.figuras)):    
            n_fig = n_fig+1
            
            cont = 1
            for clave in self.figuras:
                if cont == n_fig:
                    figura = self.figuras[clave]
                    break
                cont = cont + 1
            
            if n_fig==1:
                n_drones=len(figura)
            
            #print("Conexiones ", CONEX_ACTIVAS)
            #print("N_drones ", n_drones)

            if CONEX_ACTIVAS == n_drones:
                self.actualizar_mapa_json()
                self.actualizar_tem_ciudad_json(self.ciudad, weather)
                
                if(weather!="Fallo"):
                    if(weather>0):
                            self.notificar_motivo_vuelta_base(ip_broker, puerto_broker, "Nada")    
                            self.notificar_destinos(self.figuras, n_fig, self.ip_broker, 9092)
                            self.actualizar_mapa_json()
                            if self.mostrar_mapa == True:
                                self.dibujar_tablero_engine()

                            salimos = False
                            while (salimos==False):
                                self.enviar_tablero(self.ip_broker, self.puerto_broker)               
                                resta=self.recibir_posiciones(self.ip_broker, self.puerto_broker, n_fig)
                                n_drones=n_drones + resta       
                                CONEX_ACTIVAS = CONEX_ACTIVAS + resta
                                self.actualizar_mapa_json()
                                if self.mostrar_mapa == True:
                                    self.dibujar_tablero_engine()               
                                salimos = self.acabada_figura(n_fig)
                                self.notificar_motivo_vuelta_base(ip_broker, puerto_broker, "Nada")
                                self.notificar_destinos(self.figuras, n_fig, self.ip_broker, 9092)
                                weather = self.obtener_temperatura("73d22518c7b690c635b670eb9a918309")
                                self.actualizar_tem_ciudad_json(self.ciudad, weather)
                                if(weather=="Fallo" or weather<=0):
                                    break
                                             
                            if(salimos==True):           
                                self.figura_completada()
                                self.actualizar_logs_json(f"Figura {n_fig} acabada.\n")
                                
                            if (n_fig==len(self.figuras)):
                                print("Todas las figuras acabadas, volvemos a casa.")
                                self.actualizar_logs_json(f"Todas las figuras completadas, los drones vuelven a casa.\n")
                                self.notificar_motivo_vuelta_base(ip_broker, puerto_broker, "Acabado")
                                self.volver_a_base(n_fig)
                                acabamos = False
                                while (acabamos==False):
                                    self.enviar_tablero(self.ip_broker, self.puerto_broker)               
                                    resta=self.recibir_posiciones(self.ip_broker, self.puerto_broker, n_fig)
                                    n_drones=n_drones + resta 
                                    NEX_ACTIVAS = CONEX_ACTIVAS + resta
                                    self.actualizar_mapa_json()    
                                    if self.mostrar_mapa == True:         
                                        self.dibujar_tablero_engine()               
                                    acabamos = self.acabado_espectaculo(n_fig, CONEX_ACTIVAS)
                                    self.notificar_motivo_vuelta_base(ip_broker, puerto_broker, "Acabado")
                                    self.notificar_destinos(self.figuras, n_fig, self.ip_broker, 9092)                            
                                                                                
                            if (weather != "Fallo" and weather<1):
                                self.notificar_motivo_vuelta_base(ip_broker, puerto_broker, "Mal tiempo")
                                print("Volvemos a casa, situaciones climáticas adversas")
                                self.actualizar_logs_json("Situaciones climáticas adversas, los drones vuelven a casa.\n")
                                self.volver_a_base(n_fig)
                                acabamos = False
                                while (acabamos==False):
                                    self.enviar_tablero(self.ip_broker, self.puerto_broker)               
                                    resta=self.recibir_posiciones(self.ip_broker, self.puerto_broker, n_fig)
                                    n_drones=n_drones + resta       
                                    CONEX_ACTIVAS = CONEX_ACTIVAS + resta
                                    self.actualizar_mapa_json()
                                    if self.mostrar_mapa == True:                               
                                        self.dibujar_tablero_engine()               
                                    acabamos = self.acabado_espectaculo(n_fig, n_drones)
                                    self.notificar_motivo_vuelta_base(ip_broker, puerto_broker, "Mal tiempo")
                                    self.notificar_destinos(self.figuras, n_fig, self.ip_broker, 9092)
                                break
                                    
                            elif (weather=="Fallo"):
                                self.notificar_motivo_vuelta_base(ip_broker, puerto_broker, "No tiempo")
                                print("No podemos contactar con weather, volvemos a casa")
                                self.actualizar_logs_json("No podemos contactar con weather, los drones vuelven a casa.\n")
                                self.volver_a_base(n_fig)
                                acabamos = False
                                while (acabamos==False):
                                    self.enviar_tablero(self.ip_broker, self.puerto_broker)               
                                    resta=self.recibir_posiciones(self.ip_broker, self.puerto_broker, n_fig)
                                    n_drones=n_drones + resta       
                                    CONEX_ACTIVAS = CONEX_ACTIVAS + resta
                                    self.actualizar_mapa_json()  
                                    if self.mostrar_mapa == True:                                
                                        self.dibujar_tablero_engine()               
                                    acabamos = self.acabado_espectaculo(n_fig, n_drones)
                                    self.notificar_motivo_vuelta_base(ip_broker, puerto_broker, "No tiempo")
                                    self.notificar_destinos(self.figuras, n_fig, self.ip_broker, 9092)
                                break
                    else:
                        print("CONDICIONES CLIMATICAS ADVERSAS ESPECTACULO FINALIZADO")
                        self.actualizar_logs_json("Situaciones climáticas adversas, los drones vuelven a casa.\n")
                        self.notificar_motivo_vuelta_base(ip_broker, puerto_broker, "Mal tiempo")
                else:
                    print("No se puede contactar con weather, no podemos iniciar el vuelo") 
                    self.actualizar_logs_json("No podemos contactar con weather, los drones vuelven a casa.\n")
                    self.notificar_motivo_vuelta_base(ip_broker, puerto_broker, "No tiempo")
                    
      
        #conn.close()

    def start(self):
        
        #Este es de la practica 1
        #server.listen()
        #practica 2
        bindsocket.listen(MAX_CONEXIONES)
        print(f"Escuchando en {SERVER} {puerto_escucha}" )
        
        
        CONEX_ACTIVAS = threading.active_count()-1
        print(CONEX_ACTIVAS)
        while True:
            newsocket, fromaddr = bindsocket.accept()
            connstream = context.wrap_socket(newsocket,server_side=True)
            #conn, addr = server.accept()
            if (CONEX_ACTIVAS <= MAX_CONEXIONES): 
                thread = threading.Thread(target= self.handle_client, args=(connstream, fromaddr))
                thread.start()
                               
                
                print(f"[CONEXIONES ACTIVAS] {CONEX_ACTIVAS}")     
                print("CONEXIONES RESTANTES PARA CERRAR EL SERVICIO", MAX_CONEXIONES-CONEX_ACTIVAS)
            else:
                print("OOppsss... DEMASIADAS CONEXIONES. ESPERANDO A QUE ALGUIEN SE VAYA")
                connstream.shutdown(socket.SHUT_RDWR)
                connstream.close()
                CONEX_ACTUALES = threading.active_count()-1
        

######################### MAIN ##########################

if (len(sys.argv) == 7):
    fichero="AwD_figuras_correccion.json"
    puerto_escucha = int(sys.argv[1])
    max_drones = int(sys.argv[2])
    ip_broker = sys.argv[3]
    puerto_broker = int(sys.argv[4])
    ip_weather= sys.argv[5]
    puerto_weather = int(sys.argv[6])
    
    
    ADDR = (SERVER, puerto_escucha) 
    print("[STARTING] Servidor inicializándose...")
    """server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)"""
    
    #ESTO ES DE LA PRACTICA 2 LOS SSL DE SOCKET
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(CERT,CERT)
    bindsocket = socket.socket()
    bindsocket.bind((SERVER ,puerto_escucha))
    MAX_CONEXIONES = max_drones
    
    
    engine = AD_Engine(puerto_escucha, max_drones, ip_broker , puerto_broker, ip_weather, puerto_weather)
    engine.procesar_fichero(fichero)
    if fichero != "":   
        engine.start()
        
