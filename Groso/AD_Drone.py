from coordenada import *
import socket
import sys
import math

HEADER = 64
FORMAT = 'utf-8'

class Dron:
    
    # *Constructor
    def __init__(self):
        self.id = 0
        self.alias = ""
        self.color = "Rojo"
        self.coordenada = Coordenada(1,1)
        self.token = ""
        self.destino = None
        self.mapa = None
        
    # *Movemos el dron dónde le corresponde y verificamos si ha llegado a la posición destino
    def mover(self, destino):
        self.posicion = self.siguiente_mov(destino)
        if (self.posicion[0]==destino[0] and self.posicion[1]==destino[1]):
            self.estado = "Verde"  # Cambiar a estado final si ha llegado a la nueva posición
    
    #Recibimos destino del engine
    def recibir_destino(self, destino):
        self.destino=destino
        
    #Recibimos tablero del engine
    def recibir_mapa(self, mapa):
        self.mapa=mapa
        
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
    
    # * Funcion que transmite la posición al servidor
    def enviar_mensaje(self, cliente, msg): 
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        cliente.send(send_length)
        cliente.send(message)
    
        
    # *Función que comunica con el servidor(engine) y hace lo que le mande
    def conectar_engine(self, server, port):              
        #Establece conexión con el servidor (engine)
        try:
            ADDR = (server, port)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(ADDR)
            print (f"Establecida conexión (engine) en [{ADDR}]")
            
            #Una vez establecida la conexión 
            orden = "vacio"  
            while  orden != "END":
                print("Recibo del Servidor: ", client.recv(2048).decode(FORMAT))
                orden=input()
                orden_preparada=orden.split(" ")
                if (orden[0]=="RUN"):
                    pos_fin = Coordenada(int(orden_preparada[1]),int(orden_preparada[2]))
                    while (self.estado=="Verde"):
                        self.mover(pos_fin)
                        self.enviar_mensaje(client, self.posicion[0] + " " + self.posicion[1])
                print("Vuelvo a base")
                client.send("Vuelvo a base")
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
            print("No se ha podido establecer conexión(engine)")
        
        return client

    # *Menú del dron para interactuar con registry
    def menu(self, server_reg, port_reg, cliente):
        token=""
        opc = 0
        while(opc>4 or opc<1):
            print("\nHola, soy un dron, qué operación desea realizar?")
            print("[1] Dar de alta")
            print("[2] Editar perfil")
            print("[3] Dar de baja")
            print("[4] Desconectar")
            opc=int(input())
            if(opc<1 or opc>4):
                print("Opción no válida, inténtelo de nuevo")
                
            
        
        if (opc==1):
                alias = ""
                print("\nIntroduce mi alias")
                alias = input()
                #Hasta aquí hemos recopilado los datos y vamos a conectarnos al registry
                message = f"{opc} {alias}"
                self.enviar_mensaje(cliente, message)
                #Hemos enviado los datos y esperamos respuesta con nuestro token               
                while (token==""):
                    long = cliente.recv(HEADER).decode(FORMAT)
                    if long:
                        long = int(long)
                        token = cliente.recv(long).decode(FORMAT)
                        print(token)    
                                               
                token_manejable=token.split(" ")
                #si nuestro token empieza con tkn hemos podido registrarnos, si no no y volvemos a introducir datos
            
                self.token=token_manejable[1]
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
                        
        elif (opc==4):
            sys.exit(1)
            cliente.close()
        dron.menu(SERVER,PORT, cliente_reg)
            
            
if (len(sys.argv) == 3):
    SERVER = sys.argv[1]
    PORT = int(sys.argv[2])
    ADDR = (SERVER, PORT)
    
    dron = Dron()
    
    cliente_reg = dron.conectar_registri(SERVER,PORT)
    dron.menu(SERVER,PORT, cliente_reg)
    