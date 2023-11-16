#!/bin/bash

# Cambia la ruta al directorio de Kafka
KAFKA_DIR="/kafka_2.13-3.6.0"

# Comando 1: Iniciar el servidor de ZooKeeper
gnome-terminal -- bash -c "cd $KAFKA_DIR && bin/zookeeper-server-start.sh config/zookeeper.properties"

#time.sleep(2)

# Comando 2: Iniciar el servidor de Kafka
gnome-terminal -- bash -c "cd $KAFKA_DIR && bin/kafka-server-start.sh config/server.properties"

sleep 2

#ELIMINAR TOPICS
gnome-terminal -- bash -c "cd $KAFKA_DIR && bin/kafka-topics.sh --bootstrap-server 127.0.0.1:9092 --delete --topic destinos_a_drones_topic"cl
