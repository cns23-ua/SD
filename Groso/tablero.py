import tkinter as tk
import math
from coordenada import *  # Asegúrate de importar la clase Coordenada desde el archivo adecuado
from collections import deque
import pdb

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
        x = x -1
        y = y -1
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
        x = x -1
        y = y -1
        x0 = x * 30 + 40
        y0 = y * 30 + 40
        x1 = x0 + 30
        y1 = y0 + 30
        cuadro = self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="black")
        self.cuadros.append(cuadro)

    def mover_contenido(self, pos_origen, pos_destino):
        cuadro = self.cuadros[pos_origen[0]-1][pos_origen[1]-1]
        print("Cuadro: " + str(cuadro))
        # Borra el contenido del cuadro de origen
        self.cuadros[pos_origen[0]-1][pos_origen[1]-1] = 0

        # Copia el cuadro a la nueva posición
        self.cuadros[pos_destino[0]-1][pos_destino[1]-1] = cuadro
            
    def introducir_en_posicion(self, x, y, objeto):
        x = x -1
        y = y -1
        elemento=self.cuadros[x][y]
        
        if(elemento==0):
            elemento=objeto
        else:
            elemento[0] = elemento[0] + objeto[0]
            elemento[1] = elemento[1] + 1
            elemento[2] = elemento[2] + objeto[2]

    def dibujar_tablero(self):
        for fila in range(self.filas):
            for columna in range(self.columnas):
                contenido=self.cuadros[fila][columna]
                if(contenido!=0):
                    for color in contenido[2]:
                        pintura="green"
                        if(color=="Rojo"):
                            pintura="red"
                            break
                    self.dibujar_casilla_sinId(fila, columna, pintura)
                

if __name__ == "__main__":
    root = tk.Tk()
    tablero = Tablero(root, 20, 20)
    
    # Llama a la función dibujar_casilla con coordenadas x, y, ID y color   
  
    tablero.cuadros[7][7]=([1,2,3],3,["Verde"])
    tablero.cuadros[4][4]=([1,2,3],3,["Rojo", "Verde"])
    

    
    tablero.dibujar_tablero()
    
    root.mainloop()