# Python C2 Botnet Infrastructure

A lightweight, multi-protocol Command and Control (C2) infrastructure implemented entirely in Python. This project demonstrates how distributed nodes ("bots") can be controlled remotely via a central broker, supporting both raw TCP (via Ncat) and the Internet Relay Chat (IRC) protocol.

## Features
* **Dual Protocol Support:** Operates over a raw TCP broker or a standard IRC daemon.
* **Cryptographic Authentication:** Commands are authenticated using SHA-256 hashed Message Authentication Codes (MACs) and unique nonces to prevent unauthorized execution and replay attacks.
* **Asynchronous Command Aggregation:** The controller utilizes I/O multiplexing (`select`) to dispatch commands to multiple nodes and aggregate their asynchronous replies within a strict timeout window.
* **High Resiliency:** Nodes feature autonomous fault tolerance, automatically detecting dropped connections and indefinitely attempting reconnections without crashing.
* **Simulated Network Operations:** Supports commands for node status reporting, graceful shutdown, network migration (moving to a new C2 server), and simulated target connection testing (with strict OS-level timeout handling).

## Quick Start (IRC Mode)

The IRC implementation relies on a local IRC server. I recommend using `miniircd` for local testing.

### 1. Setup the IRC Server
Clone and start the `miniircd` server on port 6667:
```bash
git clone [https://github.com/jrosdahl/miniircd.git](https://github.com/jrosdahl/miniircd.git)
cd miniircd
./miniircd --ports 6667 --debug
