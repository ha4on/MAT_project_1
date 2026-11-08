import socket
import argparse
import logging
import json
import random
import base64
from Crypto.Cipher import AES

BLOCK_SIZE = 16

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

def run(addr, port, msg):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((addr, port))
    logging.info("Alice is connected to {}:{}".format(addr, port))

    random.seed(None)

    smsg = {}
    smsg["opcode"] = 0
    smsg["type"] = "RSA"
    send_json(conn, smsg)

    rmsg = recv_json(conn)
    public = rmsg["public"]
    n = rmsg["parameter"]["n"]

    key = random.randbytes(32)
    encrypted_key = [pow(value, public, n) for value in key]

    smsg = {}
    smsg["opcode"] = 2
    smsg["type"] = "RSA"
    smsg["encrypted_key"] = encrypted_key
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
