import datetime
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
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import threading
from datetime import datetime

# Desactivar las advertencias de solicitud no segura debido a certificados autofirmados
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


HEADER = 64
FORMAT = 'utf-8'

class Dron:
    
    # *Constructor
    def __init__(self):
        self.id = 1
        self.alias = "alias"
        self.color = "Rojo"
        self.coordenada = Coordenada(1,1)
        self.token = "token"
        self.destino = ""
        self.mapa = Tablero(tk.Tk(),20,20)
        self.url_api = "https://localhost:3000"
        self.url_api_eng = "https://localhost:3001"
        
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
                    print("Mi posicion no es valida me voy del espectaculo")
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
    
        
    def borrar_token_en_20s(self):
        time.sleep(20)  
        self.borrar_token_api()
        
    # *Función que comunica con el servidor(engine) y hace lo que le mande
    def conectar_verify_engine(self, SERVER_eng, PORT_eng):   
        self.generar_token_api()
        # Generamos la token y iniciamos el tiempo de la autodestrucción
        thread = threading.Thread(target=self.borrar_token_en_20s)
        thread.start()
        
        try:
            ADDR_eng = (SERVER_eng, PORT_eng)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR_eng)
        
            print(f"Establecida conexión (engine) en [{ADDR_eng}]")          
            message = f"{self.alias} {self.id} {self.token}"      
            self.enviar_mensaje(client, message)
            
            orden = ""
            while orden == "":
                orden = self.receive_message(client)
                orden_preparada = orden.split(" ")
                
            if orden == "Rechazado":
                print("Conexión rechazada por el engine")
                client.close()
            else:
                self.borrar_token_api()
                return client
        except Exception as e:
            print(f"No se ha podido establecer conexión (engine): {e}")
            if 'client' in locals():
                client.close()
    
    def conectar_verify_engine_API(self, SERVER_eng, PORT_eng):   
        self.generar_token_api()
        # Generamos la token y iniciamos el tiempo de la autodestrucción
        thread = threading.Thread(target=self.borrar_token_en_20s)
        thread.start()
        resultado = ""
        try:
            url = f"{self.url_api_eng}/verificar_dron"  # Reemplaza con la URL correcta de tu API

            # Define el cuerpo de la solicitud con el token
            payload = {'token': self.token}

            try:
                response = requests.post(url, json=payload, verify=False)
                if response.status_code == 200:
                    resultado = "Exito"
                else:
                    print(f"Error al verificar el token. Código de estado: {response.status_code}")
                    return None
            except requests.RequestException as e:
                print(f"Error de conexión: {e}")
                return None
                    
            if resultado == "Exito":
                ADDR_eng = (SERVER_eng, PORT_eng)
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(ADDR_eng)
            
                print(f"Establecida conexión (engine) en [{ADDR_eng}]")          
                message = f"{self.alias} {self.id} API"     
                print(message) 
                self.enviar_mensaje(client, message)
                
                orden = ""
                while orden == "":
                    orden = self.receive_message(client)
                    orden_preparada = orden.split(" ")
                    
                if orden == "Rechazado":
                    print("Conexión rechazada por el engine")
                    client.close()
                else:
                    self.borrar_token_api()
                    return client
        except Exception as e:
            print(f"No se ha podido establecer conexión (engine): {e}")
            if 'client' in locals():
                client.close()
    
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



    def menu(self, server_reg, port_reg, cliente , SERVER_eng , PORT_eng):
        print("Bienvenido al menú:")
        print("1. Registro Clásico")
        print("2. API")
        print("3. Salir")
        opcion = int(sys.stdin.readline())

        if opcion == 1:
            print("Has seleccionado Registro Clásico")
            self.menu_clasico(server_reg, port_reg, cliente , SERVER_eng , PORT_eng)
        elif opcion == 2:
            print("Has seleccionado API")
            self.menu_nuevo(server_reg, port_reg, cliente , SERVER_eng , PORT_eng)
        elif opcion == 3:
            sys.exit(1)
        else:
            print("Opción inválida. Por favor, elige 1 o 2.")


    # *Menú del dron para interactuar con registry
    def menu_clasico(self, server_reg, port_reg, cliente , SERVER_eng , PORT_eng):
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
                print("token manejable ", token_manejable)
                self.alias=token_manejable[0]
                self.id=int(token_manejable[1])

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
                opt = 0
                while(opt != 1 and opt != 2):
                    print("Por donde deseas verificarte en el engine?")
                    print("1.Via sokets")
                    print("2.Via API")
                    opt = int(sys.stdin.readline())
                    if opt == 1:
                        cliente = self.conectar_verify_engine(SERVER_eng, PORT_eng)
                    elif opt == 2:
                        cliente = self.conectar_verify_engine_API(SERVER_eng, PORT_eng)
                    else: 
                        print("Opción no válida, inténtalo de nuevo.")
                cont=0
                hecho=False
                while True:
                    try:
                        hecho=self.recibir_motivo_vuelta("127.0.0.1", 9092, hecho)
                        if (self.recibir_destino("127.0.0.1", 9092,6,cliente)):
                            break
                        mapa_actualizado_cuadros = self.recibir_mapa("127.0.0.1", 9092)
                        if cont == 0:
                            self.actualizar_logs_json("He conectado con registry y engine exitosamente.")
                            self.actualizar_logs_json("Empezamos el espectáculo")
                            cont = cont+1
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
        if(opc!=5):
            self.menu(SERVER,PORT, port_reg , SERVER_eng , PORT_eng)
            
    def listar_drones_api(self):
        url = f"{self.url_api}/listar_drones"  # Reemplaza 'URL_DE_TU_API' con la URL correcta de tu API
        
        try:
            response = requests.get(url, verify=False)
            if response.status_code == 200:
                drones = response.json()
                return drones  # Devolver los datos de los drones
            else:
                print("Error al obtener la lista de drones.")
                return {}  # Devolver un diccionario vacío en caso de error
        except requests.RequestException as e:
            print(f"Error de conexión: {e}")
            return {}  # Devolver un diccionario vacío en caso de error
            
    def agregar_dron_api(self, alias):
        drones = self.listar_drones_api()
        if drones != None:
            # Verificar si el alias ya existe en la lista de drones
            for dron in drones:
                if dron.get('alias') == str(alias).strip():
                    print("Ya hay un dron que tiene este alias")
                    return
        
        # Si el alias no existe, realizar la solicitud para agregar el dron
        url = f"{self.url_api}/agregar_dron"  # Reemplaza 'URL_DE_TU_API' con la URL correcta de tu API
        data = {"alias": str(alias).strip()}

        try:
            response = requests.post(url, json=data, verify=False)
            if response.status_code == 201:
                print(f"Dron con alias '{str(alias).strip()}' agregado correctamente.")
                # Obtener el ID asignado al dron recién agregado y guardar en self.id
                 # Asignar el ID del dron recién agregado a self.id si la respuesta contiene el ID
                drones = self.listar_drones_api()
                for dron in drones:
                    if dron.get('alias') == str(alias).strip():
                        self.alias = alias
                        self.id = int(dron.get('id'))
                        print(f"ID asignado al dron '{alias.strip()}': {self.id}")
            else:
                print(f"Error al agregar el dron. Código de estado: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error de conexión: {e}")
            
    def modificar_dron_api(self):
        drones = self.listar_drones_api()
        dentro = False
        # Verificar si el alias existe en la lista de drones
        if drones != None:
            # Verificar si el alias ya existe en la lista de drones
            for dron in drones:
                if dron.get('alias') == self.alias.strip():
                    dentro = True
                    # Realizar la solicitud para modificar el dron
                    url = f"{self.url_api}/modificar_dron/{self.id}"
                    print("Introduce el nuevo alias que quieres que tenga")
                    nuevo_alias = sys.stdin.readline()
                    data = {'alias': str(nuevo_alias.strip())}

                    try:
                        response = requests.put(url, json=data, verify=False)
                        if response.status_code == 200:
                            self.alias=nuevo_alias
                            print(f"Alias modificado correctamente. Nuevo alias: '{nuevo_alias.strip()}'")
                        else:
                            print(f"Error al modificar el dron. Código de estado: {response.status_code}")
                    except requests.RequestException as e:
                        print(f"Error de conexión: {e}")
        if dentro == False:
            print("Este dron no está registrado")
        
    def borrar_dron_api(self, alias):
        url = f"{self.url_api}/borrar_dron/{self.id}"  # Reemplaza 'URL_DE_TU_API' con la URL correcta de tu API

        try:
            response = requests.delete(url, verify=False)
            if response.status_code == 200:
                print(f"Dron con alias '{alias.strip()}' eliminado correctamente")
            elif response.status_code == 404:
                print(f"No se encontró el dron con el id '{self.id}'")
            else:
                print(f"Error al intentar eliminar el dron. Código de estado: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error de conexión: {e}")
            
    def generar_token_api(self):
        dentro=False
        drones = self.listar_drones_api()
        # Verificar si el alias existe en la lista de drones
        if drones != None:
            # Verificar si el alias ya existe en la lista de drones
            for dron in drones:
                if dron.get('alias').strip() == self.alias.strip():
                    dentro=True
                    url = f"{self.url_api}/generar_token/{self.alias.strip()}"  # Ruta para generar token, reemplaza 'URL_DE_TU_API'
                    try:
                        response = requests.put(url, verify=False)  # Realizar solicitud PUT para generar el token
                        if response.status_code == 200:
                            token_data = response.json()
                            token = token_data.get('drone', {}).get('token')
                            if token:
                                self.token = token  # Devolver el token generado
                            else:
                                print("No se pudo obtener el token.")
                                return 
                        else:
                            print(f"Error al generar el token. Código de estado: {response.status_code}")
                            return None
                    except requests.RequestException as e:
                        print(f"Error de conexión: {e}")
                        return None
        if dentro == False:
            print("Este dron no está registrado")
                    
    def borrar_token_api(self):
        drones = self.listar_drones_api()
        dentro = False
        # Verificar si el alias existe en la lista de drones
        if drones is not None:
            # Verificar si el alias existe en la lista de drones
            for dron in drones:
                if dron.get('alias').strip() == self.alias.strip():
                    dentro = True
                    url = f"{self.url_api}/borrar_token/{self.alias.strip()}"  # Ruta para borrar token, reemplaza 'URL_DE_TU_API'
                    try:
                        response = requests.put(url, verify=False)  # Realizar solicitud PUT para borrar el token
                        if response.status_code == 200:
                            print(f"Token del dron '{self.alias.strip()}' eliminado correctamente.")
                            self.token=""
                        elif response.status_code == 404:
                            print(f"No se encontró el dron con el alias '{self.alias.strip()}'")
                        else:
                            print(f"Error al intentar eliminar el token. Código de estado: {response.status_code}")
                    except requests.RequestException as e:
                        print(f"Error de conexión: {e}")
                        return 
        if dentro == False:
            print("Este dron no está registrado.")
            
            
    def actualizar_logs_json(self, newlog):
        # Hacer una solicitud a la API para agregar el log
        url_api = url = f"{self.url_api_eng}/agregar_log"  # Reemplaza con la URL de tu API
        headers = {'Content-Type': 'application/json'}

        # Realizar la solicitud POST a la API
        try:
            response = requests.post(url_api, verify=False, headers=headers, json={'nuevoLog': f"[{self.obtener_ip()}] [{self.obtener_fecha_hora()}] {newlog}"})
            response.raise_for_status()  # Verificar si la solicitud fue exitosa
            print("Log agregado a la API correctamente")
        except requests.exceptions.RequestException as e:
            print(f"Error al agregar el log a la API: {e}")
        
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
        
                
    # *Menú del dron para interactuar con registry
    def menu_nuevo(self, server_reg, port_reg, cliente , SERVER_eng , PORT_eng):
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
            self.agregar_dron_api(alias)        
    
        elif (opc==2):      
            self.modificar_dron_api()
                       
        elif (opc==3):
           self.borrar_dron_api(self.alias)
                        
        elif (opc==5):
            cliente.close()
            sys.exit(1)

        elif (opc==4):
                opt = 0
                while(opt != 1 and opt != 2):
                    print("Por donde deseas verificarte en el engine?")
                    print("1.Via sokets")
                    print("2.Via API")
                    opt = int(sys.stdin.readline())
                    if opt == 1:
                        cliente = self.conectar_verify_engine(SERVER_eng, PORT_eng)
                    elif opt == 2:
                        cliente = self.conectar_verify_engine_API(SERVER_eng, PORT_eng)
                    else: 
                        print("Opción no válida, inténtalo de nuevo.")
                cont=0
                hecho=False
                while True:
                    try:
                        hecho=self.recibir_motivo_vuelta("127.0.0.1", 9092, hecho)
                        if (self.recibir_destino("127.0.0.1", 9092,6,cliente)):
                            break
                        mapa_actualizado_cuadros = self.recibir_mapa("127.0.0.1", 9092)
                        if cont == 0:
                            print("me estoy metiendo")
                            self.actualizar_logs_json("He conectado con registry y engine exitosamente.")
                            self.actualizar_logs_json("Empezamos el espectáculo")
                            cont = cont+1
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
    
            
            
            
            
        