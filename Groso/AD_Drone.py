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
from confluent_kafka import KafkaException, KafkaError
import ssl
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from base64 import b64encode, b64decode


KEY = "clave_secreta_32b".ljust(32, ' ').encode('utf-8')
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
        
        
        
    def encrypt_message(self, message, key):
        iv = b'\x00' * 12  # Vector de inicialización (puedes generar uno de forma segura)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(message.encode()) + encryptor.finalize()

        # Obtén el tag de autenticación
        tag = encryptor.tag
        print("el length del tag es:" , len(tag))

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
    
    def  receive_message_ssl(self,ssock):
        data = ssock.recv(1024)
        return data.decode('utf-8')
        
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
    def recibir_destino(self, servidor_kafka, puerto_kafka, timeout_segundos,cliente):
        consumer = KafkaConsumer(bootstrap_servers=f"{servidor_kafka}:{puerto_kafka}")
        topic = "destinos_a_drones_topic"
        consumer.subscribe([topic])

        fallo = False
        mensaje = None

        try:
            # Configurar el temporizador para esperar el mensaje
            msg = consumer.poll(timeout_ms=timeout_segundos * 1000)

            if msg:
                mensaje = loads(next(iter(msg.values()))[0].value.decode('utf-8'))
                self.destino = eval(mensaje)[self.id]
                x, y = map(int, self.destino.split(","))
                if((x > 20 or x < 1) or (y > 20 or y < 1)):
                    print("mi posicion no es valida me voy del espectaculo")
                    cliente.close()
                    fallo = True
                self.destino = Coordenada(x, y)
            else:
                print("Error: No se pudo recibir el destino. El engine no está operativo.")
                # Aquí puedes agregar código para manejar la falta de mensaje, por ejemplo, lanzar una excepción.
                cliente.close()

        except KafkaException as e:
            if isinstance(e, KafkaError) and e.args[0].code() == KafkaError._TIMED_OUT:
                print("Error: Se agotó el tiempo de espera. El engine no está operativo.")
                
            cliente.close()
            
        return fallo

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
            
            
    def recibir_motivo_vuelta(self, servidor_kafka, puerto_kafka, hecho):
        consumer = KafkaConsumer(bootstrap_servers= servidor_kafka + ":" + str(puerto_kafka))

        topic = "motivo_a_drones_topic"
        
        consumer.subscribe([topic])
        
        mensaje=""
        
        if(hecho==False):
        
            for msg in consumer:
                if msg.value:
                    mensaje = loads(msg.value.decode('utf-8'))
                    print("Mensaje: ", mensaje)
                    if(mensaje=="No tiempo"):
                        print("No podemos contactar con weather, volvemos a casa")
                        hecho=True
                    elif(mensaje=="Mal tiempo"):
                        print("Volvemos a casa, situaciones climáticas adversas")
                        hecho=True
                    elif(mensaje=="Acabado"):
                        print("Todas las figuras completadas, volvemos a la base")
                        hecho=True
                    break
                
        return hecho
                                
                
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
        print("el mensaje sin cifrar es:" , cadena)
        msg = self.encrypt_message(cadena,KEY)
        print("el mensaje  cifrado es:" , msg)
        
        producer.send(topic, dumps(msg).encode('utf-8'))
        producer.flush()
    
    # * Funcion que envia un mensaje al servidor
    def enviar_mensaje_ssl(self, cliente, msg): 
        mensaje_bytes = msg.encode('utf-8')
        cliente.send(mensaje_bytes)
        
        
    def enviar_mensaje(self ,cliente , msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        cliente.send(send_length)
        cliente.send(message)
    

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

    def mostrar_mapa_terminal_rotado(self, cuadros):
        

        completado = True
        for j in range(len(cuadros)):
            for i in range(len(cuadros)):
                casilla = cuadros[i][j]
                if casilla == 0:
                    print('  .  ', end='')
                elif isinstance(casilla, tuple):
                    # Verificar si la casilla contiene un dron
                    if casilla[1] > 0:
                        # Mostrar solo el primer dron si hay varios
                        primer_dron = casilla[0][0]
                        estado = casilla[2]
                        if estado == 'green':
                            print(f'  \033[92m{primer_dron}G\033[0m  ', end='')  # Dron verde
                        else:
                            completado = False
                            print(f'  \033[91m{primer_dron}R\033[0m  ', end='')  # Dron rojo
                    else:
                        print('  .  ', end='')
                else:
                    print(f'  {casilla}  ', end='')
            print()

        if completado:
            print("\n¡Figura completada!\n")





        

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
            try:
                ADDR_eng = (SERVER_eng, PORT_eng)
                """
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(ADDR_eng)
                """
                
                #Practica 2
                context = ssl._create_unverified_context()
                with socket.create_connection(ADDR_eng) as sock:
                    with context.wrap_socket(sock,server_hostname=SERVER_eng)as ssock:
                    
                        print(f"Establecida conexión (engine) en [{ADDR_eng}]")          
                        message = f"{self.alias} {self.id} {self.token}"  
                            
                        
                        self.enviar_mensaje_ssl(ssock, message)
                        
                        
                        orden = ""
                        while orden == "":
                            print("1" , message) 
                            orden = self.receive_message_ssl(ssock)
                            print("2" , orden) 
                            orden_preparada = orden.split(" ")
                            
                            
                        
                        if orden == "Rechazado":
                            print("Conexión rechazada por el engine")
                            ssock.close()
                        elif orden_preparada[0] == "RUN":
                            pos_fin = Coordenada(int(orden_preparada[1]), int(orden_preparada[2]))
                            while self.color == "Rojo":
                                try:
                                    self.mover(pos_fin)
                                    self.enviar_mensaje_ssl(ssock, f"{self.posicion[0]} {self.posicion[1]}")
                                except (ConnectionResetError, ConnectionAbortedError):
                                    print("Conexión con el servidor perdida.")
                                    break
                            ssock.send("Vuelvo a base")
                        elif orden == "END":
                            ssock.close()
                            
                        
                        hecho=False
                        while True:
                            try:
                                hecho=self.recibir_motivo_vuelta("127.0.0.1", 9092, hecho)
                                if (self.recibir_destino("127.0.0.1", 9092,6,cliente)):
                                    break
                                mapa_actualizado_cuadros = self.recibir_mapa("127.0.0.1", 9092)
                                if mapa_actualizado_cuadros != self.mapa.cuadros:
                                    self.mapa.cuadros = mapa_actualizado_cuadros
                                    pos_vieja = self.coordenada
                                    
                                    self.mostrar_mapa_terminal_rotado(mapa_actualizado_cuadros)
                                    
                                    self.mover(self.destino)
                                    self.notificar_posicion("127.0.0.1", 9092, pos_vieja)
                                    print("Destino:", self.destino.x, ",", self.destino.y)
                                    print("Posicion:", self.coordenada.x, ",", self.coordenada.y)
                            except(ConnectionResetError, ConnectionAbortedError):
                                print("Conexión con el servidor perdida.")
                                break
            except Exception as e:
                print(f"No se ha podido establecer conexión (engine): {e}")
                       
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
    
            
            
            
            
        