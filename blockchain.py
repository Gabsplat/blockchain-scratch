import hashlib
import datetime
import sqlite3
import json

class Transaction:
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount

    def to_dict(self):
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount
        }

    @staticmethod
    def from_dict(data):
        return Transaction(data['sender'], data['recipient'], data['amount'])

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0, hash=None):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = hash or self.calculate_hash()

    def calculate_hash(self):
        sha = hashlib.sha256()
        sha.update(
            str(self.index).encode('utf-8') +
            str(self.timestamp).encode('utf-8') +
            str([tx.to_dict() for tx in self.transactions]).encode('utf-8') +
            str(self.previous_hash).encode('utf-8') +
            str(self.nonce).encode('utf-8')
        )
        return sha.hexdigest()

    def mine_block(self, difficulty):
        target = '0' * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

    def to_dict(self):
        return {
            'index': self.index,
            'timestamp': self.timestamp.isoformat(),
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }

    @staticmethod
    def from_dict(data):
        return Block(
            data['index'],
            datetime.datetime.fromisoformat(data['timestamp']),
            [Transaction.from_dict(tx) for tx in data['transactions']],
            data['previous_hash'],
            data['nonce'],
            data['hash']
        )

class Blockchain:
    def __init__(self, difficulty=4, db_path='blockchain.db'):
        self.difficulty = difficulty
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()
        self.chain = self.load_chain()
        self.pending_transactions = []
        self.balances = self.load_balances()  # Initialize balances after loading the chain

    def create_table(self):
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS blocks (
                                    block_index INTEGER PRIMARY KEY,
                                    timestamp TEXT,
                                    transactions TEXT,
                                    previous_hash TEXT,
                                    nonce INTEGER,
                                    hash TEXT
                                )''')

    def create_genesis_block(self):
        genesis_transactions = [
            Transaction("genesis", "5001", 100),
            Transaction("genesis", "5002", 100),
            Transaction("genesis", "5003", 100),
            Transaction("genesis", "5004", 100)
        ]
        genesis_block = Block(0, datetime.datetime.now(), genesis_transactions, "0")
        self.add_block_to_db(genesis_block)
        return genesis_block

    def load_chain(self):
        with self.conn:
            cursor = self.conn.execute('SELECT * FROM blocks ORDER BY block_index ASC')
            rows = cursor.fetchall()
            if not rows:
                return [self.create_genesis_block()]
            return [Block.from_dict({
                'index': row[0],
                'timestamp': row[1],
                'transactions': json.loads(row[2]),
                'previous_hash': row[3],
                'nonce': row[4],
                'hash': row[5]
            }) for row in rows]

    def load_balances(self):
        balances = {}
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender != "genesis":
                    if tx.sender in balances:
                        balances[tx.sender] -= tx.amount
                    else:
                        balances[tx.sender] = -tx.amount
                if tx.recipient in balances:
                    balances[tx.recipient] += tx.amount
                else:
                    balances[tx.recipient] = tx.amount
        return balances

    def add_block_to_db(self, block):
        with self.conn:
            cursor = self.conn.execute('SELECT * FROM blocks WHERE hash = ?', (block.hash,))
            if cursor.fetchone() is None:
                self.conn.execute('INSERT INTO blocks (block_index, timestamp, transactions, previous_hash, nonce, hash) VALUES (?, ?, ?, ?, ?, ?)',
                                  (block.index, block.timestamp.isoformat(), json.dumps([tx.to_dict() for tx in block.transactions]), block.previous_hash, block.nonce, block.hash))

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, transactions):
        latest_block = self.get_latest_block()
        new_block = Block(len(self.chain), datetime.datetime.now(), transactions, latest_block.hash)
        new_block.mine_block(self.difficulty)
        
        # Ensure the new block's hash is calculated after mining
        new_block.hash = new_block.calculate_hash()
        
        # Append the new block to the chain
        self.chain.append(new_block)
        self.add_block_to_db(new_block)
        self.update_balances(transactions)
        print(f"Nuevo bloque minado: {new_block.hash}\n")
        return new_block

    def update_balances(self, transactions):
        for tx in transactions:
            if tx.sender in self.balances:
                self.balances[tx.sender] -= tx.amount
            else:
                self.balances[tx.sender] = -tx.amount
            if tx.recipient in self.balances:
                self.balances[tx.recipient] += tx.amount
            else:
                self.balances[tx.recipient] = tx.amount

    def add_transaction(self, sender, recipient, amount):
        if sender != "genesis" and (sender not in self.balances or self.balances[sender] < amount):
            print(f"Transacción de {sender} a {recipient} por la cantidad de{amount} falló: no hay saldo suficiente.\n")
            return False
        transaction = Transaction(sender, recipient, amount)
        self.pending_transactions.append(transaction)
        print(f"Transacción agregada: {sender} -> {recipient}: {amount}\n")
        return True

    def mine_pending_transactions(self):
        if not self.pending_transactions:
            print("No hay transacciones para minar.\n") 
            return None
        new_block = self.add_block(self.pending_transactions)
        self.pending_transactions = []
        return new_block

    def is_chain_valid(self, chain=None):
        chain = chain or self.chain
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True

    def replace_chain(self, new_chain):
        if len(new_chain) > len(self.chain) and self.is_chain_valid(new_chain):
            self.chain = new_chain
            with self.conn:
                self.conn.execute('DELETE FROM blocks')
                for block in new_chain:
                    self.add_block_to_db(block)
            self.balances = self.load_balances()
            return True
        return False

    def get_balance(self, node_id):
        return self.balances.get(node_id, 0)
