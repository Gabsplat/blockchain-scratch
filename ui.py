import sys
import threading
from p2p import Node  # Import the Node class
from PyQt6.QtCore import QSize, Qt, QObject, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QWidget, QMainWindow, QSizePolicy, QMessageBox, QLineEdit
)

class EnterPortDialog(QMessageBox):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Puerto de nodo")
        self.setText("Ingresa el puerto del nodo")

        self.text_input = QLineEdit(self)
        self.text_input.setPlaceholderText("5500")
        self.layout().addWidget(self.text_input, 1, 0, 1, 2)
        
        self.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        self.exec()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.label = QLabel("Messages will appear here", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Get the port from the user
        port_dialog = EnterPortDialog()
        self.port = 5500
        
        print("Waiting dialog")
        if(port_dialog.result() == QMessageBox.StandardButton.Ok):
            self.port = int(port_dialog.text_input.text())
        else:
            sys.exit(1)

        # Initialize the node
        print("Initializing node")
        self.initialize_node()

        self.setWindowTitle("Blockchain from scratch")
        self.setFixedSize(QSize(1280, 720))

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.label)
        # Navbar
        navbar = Navbar(self.node)
        main_layout.addWidget(navbar)

        # Main Content Area
        main_content = QHBoxLayout()
        left_panel = LeftPanel()
        right_panel = ConnectedNodes()

        main_content.setSpacing(40)
        main_content.addLayout(left_panel, 7)
        main_content.addWidget(right_panel, 3)

        main_layout.addLayout(main_content)

        # Set main layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

       
        # Setup UI components
        # self.setup_ui()

    def initialize_node(self):
        # Initialize the Node
        print(self.port)
        self.node = Node("localhost", self.port)
        self.node.message_received.connect(self.on_message_received)  # Connect the signal to the slot

        self.node_thread = threading.Thread(target=self.node.start)
        self.node_thread.start()

        # Wait for the node to start running
        while not self.node.running:
            pass  # Busy-wait until the node is running

        if(self.node.running):
            print("Node is running now")

        print(self.node.get_balance())
        
    def on_message_received(self, message):
        self.label.setText(message)


class Navbar(QWidget):
    def __init__(self, node: Node):
        super().__init__()

        self.node = node

        self.setFixedHeight(80) 
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("font-size: 20px; border-radius: 10px; background-color: #333; color: white; padding: 10px;")

        layout = QHBoxLayout()

        port = node.port
        balance = node.get_balance()

        label1 = QLabel("Puerto del nodo: " + str(node.port))
        label2 = QLabel("Monedas: " + str(balance))

        layout.addWidget(label1)
        layout.addStretch(1)
        layout.addWidget(label2)

        self.setLayout(layout)


class LeftPanel(QVBoxLayout):
    def __init__(self):
        super().__init__()
        # Actions Panel
        actions = Actions()
        self.addWidget(actions)

        # Transactions to Mine Panel
        transactions = PendingMine()
        self.addWidget(transactions)

class Actions(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        layout.addWidget(QPushButton("Enviar monedas"))
        layout.addWidget(QPushButton("Ver blockchain"))
        self.setLayout(layout)

class PendingMine(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout()
        self.setStyleSheet("padding: 20px;")
        # Adding "Minar" buttons in a grid
        for i in range(2):
            for j in range(3):
                layout.addWidget(QPushButton("Minar"), i, j)
        self.setLayout(layout)

class ConnectedNodes(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        label = QLabel("Nodos conectados")
        label.setStyleSheet("font-size: 24px; font-weight: 600; margin-left: 0; margin-bottom: 20px; background-color: #333; padding: 10px; border-radius: 10px;")
        layout.addWidget(label)
        
        for i in range(3):
            newLabel = QLabel("Node - Port " + str(i+1))
            newLabel.setStyleSheet("font-size: 16px")
            layout.addWidget(newLabel)
        self.setLayout(layout)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
