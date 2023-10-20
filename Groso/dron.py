from coordenada import *
import socket
import sys
import math

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'

class Dron:
    
    # *Constructor
    def __init__(self):
        self.id = 0
        self.alias = ""
        self.color = "Rojo"
        self.coordenada = Coordenada(1,1)
        self.token = ""
        
    # *Movemos el dron dónde le corresponde y verificamos si ha llegado a la posición destino
    def mover(self, pos_fin):
        self.posicion = self.siguiente_mov(pos_fin)
        if (self.posicion[0]==pos_fin[0] and self.posicion[1]==pos_fin[1]):
            self.estado = "Verde"  # Cambiar a estado final si ha llegado a la nueva posición
    
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
    
    # * Funcion que transmite un mensaje al servidor
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
        
        opc = 0
        while(opc>4 or opc<1):
            print("Hola, soy un dron, qué operación desea realizar?")
            print("[1] Dar de alta")
            print("[2] Editar perfil")
            print("[3] Dar de baja")
            print("[4] Desconectar")
            opc=int(input())
            if(opc<1 or opc>4):
                print("Opción no válida, inténtelo de nuevo")
        
        if (opc==1):
            exito = False
            while(exito==False):
                alias = ""
                print("Vamos a registrarme")
                print("Introduce mi alias")
                alias = input()
                #Hasta aquí hemos recopilado los datos y vamos a conectarnos al registry
                self.enviar_mensaje(cliente, alias)
                #Hemos enviado los datos y esperamos respuesta con nuestro token
                while (token==""): # !Arreglar esta parte y hacer lo mismo en edit
                    long = cliente.recv(HEADER).decode(FORMAT)
                    if long:
                        long = int(long)
                        token = cliente.recv(long).decode(FORMAT)
                        print(token)    
                token_manejable=token.split(" ")
                #si nuestro token empieza con tkn hemos podido registrarnos, si no no y volvemos a introducir datos
                if(token_manejable[0]=="tkn"):
                    self.token=token_manejable[1]
                    print("Ya tengo mi token y estoy dado de alta")
                    exito=True
                    cliente.close()
                else:
                    print("No puedes registrarte con estos credenciales, inténtalo de nuevo")
        elif (opc==2):
            exito = False
            while(exito==False):
                print("Introduce mi alias nuevo")
                alias = input()
                #Hasta aquí hemos recopilado los datos y vamos a conectarnos al registry
                self.enviar_mensaje(cliente, alias)
                #Hemos enviado los datos y esperamos respuesta de si podemos editar
                editado = True # !Dejarlo cómo arriba
                while (editado == False):
                    print("Recibo del Servidor: ", cliente.recv(HEADER).decode(FORMAT))
                    edit=cliente.recv(HEADER).decode(FORMAT)
                    if(edit == "ok"):
                        editado=True
                        exito=True
                        self.alias=alias
                        print("Sus credenciales han sido modificadas con éxito")
                        cliente.close()
                    elif(edit == "Not exist"):
                        exito=True
                        editado=True
                        print("No hay registros en la base de datos, pruebe a registrarse")
                        cliente.close()
        elif (opc==3):
            exito = False
            while(exito==False):
                #Conectamos con registri
                self.enviar_mensaje(cliente, self.id + "" + self.alias)
                #Hemos enviado los datos y esperamos respuesta de si hemos dado de baja
                baja = True
                while (baja == False):
                    print("Recibo del Servidor: ", cliente.recv(2048).decode(FORMAT))
                    baja=input()
                    if(baja == "ok"):
                        baja=True
                        exito=True
                        print("Se ha dado de baja con éxito")
                        cliente.close()
                    else:
                        exito=True
                        baja=True
                        print("Algo ha fallado, pruebe de nuevo más tarde")
                        cliente.close()
        elif (opc==4):
            sys.exit(1)
            
#Prueba :

if (len(sys.argv) == 3):
    SERVER = sys.argv[1]
    PORT = int(sys.argv[2])
    ADDR = (SERVER, PORT)
    
    dron = Dron()
    
    cliente_reg = dron.conectar_registri(SERVER,PORT)
    dron.menu(SERVER,PORT, cliente_reg)
