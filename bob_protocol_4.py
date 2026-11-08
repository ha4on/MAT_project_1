import socket
import threading
import argparse
import logging
import json
import random
import base64

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

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

def get_bad_parameters(error):
    if error == "prime":
        numbers = [n for n in range(401, 500) if not is_prime(n)]
        p = random.choice(numbers)
        g = random.randint(2, p - 1)
    else:
        p = random.choice(get_prime(400, 500))
        numbers = [g for g in range(2, p) if not is_generator(g, p)]
        g = random.choice(numbers)
    return p, g

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

def handler(conn, error):
    rmsg = recv_json(conn)
    if rmsg["opcode"] != 0 or rmsg["type"] != "DH":
        conn.close()
        return

    p, g = get_bad_parameters(error)
    private = random.randint(2, p - 2)
    public = pow(g, private, p)
    encoded_public = base64.b64encode(public.to_bytes(2, byteorder="big")).decode("ascii")

    smsg = {}
    smsg["opcode"] = 1
    smsg["type"] = "DH"
    smsg["public"] = encoded_public
    smsg["parameter"] = {}
    smsg["parameter"]["p"] = p
    smsg["parameter"]["g"] = g
    send_json(conn, smsg)

    rmsg = recv_json(conn)
    logging.error(rmsg["error"])

    conn.close()

def run(addr, port, error):
    bob = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bob.bind((addr, port))

    bob.listen(10)
    logging.info("[*] Bob is listening on {}:{}".format(addr, port))

    while True:
        conn, info = bob.accept()

        logging.info("[*] Bob accepts the connection from {}:{}".format(info[0], info[1]))

        conn_handle = threading.Thread(target=handler, args=(conn, error,))
        conn_handle.start()
        conn_handle.join()

def command_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--addr", metavar="<bob's IP address>", help="Bob's IP address", type=str, default="0.0.0.0")
    parser.add_argument("-p", "--port", metavar="<bob's open port>", help="Bob's port", type=int, required=True)
    parser.add_argument("-e", "--error", metavar="<prime/generator>", help="DH parameter error", type=str, choices=["prime", "generator"], default="prime")
    parser.add_argument("-m", "--message", metavar="<message>", help="Message", type=str)
    parser.add_argument("-l", "--log", metavar="<log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)>", help="Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)", type=str, default="INFO")
    args = parser.parse_args()
    return args

def main():
    args = command_line_args()
    log_level = args.log
    logging.basicConfig(level=log_level)

    random.seed(None)
    run(args.addr, args.port, args.error)

if __name__ == "__main__":
    main()
