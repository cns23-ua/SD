import tkinter as tk
import math
from coordenada import *  # Asegúrate de importar la clase Coordenada desde el archivo adecuado
from collections import deque
import pdb
import time

class Tablero:
    def __init__(self, root, filas, columnas):
        self.root = root
        self.filas = filas
        self.columnas = columnas
        self.cuadros = [[None for _ in range(columnas)] for _ in range(filas)]

        # Tamaño de la enumeración
        enumeration_width = 40

        # Crear un lienzo (canvas) para el tablero con espacio adicional en la parte superior e izquierda
        canvas_width = (columnas * 30) + enumeration_width
        canvas_height = (filas * 30) + enumeration_width
        self.canvas = tk.Canvas(root, width=canvas_width, height=canvas_height)
        self.canvas.pack()

        # Dibujar los cuadros en el lienzo y enumerar los cuadros en el margen superior e izquierdo
        for fila in range(filas):
            for columna in range(columnas):
                x0 = columna * 30 + enumeration_width  # Añade espacio para enumeración en el margen izquierdo
                y0 = (filas - fila - 1) * 30 + enumeration_width  # Invierte el orden de las filas
                x1 = x0 + 30
                y1 = y0 + 30
                cuadro = self.canvas.create_rectangle(x0, y0, x1, y1, fill="white", outline="black")
                self.cuadros[fila][columna] = 0

                # Enumerar los cuadros en el margen izquierdo
                if columna == 0:
                    numero = filas - fila
                    x_text = x0 - 15  # Coloca el número a la izquierda del cuadro
                    y_text = (y0 + y1) / 2
                    self.canvas.create_text(x_text, y_text, text=str(numero), font=("Helvetica", 12))

                # Enumerar los cuadros en el margen superior
                if fila == 0:
                    numero = columna + 1
                    x_text = (x0 + x1) / 2
                    y_text = enumeration_width - 15  # Coloca el número encima del cuadro
                    self.canvas.create_text(x_text, y_text, text=str(numero), font=("Helvetica", 12))

    def dibujar_casilla(self, x, y, id, color):
        x0 = x * 30 + 40
        y0 = y * 30 + 40
        x1 = x0 + 30
        y1 = y0 + 30
        cuadro = self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="black")
        self.cuadros.append(cuadro)
        x_text = (x0 + x1) / 2
        y_text = (y0 + y1) / 2
        self.canvas.create_text(x_text, y_text, text=str(id), font=("Helvetica", 12))
        
    def dibujar_casilla_sinId(self, x, y, color):
        x0 = x * 30 + 40
        y0 = y * 30 + 40
        x1 = x0 + 30
        y1 = y0 + 30
        cuadro = self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="black")
        self.cuadros.append(cuadro)

    def mover_contenido(self, id, pos_origen, pos_destino, color):
        
        # Borramos el contenido del cuadro de origen teniendo en cuenta
        # todo, que tanto que en el cuadro anterior hubiera varios drones
        # o ninguno
        if (self.cuadros[pos_origen[0]-1][pos_origen[1]-1][1]==1 and 
            id in self.cuadros[pos_origen[0]-1][pos_origen[1]-1][0]):
            self.cuadros[pos_origen[0]-1][pos_origen[1]-1] = 0
            #Pasamos el dron indicado de la posición anterior a la que queremos
            self.introducir_en_posicion(pos_destino[0], pos_destino[1], ([id],1,color))
        elif(self.cuadros[pos_origen[0]-1][pos_origen[1]-1][1]>1 and 
            id in self.cuadros[pos_origen[0]-1][pos_origen[1]-1][0]):
            ids=[]
            for identificador in self.cuadros[pos_origen[0]-1][pos_origen[1]-1][0]:
                if identificador != id:
                    ids.append(identificador)
                    
            vieja = (ids, self.cuadros[pos_origen[0]-1][pos_origen[1]-1][1]-1, color)
            self.cuadros[pos_origen[0]-1][pos_origen[1]-1] = vieja

            #Pasamos el dron indicado de la posición anterior a la que queremos
            self.introducir_en_posicion(pos_destino[0], pos_destino[1], ([id],1,color))
            
    def introducir_en_posicion(self, x, y, objeto):
        x = x-1
        y = y-1
        elemento=self.cuadros[x][y]
        
        if(elemento==0):
            self.cuadros[x][y]=objeto
        else:
            nueva = (elemento[0]+objeto[0], elemento[1]+1, objeto[2])
            self.cuadros[x][y] = nueva

             
    def cerrar_ventana(self):
        self.root.destroy() 
        
    def dibujar_tablero(self):
        for fila in range(self.filas):
            for columna in range(self.columnas):
                contenido=self.cuadros[fila][columna]
                if(contenido!=0):                    
                    self.dibujar_casilla(fila, columna, contenido[0][len(contenido[0])-1], contenido[2])
        self.root.after(1000,self.cerrar_ventana)
        self.root.mainloop()
                
    def estado_final(self, x, y):
        x=x-1
        y=y-1
        tupla_nueva=(self.cuadros[x][y][0],self.cuadros[x][y][1],"Verde")
        self.cuadros[x][y]=tupla_nueva
        
    def mostrar_mensaje(self, mensaje):
        x0 = 40  # Margen izquierdo
        y0 = 10  # Margen superior
        x1 = self.canvas.winfo_reqwidth() - 40  # Ancho del canvas - margen derecho
        y1 = 30  # Altura del área del mensaje

        # Crear un área para mostrar el mensaje
        self.canvas.create_rectangle(x0, y0, x1, y1, fill="lightgray", outline="black")
        
        # Mostrar el mensaje en el área creada
        x_text = (x0 + x1) / 2
        y_text = (y0 + y1) / 2
        self.canvas.create_text(x_text, y_text, text=mensaje, font=("Helvetica", 12, "bold"))
        
    


    
   
