import tkinter as tk

def crear_tablero(filas, columnas):
    tablero = [[None for _ in range(columnas)] for _ in range(filas)]
    
    for fila in range(filas):
        for columna in range(columnas):
            casilla = tk.Label(ventana, width=3, height=1, relief="ridge", bd=1, bg="white")
            casilla.grid(row=fila, column=columna)
            tablero[fila][columna] = casilla
    
    return tablero

def cambiar_color(tablero, fila, columna, color, numero):
    tablero[fila][columna].configure(bg=color)
    tablero[fila][columna].config(text=numero)

filas = 20
columnas = 20

# Crear una ventana
ventana = tk.Tk()
ventana.title("Tablero Gráfico")

tablero = crear_tablero(filas, columnas)

# Cambiar el color y el número de una casilla
cambiar_color(tablero, 5, 10, "red", "6")
cambiar_color(tablero, 10, 15, "red", "7")

ventana.mainloop()
