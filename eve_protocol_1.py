import socket
import threading
import argparse
import logging
import json
import base64
from Crypto.Cipher import AES

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def crack_rsa(public, n):
    for p in range(401, 500):
        if n % p == 0:
            q = n // p
            if p != q and 400 < q < 500 and is_prime(p) and is_prime(q):
                phi = (p - 1) * (q - 1)
                private = pow(public, -1, phi)
                return private, p, q
    raise ValueError("RSA modulus could not be factored")

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

def handler(alice, bob_addr, bob_port):
    bob = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bob.connect((bob_addr, bob_port))
    logging.info("[*] Eve is connected to Bob at {}:{}".format(bob_addr, bob_port))

    rmsg = recv_json(alice)
    send_json(bob, rmsg)

    rmsg = recv_json(bob)
    public = rmsg["public"]
    n = rmsg["parameter"]["n"]
    private, p, q = crack_rsa(public, n)
    logging.info("[*] RSA key was cracked")
    logging.info(" - private: {}".format(private))
    logging.info(" - p: {}".format(p))
    logging.info(" - q: {}".format(q))
    send_json(alice, rmsg)

    rmsg = recv_json(alice)
    encrypted_key = rmsg["encrypted_key"]
    key = bytes(pow(value, private, n) for value in encrypted_key)
    logging.info("[*] AES key: {}".format(base64.b64encode(key).decode("ascii")))
    send_json(bob, rmsg)

    rmsg = recv_json(bob)
    encrypted = base64.b64decode(rmsg["encryption"])
    logging.info("[*] Decrypted from Bob: {}".format(decrypt(key, encrypted)))
    send_json(alice, rmsg)

    rmsg = recv_json(alice)
    encrypted = base64.b64decode(rmsg["encryption"])
    logging.info("[*] Decrypted from Alice: {}".format(decrypt(key, encrypted)))
    send_json(bob, rmsg)

    alice.close()
    bob.close()

def run(addr, port, bob_addr, bob_port):
    eve = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    eve.bind((addr, port))

    eve.listen(10)
    logging.info("[*] Eve is listening on {}:{}".format(addr, port))

    while True:
        conn, info = eve.accept()

        logging.info("[*] Eve accepts the connection from {}:{}".format(info[0], info[1]))

        conn_handle = threading.Thread(target=handler, args=(conn, bob_addr, bob_port,))
        conn_handle.start()
        conn_handle.join()

def command_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--addr", metavar="<eve's IP address>", help="Eve's IP address", type=str, default="0.0.0.0")
    parser.add_argument("-p", "--port", metavar="<eve's open port>", help="Eve's port", type=int, required=True)
    parser.add_argument("-b", "--bob-addr", metavar="<bob's address>", help="Bob's address", type=str, required=True)
    parser.add_argument("-q", "--bob-port", metavar="<bob's port>", help="Bob's port", type=int, required=True)
    parser.add_argument("-l", "--log", metavar="<log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)>", help="Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)", type=str, default="INFO")
    args = parser.parse_args()
    return args

def main():
    args = command_line_args()
    log_level = args.log
    logging.basicConfig(level=log_level)

    run(args.addr, args.port, args.bob_addr, args.bob_port)

if __name__ == "__main__":
    main()
