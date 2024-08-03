# Desarrollo de una Blockchain desde Cero: Fundamentos y Ejemplo en Python

**Autor**: Pérez Diez Gabriel, grperezdiez@uda.com.ar

## Descripción

Este repositorio contiene una implementación básica de una blockchain desarrollada en Python. El objetivo de este proyecto es proporcionar una comprensión fundamental de la tecnología blockchain, destacando los componentes esenciales necesarios para su funcionamiento y ofreciendo un punto de partida educativo para aquellos interesados en adentrarse en este campo.

## Características

- **Estructura de Bloques:** Implementación de la estructura básica de un bloque, incluyendo el encabezado y la lista de transacciones.
- **Red P2P (Peer-to-Peer):** Configuración de una red descentralizada donde cada nodo actúa tanto como cliente como servidor.
- **Criptografía:** Uso de técnicas criptográficas como hashing y firmas digitales para asegurar las transacciones.
- **Mecanismo de Consenso:** Implementación del algoritmo Proof of Work (PoW) para la validación de transacciones y adición de bloques.

## Objetivos

- **Educación:** Proveer una base educativa para aquellos que deseen aprender sobre blockchain y sus componentes.
- **Accesibilidad:** Facilitar el acceso a la tecnología blockchain, reduciendo la brecha de conocimiento entre los principiantes y los expertos.
- **Experimentación:** Ofrecer un entorno experimental donde los usuarios puedan extender y modificar la implementación básica para fines de investigación o aplicaciones prácticas.

## Contenido

- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Arquitectura del Proyecto](#arquitectura-del-proyecto)
- [Clases Principales](#clases-principales)
- [Detalles de Implementación](#detalles-de-implementación)
- [Contribuciones](#contribuciones)

## Requisitos

- Python 3.6+
- Bibliotecas estándar de Python: `hashlib`, `datetime`, `sqlite3`, `json`, `socket`, `threading`, `sys`

## Instalación

1. Clona el repositorio en tu máquina local:

   ```bash
   git clone https://github.com/tu-usuario/blockchain-p2p.git
   cd blockchain-p2p
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

### Iniciar los Nodos

Se pueden inicia múltiples nodos en diferentes terminales. Esto se hace de la siguiente manera:

1. Inicia el primer nodo:

   ```bash
   python p2p.py 5001
   ```

2. Inicia el segundo nodo:

   ```bash
   python p2p.py 5002
   ```

### Interactuar con los Nodos

En la consola de cada nodo, puedes realizar las siguientes acciones:

- **Agregar una transacción**:

  ```plaintext
  Enter 't' to add a transaction, 'm' to mine pending transactions, or 'b' to check balance: t
  Enter recipient port: 5002
  Enter amount: 10.0
  ```

- **Minar transacciones pendientes**:

  ```plaintext
  Enter 't' to add a transaction, 'm' to mine pending transactions, or 'b' to check balance: m
  ```

- **Verificar el saldo**:
  ```plaintext
  Enter 't' to add a transaction, 'm' to mine pending transactions, or 'b' to check balance: b
  Current balance: 90.0
  ```

## Arquitectura del Proyecto

El proyecto consta de dos archivos principales:

1. `blockchain.py` - Implementa la lógica de la blockchain, incluidos los bloques, transacciones, minería y validación de la cadena.
2. `p2p.py` - Implementa la lógica de la red P2P, incluido el manejo de nodos, transmisión de mensajes y sincronización de la cadena de bloques entre nodos.

## Clases Principales

### Blockchain (blockchain.py)

- **Transaction**: Representa una transacción en la blockchain.
- **Block**: Representa un bloque en la blockchain.
- **Blockchain**: Gestiona la cadena de bloques, incluyendo la creación de bloques, validación de la cadena, minería y manejo de transacciones.

### P2P (p2p.py)

- **Node**: Representa un nodo en la red P2P. Gestiona la comunicación entre nodos, transmisión de mensajes y sincronización de la blockchain.

## Detalles de Implementación

### Blockchain

- **Transaction**: Incluye los atributos `sender`, `recipient` y `amount`.
- **Block**: Incluye los atributos `index`, `timestamp`, `transactions`, `previous_hash`, `nonce` y `hash`.
- **Blockchain**: Gestiona la cadena de bloques, incluyendo la creación del bloque génesis, carga de la cadena desde la base de datos, actualización de saldos, adición de transacciones y minería de bloques.

### P2P

- **Node**: Gestiona la comunicación entre nodos. Incluye métodos para iniciar el nodo, manejar mensajes de otros nodos, conectar con otros nodos, enviar mensajes, transmitir la cadena y las transacciones pendientes, y transmitir nuevos bloques y transacciones.
