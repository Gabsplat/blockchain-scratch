import socket
import threading
import json
import sys
from blockchain import Blockchain, Block, Transaction

print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

class Node:
    def __init__(self, host, port, db_path='blockchain.db'):
        self.host = host
        self.port = port
        self.node_id = str(port)
        self.peers = set()
        self.blockchain = Blockchain(db_path=db_path)
        self.received_transactions = set()
        self.received_blocks = set()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen()

        safe_print(f"Nodo escuchando en {self.host}:{self.port}")

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
            safe_print(f"Nuevo peer añadido: {message['host']}:{message['port']}")
            self.send_chain(message['host'], message['port'])
            self.send_pending_transactions(message['host'], message['port'])
        elif message['type'] == 'GET_PEERS':
            self.send_peers(message['host'], message['port'])
        elif message['type'] == 'NEW_BLOCK':
            new_block = Block.from_dict(message)
            if new_block.hash == new_block.calculate_hash() and new_block.previous_hash == self.blockchain.get_latest_block().hash:
                if self.blockchain.add_block(new_block.transactions):
                    safe_print(f"Nuevo bloque añadido a la cadena: {new_block.hash}")
                else:
                    safe_print("Error al añadir el nuevo bloque a la cadena")
            else:
                safe_print("El bloque recibido es inválido")
        elif message['type'] == 'CHAIN':
            new_chain = [Block.from_dict(block) for block in message['chain']]
            if self.blockchain.replace_chain(new_chain):
                safe_print("Cadena reemplazada con la cadena recibida.")
        elif message['type'] == 'NEW_TRANSACTION':
            transaction_data = json.dumps(message['transaction'])
            if transaction_data not in self.received_transactions:
                self.received_transactions.add(transaction_data)
                transaction = Transaction.from_dict(message['transaction'])
                if self.blockchain.add_transaction(transaction.sender, transaction.recipient, transaction.amount):
                    self.broadcast_transaction(transaction)
        elif message['type'] == 'PENDING_TRANSACTIONS':
            pending_transactions = [Transaction.from_dict(tx) for tx in message['transactions']]
            self.blockchain.pending_transactions.extend(pending_transactions)

    def connect_to_peer(self, host, port):
        if (host, port) not in self.peers:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(5)  # Timeout de 5 segundos para evitar conexiones colgantes
                client.connect((host, port))
                self.send_message(client, {
                    'type': 'NEW_PEER',
                    'host': self.host,
                    'port': self.port
                })
                self.peers.add((host, port))
                safe_print(f"Conectado al peer: {host}:{port}")
            except socket.timeout:
                safe_print(f"Conexión a {host}:{port} agotada")
            except Exception as e:
                safe_print(f"No se pudo conectar a {host}:{port}: {e}")

    def send_message(self, client, message):
        client.send(json.dumps(message).encode('utf-8'))

    def send_peers(self, host, port):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5)
        try:
            client.connect((host, port))
            self.send_message(client, {
                'type': 'PEER_LIST',
                'peers': list(self.peers)
            })
        except socket.timeout:
            safe_print(f"Conexión a {host}:{port} agotada")
        except Exception as e:
            safe_print(f"No se pudieron enviar los peers a {host}:{port}: {e}")
        finally:
            client.close()

    def broadcast_chain(self):
        chain_data = {
            'type': 'CHAIN',
            'chain': [block.to_dict() for block in self.blockchain.chain]
        }
        self.broadcast(chain_data) 
        

    def send_chain(self, host, port):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5)
        try:
            client.connect((host, port))
            chain_data = {
                'type': 'CHAIN',
                'chain': [block.to_dict() for block in self.blockchain.chain]
            }
            self.send_message(client, chain_data)
        except socket.timeout:
            safe_print(f"Conexión a {host}:{port} agotada")
        except Exception as e:
            safe_print(f"No se pudo enviar la cadena a {host}:{port}: {e}")
        finally:
            client.close()

    def send_pending_transactions(self, host, port):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5)
        try:
            client.connect((host, port))
            pending_transactions_data = {
                'type': 'PENDING_TRANSACTIONS',
                'transactions': [tx.to_dict() for tx in self.blockchain.pending_transactions]
            }
            self.send_message(client, pending_transactions_data)
        except socket.timeout:
            safe_print(f"Conexión a {host}:{port} agotada")
        except Exception as e:
            safe_print(f"No se pudieron enviar las transacciones pendientes a {host}:{port}: {e}")
        finally:
            client.close()

    def broadcast_block(self, block):
        block_data = block.to_dict()
        block_data['type'] = 'NEW_BLOCK'
        self.broadcast(block_data)

    def broadcast(self, message):
        peers_copy = list(self.peers)
        for peer in peers_copy:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(5)  # Timeout to avoid hanging connections
                client.connect(peer)
                self.send_message(client, message)
                client.close()
            except socket.timeout:
                safe_print(f"Conexión a {peer} agotada")
            except Exception as e:
                self.peers.remove(peer)
                safe_print(f"Peer {peer} no disponible, eliminado de la lista: {e}")

    def broadcast_transaction(self, transaction):
        transaction_data = {
            'type': 'NEW_TRANSACTION',
            'transaction': transaction.to_dict()
        }
        self.broadcast(transaction_data)

    def get_balance(self):
        return self.blockchain.get_balance(self.node_id)
    
    def start_mining(self):
        new_block = self.blockchain.mine_pending_transactions()
        if new_block:
            self.broadcast_chain()  # Broadcast the entire chain after mining
            self.broadcast_block(new_block)  # Broadcast the new block after mining

# Usage example
if __name__ == "__main__":
    if len(sys.argv) != 2:
        safe_print("Uso: python p2p.py <puerto>")
        sys.exit(1)

    my_port = int(sys.argv[1])
    all_ports = [5001, 5002, 5003, 5004]
    
    if my_port in all_ports:
        all_ports.remove(my_port)
    
    node = Node("localhost", my_port)
    
    safe_print(f"Iniciando nodo en el puerto {my_port}")
    
    node_thread = threading.Thread(target=node.start)
    node_thread.start()

    for port in all_ports:
        node.connect_to_peer("localhost", port)
        
    try:
        while True:
            action = input("Ingrese 't' para añadir una transacción, 'm' para minar transacciones pendientes, o 'b' para verificar el saldo: ").strip().lower()
            if action == 't':
                recipient = input("Ingrese el puerto del destinatario: ").strip()
                amount = float(input("Ingrese la cantidad: ").strip())
                if node.blockchain.add_transaction(node.node_id, recipient, amount):
                    transaction = Transaction(node.node_id, recipient, amount)
                    node.broadcast_transaction(transaction)
            elif action == 'm':
                node.start_mining()  # Call the mining method which will also broadcast the block    
            elif action == 'b':
                safe_print(f"Saldo actual: {node.get_balance()}")
    except KeyboardInterrupt:
        safe_print("Apagando nodo...")
        sys.exit(0)