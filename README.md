# Distributed Systems Algorithms Implementation by Vinícius Abrunhosa

This project implements three distributed algorithms: **Token Ring**, **Anti-Entropy Gossip**, and **Totally Ordered Multicast**. All algorithms use the same port 50000 for communication, and the code is built entirely with Python's native libraries.

---

## Setup

This project uses **Python 3.12.7**. But others recents versions may works.

---

## Algorithms Overview

### 1. **Token Ring**
The **Token Ring** algorithm ensures mutual exclusion in a distributed system by passing a token between peers in a logical ring.

#### How to Use:
1. Run the calculator application:
   ```bash
   python3 multiCalculator.py
   ```
2. Set up the ring by starting each peer. Replace `next_host` and `multicalculator_host` with the appropriate IPs or hostnames:
   ```bash
   python3 peer_token.py localhost next_host multicalculator_host
   ```
3. Start the token exchange process:
   ```bash
   python3 inject.py some_peer
   ```

Once the injector is started, the peers will begin exchanging the token within the ring.

---

### 2. **Anti-Entropy Gossip Algorithm**
This algorithm disseminates information across peers using the Anti-Entropy method, ensuring eventual consistency.

#### How to Use:
Run each peer by providing its local IP and the IPs of its neighboring peers, separated by spaces:
```bash
python3 peer.py localhost neighbor_host1 neighbor_host2 ...
```

Each peer will periodically exchange data with its neighbors, updating its state using the Anti-Entropy algorithm.

---

### 3. **Totally Ordered Multicast**
The **Totally Ordered Multicast** algorithm ensures that all peers in the system receive messages in the same order, preserving causality.

#### How to Use:
Run each peer by providing its local IP and the IPs of all other peers in the system, separated by spaces:
```bash
python3 peer.py localhost peer1_host peer2_host ...
```

Messages sent within the system will follow the totally ordered multicast protocol.

---

## Key Notes

- **Token Ring:** Ensure that all peers in the ring are started before injecting the token.
- **Anti-Entropy Gossip:** Peers can dynamically join the network by connecting to at least one existing peer.
- **Totally Ordered Multicast:** All peers must be aware of the full set of participants in the system.
- **Shutdown Process:** 
    - To stop a peer gracefully token ring and totally ordered multicast, use Ctrl+C in the terminal where the peer is running.
    - In anti-entropy gossip Ctrl+C will just close the peer that sent signal.


---

## Example Execution

### Token Ring
1. Start `multiCalculator.py`:
   ```bash
   python3 multiCalculator.py
   ```
2. Start peers (example for a ring of 3 peers):
   ```bash
   python3 peer_token.py localhost 192.168.1.2 192.168.1.3
   python3 peer_token.py 192.168.1.2 192.168.1.3 localhost
   python3 peer_token.py 192.168.1.3 localhost 192.168.1.2
   ```
3. Inject the token:
   ```bash
   python3 inject.py localhost
   ```

### Gossip Algorithm
Start peers with their neighbors:
```bash
python3 peer.py localhost 192.168.1.2 192.168.1.3
python3 peer.py 192.168.1.2 localhost 
python3 peer.py 192.168.1.3 localhost 
```

### Totally Ordered Multicast
Start peers with the list of all participants:
```bash
python3 peer.py localhost 192.168.1.2 192.168.1.3
python3 peer.py 192.168.1.2 localhost 192.168.1.3
python3 peer.py 192.168.1.3 localhost 192.168.1.2
```

---

## Troubleshooting

- **Token Ring:**
  - Ensure that the injector is started after all peers are initialized.
  - Verify that all peers are connected in a proper logical ring.
- **Gossip Algorithm:**
  - If a peer fails, the algorithm will continue, but some updates might be delayed.
- **Totally Ordered Multicast:**
  - Ensure all peers are aware of the full list of participants before starting.
---


