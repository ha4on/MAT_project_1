import socket
import argparse
import logging
import json
import random
import base64
from Crypto.Cipher import AES

BLOCK_SIZE = 16

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def get_prime_factors(n):
    factors = []
    i = 2
    while i * i <= n:
        if n % i == 0:
            factors.append(i)
            while n % i == 0:
                n //= i
        i += 1
    if n > 1:
        factors.append(n)
    return factors

def is_generator(g, p):
    if g < 2 or g >= p:
        return False
    for factor in get_prime_factors(p - 1):
        if pow(g, (p - 1) // factor, p) == 1:
            return False
    return True

def get_aes_key(shared):
    return shared.to_bytes(2, byteorder="big") * 16

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

def send_error(conn, message):
    smsg = {}
    smsg["opcode"] = 3
    smsg["error"] = message
    send_json(conn, smsg)

def run(addr, port, msg):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((addr, port))
    logging.info("Alice is connected to {}:{}".format(addr, port))

    random.seed(None)

    smsg = {}
    smsg["opcode"] = 0
    smsg["type"] = "DH"
    send_json(conn, smsg)

    rmsg = recv_json(conn)
    bob_public = rmsg["public"]
    p = rmsg["parameter"]["p"]
    g = rmsg["parameter"]["g"]

    if not is_prime(p):
        send_error(conn, "incorrect prime number")
        conn.close()
        return
    if not is_generator(g, p):
        send_error(conn, "incorrect generator")
        conn.close()
        return

    private = random.randint(2, p - 2)
    public = pow(g, private, p)
    shared = pow(bob_public, private, p)
    key = get_aes_key(shared)

    smsg = {}
    smsg["opcode"] = 1
    smsg["type"] = "DH"
    smsg["public"] = public
    send_json(conn, smsg)

    rmsg = recv_json(conn)
    encrypted = base64.b64decode(rmsg["encryption"])
    logging.info("[*] Decrypted: {}".format(decrypt(key, encrypted)))

    smsg = {}
    smsg["opcode"] = 2
    smsg["type"] = "AES"
    smsg["encryption"] = base64.b64encode(encrypt(key, msg)).decode("ascii")
    send_json(conn, smsg)

    conn.close()

def command_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--addr", metavar="<bob's address>", help="Bob's address", type=str, required=True)
    parser.add_argument("-p", "--port", metavar="<bob's port>", help="Bob's port", type=int, required=True)
    parser.add_argument("-m", "--message", metavar="<message>", help="Message", type=str, required=True)
    parser.add_argument("-l", "--log", metavar="<log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)>", help="Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)", type=str, default="INFO")
    args = parser.parse_args()
    return args

def main():
    args = command_line_args()
    log_level = args.log
    logging.basicConfig(level=log_level)

    run(args.addr, args.port, args.message)

if __name__ == "__main__":
    main()
