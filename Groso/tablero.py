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
        canvas_width = (filas * 30) + enumeration_width
        canvas_height = (columnas * 30) + enumeration_width
        self.canvas = tk.Canvas(root, width=canvas_width, height=canvas_height)
        self.canvas.pack()

        # Dibujar los cuadros en el lienzo y enumerar los cuadros en el margen superior e izquierdo
        for fila in range(filas):
            for columna in range(columnas):
                x0 = columna * 30 + enumeration_width  # Añade espacio para enumeración en el margen izquierdo
                y0 = fila * 30 + enumeration_width  # Añade espacio para enumeración en el margen superior
                x1 = x0 + 30
                y1 = y0 + 30
                cuadro = self.canvas.create_rectangle(x0, y0, x1, y1, fill="white", outline="black")
                self.cuadros[fila][columna] = cuadro

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
                    y_text = y0 - 15  # Coloca el número por encima del cuadro
                    self.canvas.create_text(x_text, y_text, text=str(numero), font=("Helvetica", 12))

    def dibujar_casilla(self, x, y, id, color):
        x0 = x * 30 + 40  # Ajusta las coordenadas al tamaño de las casillas y el margen
        y0 = (self.filas - y - 1) * 30 + 40  # Invierte las coordenadas en el eje y
        x1 = x0 + 30
        y1 = y0 + 30
        cuadro = self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="black")
        self.cuadros.append(cuadro)
        x_text = (x0 + x1) / 2
        y_text = (y0 + y1) / 2
        self.canvas.create_text(x_text, y_text, text=str(id), font=("Helvetica", 12))

    def siguiente_mov(self, pos_fin, pos_ini):
        x = [-1, 0, 1]
        y = [-1, 0, 1]
        ini = pos_ini
        anterior = 30.0
        resul = [0, 0]

        for i in x:
            for j in y:
                optima = [ini[0] + i, ini[1] + j]

                # Ajusta las coordenadas si salen del rango 1-20
                for k in range(2):
                    if optima[k] > 20:
                        optima[k] -= 20
                    if optima[k] < 1:
                        optima[k] += 20

                distancia = math.sqrt(((optima[0] - pos_fin[0]) ** 2) + ((optima[1] - pos_fin[1]) ** 2))

                if distancia < anterior:
                    print("x ", optima[0], "y ", optima[1], "valor ", distancia)
                    anterior = distancia
                    resul = optima

        return resul


if __name__ == "__main__":
    root = tk.Tk()
    tablero = Tablero(root, 20, 20)
    
    # Llama a la función dibujar_casilla con coordenadas x, y, ID y color   
  
    tablero.dibujar_casilla(2, 2, 2, "green")
    tablero.dibujar_casilla(3, 3, 3, "red")
    
    root.mainloop()