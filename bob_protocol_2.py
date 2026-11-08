import socket
import threading
import argparse
import logging
import json
import random
import base64
import math
from Crypto.Cipher import AES

BLOCK_SIZE = 16

def get_prime(l, r):
    p = []
    tL = [0, 0] + [1] * (r - 1)
    for i in range(2, r):
        if tL[i]:
            if i > l:
                p.append(i)
            for j in range(2 * i, r, i):
                tL[j] = 0
    return p

def generate_rsa_keypair():
    p, q = random.sample(get_prime(400, 500), 2)
    n = p * q
    phi = (p - 1) * (q - 1)

    public = random.randint(2, phi - 1)
    while math.gcd(public, phi) != 1:
        public = random.randint(2, phi - 1)

    private = pow(public, -1, phi)
    return private, public, n

def encrypt(key, msg):
    msg = msg.encode()
    pad = BLOCK_SIZE - len(msg) % BLOCK_SIZE
    msg = msg + bytes([pad]) * pad
    aes = AES.new(key, AES.MODE_ECB)
    return aes.encrypt(msg)

def decrypt(key, encrypted):
    aes = AES.new(key, AES.MODE_ECB)
    decrypted = aes.decrypt(encrypted)
    return decrypted[:-decrypted[-1]].decode()

def send_json(conn, smsg):
    logging.debug("smsg: {}".format(smsg))

    sjs = json.dumps(smsg)
    logging.debug("sjs: {}".format(sjs))

    sbytes = sjs.encode("ascii")
    logging.debug("sbytes: {}".format(sbytes))

    conn.send(sbytes)
    logging.info("[*] Sent: {}".format(sjs))

def recv_json(conn):
    rbytes = conn.recv(4096)
    logging.debug("rbytes: {}".format(rbytes))

    rjs = rbytes.decode("ascii")
    logging.debug("rjs: {}".format(rjs))

    rmsg = json.loads(rjs)
    logging.debug("rmsg: {}".format(rmsg))
    logging.info("[*] Received: {}".format(rjs))
    return rmsg

def handler(conn, msg):
    rmsg = recv_json(conn)
    if rmsg["opcode"] != 0 or rmsg["type"] != "RSA":
        conn.close()
        return

    private, public, n = generate_rsa_keypair()

    smsg = {}
    smsg["opcode"] = 1
    smsg["type"] = "RSA"
    smsg["public"] = public
    smsg["parameter"] = {}
    smsg["parameter"]["n"] = n
    send_json(conn, smsg)

    rmsg = recv_json(conn)
    encrypted_key = rmsg["encrypted_key"]
    key = bytes(pow(value, private, n) for value in encrypted_key)

    smsg = {}
    smsg["opcode"] = 2
    smsg["type"] = "AES"
    smsg["encryption"] = base64.b64encode(encrypt(key, msg)).decode("ascii")
    send_json(conn, smsg)

    rmsg = recv_json(conn)
    encrypted = base64.b64decode(rmsg["encryption"])
    logging.info("[*] Decrypted: {}".format(decrypt(key, encrypted)))

    conn.close()

def run(addr, port, msg):
    bob = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bob.bind((addr, port))

    bob.listen(10)
    logging.info("[*] Bob is listening on {}:{}".format(addr, port))

    while True:
        conn, info = bob.accept()

        logging.info("[*] Bob accepts the connection from {}:{}".format(info[0], info[1]))

        conn_handle = threading.Thread(target=handler, args=(conn, msg,))
        conn_handle.start()
        conn_handle.join()

def command_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--addr", metavar="<bob's IP address>", help="Bob's IP address", type=str, default="0.0.0.0")
    parser.add_argument("-p", "--port", metavar="<bob's open port>", help="Bob's port", type=int, required=True)
    parser.add_argument("-m", "--message", metavar="<message>", help="Message", type=str, required=True)
    parser.add_argument("-l", "--log", metavar="<log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)>", help="Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)", type=str, default="INFO")
    args = parser.parse_args()
    return args

def main():
    args = command_line_args()
    log_level = args.log
    logging.basicConfig(level=log_level)

    random.seed(None)
    run(args.addr, args.port, args.message)

if __name__ == "__main__":
    main()
