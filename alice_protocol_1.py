import socket
import argparse
import logging
import json

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

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

def run(addr, port):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((addr, port))
    logging.info("Alice is connected to {}:{}".format(addr, port))

    smsg = {}
    smsg["opcode"] = 0
    smsg["type"] = "RSAKey"
    send_json(conn, smsg)

    rmsg = recv_json(conn)
    private = rmsg["private"]
    public = rmsg["public"]
    p = rmsg["parameter"]["p"]
    q = rmsg["parameter"]["q"]

    p_correct = is_prime(p)
    q_correct = is_prime(q)
    phi = (p - 1) * (q - 1)
    key_correct = p != q and p_correct and q_correct and (private * public) % phi == 1

    logging.info(" - private: {}".format(private))
    logging.info(" - public: {}".format(public))
    logging.info(" - p: {} ({})".format(p, p_correct))
    logging.info(" - q: {} ({})".format(q, q_correct))
    logging.info(" - keypair: {}".format(key_correct))

    conn.close()

def command_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--addr", metavar="<bob's address>", help="Bob's address", type=str, required=True)
    parser.add_argument("-p", "--port", metavar="<bob's port>", help="Bob's port", type=int, required=True)
    parser.add_argument("-l", "--log", metavar="<log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)>", help="Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)", type=str, default="INFO")
    args = parser.parse_args()
    return args

def main():
    args = command_line_args()
    log_level = args.log
    logging.basicConfig(level=log_level)

    run(args.addr, args.port)

if __name__ == "__main__":
    main()
