#!/bin/bash

letra='A'

for i in {1..5}; do
    # Ejecutar el script del dron en una nueva terminal con la opción -- bash
    gnome-terminal -- python3 AD_Drone.py 127.0.0.3 5051 127.0.0.2 5050 --title="Dron $i" -- bash

    # Esperar un poco antes de pasar a la siguiente iteración
    sleep 2

    # Enviar '1' seguido de Enter a la terminal actual
    gnome-terminal --title="Dron $i" -- bash -c 'echo "1" && read -p "Presiona Enter"'

    # Esperar un poco antes de pasar a la siguiente iteración
    sleep 2

    # Enviar la letra actual seguido de Enter a la terminal actual
    gnome-terminal --title="Dron $i" -- bash -c 'echo "$letra" && read -p "Presiona Enter"'

    # Incrementar la letra para la próxima iteración
    letra=$(echo "$letra" | tr "A-Y" "B-Z")

    # Esperar un poco antes de pasar a la siguiente iteración
    sleep 2
done

