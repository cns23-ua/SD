class Dron:
    def __init__(self, id, color, coordenada):
        self.id = id
        self.color = color
        self.coordenada = coordenada
        
    def mover(self, nueva_posicion):
        if self.puede_moverse_a(nueva_posicion):
            self.posicion = nueva_posicion
            self.estado = "Verde"  # Cambiar a estado final si ha llegado a la nueva posición
            
    def puede_moverse_a(self, nueva_posicion):
        # Verificar si la nueva posición es adyacente a la posición actual
        dx = abs(self.posicion[0] - nueva_posicion[0])
        dy = abs(self.posicion[1] - nueva_posicion[1])
        return (dx == 1 and dy == 0) or (dx == 0 and dy == 1) or (dx == 1 and dy == 1)