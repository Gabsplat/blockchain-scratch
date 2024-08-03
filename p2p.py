import socket
import threading
import json
import sys
from blockchain import Blockchain, Block, Transaction

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

        print(f"Node listening on {self.host}:{self.port}")

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
            print(f"New peer added: {message['host']}:{message['port']}")
            self.send_chain(message['host'], message['port'])
            self.send_pending_transactions(message['host'], message['port'])
        elif message['type'] == 'GET_PEERS':
            self.send_peers(message['host'], message['port'])
        elif message['type'] == 'NEW_BLOCK':
            block_data = json.dumps(message)
            if block_data not in self.received_blocks:
                self.received_blocks.add(block_data)
                new_block = Block.from_dict(message)
                if new_block.hash == new_block.calculate_hash() and new_block.previous_hash == self.blockchain.get_latest_block().hash:
                    self.blockchain.chain.append(new_block)
                    self.blockchain.add_block_to_db(new_block)
                    self.blockchain.update_balances(new_block.transactions)
                    print(f"New block added to chain: {new_block.hash}")
                    self.broadcast_block(new_block)
                else:
                    print("Received block is invalid")
        elif message['type'] == 'CHAIN':
            new_chain = [Block.from_dict(block) for block in message['chain']]
            if self.blockchain.replace_chain(new_chain):
                print("Chain replaced with received chain.")
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
                print(f"Connected to peer: {host}:{port}")
            except socket.timeout:
                print(f"Connection to {host}:{port} timed out")
            except Exception as e:
                print(f"Could not connect to {host}:{port}: {e}")

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
            print(f"Connection to {host}:{port} timed out")
        except Exception as e:
            print(f"Could not send peers to {host}:{port}: {e}")
        finally:
            client.close()

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
            print(f"Connection to {host}:{port} timed out")
        except Exception as e:
            print(f"Could not send chain to {host}:{port}: {e}")
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
            print(f"Connection to {host}:{port} timed out")
        except Exception as e:
            print(f"Could not send pending transactions to {host}:{port}: {e}")
        finally:
            client.close()

    def broadcast(self, message):
        peers_copy = list(self.peers)
        for peer in peers_copy:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(5)  # Timeout de 5 segundos para evitar conexiones colgantes
                client.connect(peer)
                self.send_message(client, message)
                client.close()
                print(f"Message broadcasted to {peer}")
            except socket.timeout:
                print(f"Connection to {peer} timed out")
            except Exception as e:
                self.peers.remove(peer)
                print(f"Peer {peer} not available, removed from list: {e}")

    def broadcast_block(self, block):
        block_data = {
            'type': 'NEW_BLOCK',
            'index': block.index,
            'timestamp': block.timestamp.isoformat(),
            'transactions': [tx.to_dict() for tx in block.transactions],
            'previous_hash': block.previous_hash,
            'nonce': block.nonce,
            'hash': block.hash
        }
        print(f"Broadcasting block: {block_data}")
        self.broadcast(block_data)

    def broadcast_transaction(self, transaction):
        transaction_data = {
            'type': 'NEW_TRANSACTION',
            'transaction': transaction.to_dict()
        }
        print(f"Broadcasting transaction: {transaction_data}")
        self.broadcast(transaction_data)

    def get_balance(self):
        return self.blockchain.get_balance(self.node_id)

# Usage example
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <port>")
        sys.exit(1)

    my_port = int(sys.argv[1])
    all_ports = [5001, 5002, 5003, 5004]
    
    if my_port in all_ports:
        all_ports.remove(my_port)
    
    node = Node("localhost", my_port)
    
    print(f"Starting node on port {my_port}")
    
    node_thread = threading.Thread(target=node.start)
    node_thread.start()

    for port in all_ports:
        node.connect_to_peer("localhost", port)
    
    try:
        while True:
            action = input("Enter 't' to add a transaction, 'm' to mine pending transactions, or 'b' to check balance: ").strip().lower()
            if action == 't':
                recipient = input("Enter recipient port: ").strip()
                amount = float(input("Enter amount: ").strip())
                if node.blockchain.add_transaction(node.node_id, recipient, amount):
                    transaction = Transaction(node.node_id, recipient, amount)
                    node.broadcast_transaction(transaction)
            elif action == 'm':
                new_block = node.blockchain.mine_pending_transactions()
                if new_block:
                    print(f"New block mined: {new_block.hash}")
                    node.broadcast_block(new_block)
            elif action == 'b':
                print(f"Current balance: {node.get_balance()}")
    except KeyboardInterrupt:
        print("Shutting down node...")
        sys.exit(0)
