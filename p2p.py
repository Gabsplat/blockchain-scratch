import socket
import threading
import json
import sys

class Node:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.peers = set()
        self.blockchain = []

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen()

        print(f"Nodo escuchando en {self.host}:{self.port}")

        while True:
            client, address = server.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client,))
            client_thread.start()

    def handle_client(self, client):
        while True:
            try:
                message = client.recv(1024).decode('utf-8')
                if message:
                    self.handle_message(json.loads(message))
            except:
                break
        client.close()

    def handle_message(self, message):
        if message['type'] == 'NEW_PEER':
            self.peers.add((message['host'], message['port']))
            print(f"Nuevo peer añadido: {message['host']}:{message['port']}")
        elif message['type'] == 'GET_PEERS':
            self.send_peers(message['host'], message['port'])

    def connect_to_peer(self, host, port):
        if (host, port) not in self.peers:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((host, port))
                self.send_message(client, {
                    'type': 'NEW_PEER',
                    'host': self.host,
                    'port': self.port
                })
                self.peers.add((host, port))
                print(f"Conectado a peer: {host}:{port}")
            except:
                print(f"No se pudo conectar a {host}:{port}")

    def send_message(self, client, message):
        client.send(json.dumps(message).encode('utf-8'))

    def send_peers(self, host, port):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))
        self.send_message(client, {
            'type': 'PEER_LIST',
            'peers': list(self.peers)
        })
        client.close()

    def broadcast(self, message):
        for peer in self.peers:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(peer)
                self.send_message(client, message)
                client.close()
            except:
                self.peers.remove(peer)
                print(f"Peer {peer} no disponible, eliminado de la lista")

# Ejemplo de uso
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python script.py <puerto>")
        sys.exit(1)

    my_port = int(sys.argv[1])
    all_ports = [5001, 5002, 5003, 5004]
    
    # Removemos nuestro propio puerto de la lista de puertos a los que nos conectaremos
    if my_port in all_ports:
        all_ports.remove(my_port)
    
    # Creamos el nodo
    node = Node("localhost", my_port)
    
    print(f"Iniciando nodo en el puerto {my_port}")
    
    # Iniciamos el nodo en un hilo separado
    node_thread = threading.Thread(target=node.start)
    node_thread.start()

    # Conectamos a los nodos semilla
    for port in all_ports:
        node.connect_to_peer("localhost", port)
    
    # Mantenemos el programa principal en ejecución
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Cerrando el nodo...")
        sys.exit(0)