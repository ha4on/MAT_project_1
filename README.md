# MAT Project 1: Alice and Bob (RSA / Diffie-Hellman)

EL2001 Mathematical Foundation of Computer Science, Project 1.

## Team and roles

| Member | Role |
|---|---|
| Hyeonghun Ju | Bob (server side, `bob_protocol_*.py`) |
| Jiyou Kim | Alice (client side, `alice_protocol_*.py`) |
| Both | Git / GitHub management; verifying that each protocol works against the course test servers |

## Files

| Protocol | Alice | Bob | What it does |
|---|---|---|---|
| I | `alice_protocol_1.py` | `bob_protocol_1.py` | RSA key generation; Alice verifies the key pair |
| II | `alice_protocol_2.py` | `bob_protocol_2.py` | RSA session-key transfer, then AES messages |
| III | `alice_protocol_3.py` | `bob_protocol_3.py` | Diffie-Hellman key exchange, then AES messages |
| IV | `alice_protocol_4.py` | `bob_protocol_4.py` | DH error control (non-prime p / non-generator g) |

## Setup

```
pip3 install pycryptodome
```

## Run

Start Bob first, then Alice. Replace the port and addresses as needed.

```
# Protocol I
python3 bob_protocol_1.py --port 5551
python3 alice_protocol_1.py --addr 127.0.0.1 --port 5551

# Protocol II
python3 bob_protocol_2.py --port 5552 -m "Hello"
python3 alice_protocol_2.py --addr 127.0.0.1 --port 5552 -m "Hello from Alice"

# Protocol III
python3 bob_protocol_3.py --port 5553 -m "Hello"
python3 alice_protocol_3.py --addr 127.0.0.1 --port 5553 -m "Hello from Alice"

# Protocol IV (Bob sends a bad prime or a bad generator)
python3 bob_protocol_4.py --port 5554 -e prime
python3 bob_protocol_4.py --port 5554 -e generator
python3 alice_protocol_4.py --addr 127.0.0.1 --port 5554
```

Use `-h` on any script to see its options.

## Test servers

The course test servers are at `10.41.12.51` (ports 5551 to 5554 for protocols I to IV) and need the KENTECH VPN.

```
python3 alice_protocol_1.py --addr 10.41.12.51 --port 5551
```

## Verification log

`alice_protocol_*.py` was run against the course test servers (`10.41.12.51`, ports 5551 to 5554) on 2026-11-08.

| Protocol | Result against the course test server |
|---|---|
| I | key pair verified (valid pair accepted; invalid pair with p = q reported as `False`) |
| II | server message decrypted, reply sent |
| III | DH parameters checked, server message decrypted, reply sent |
| IV | `incorrect prime number` and `incorrect generator` errors sent |
