#!/usr/bin/env python3
# ssh_server_for_scanner.py
import socket
import threading
import paramiko
import subprocess
import os
import uuid
import platform
import getpass
import logging

BIND_HOST = "0.0.0.0"
BIND_PORT = 2200
ALLOWED_USERNAME = "ssh"
ALLOWED_PASSWORD = "exploit"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

host_key = paramiko.RSAKey.generate(2048)

class SimpleServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_auth_password(self, username, password):
        if username == ALLOWED_USERNAME and password == ALLOWED_PASSWORD:
            logging.info(f"Successful auth for {username}")
            return paramiko.AUTH_SUCCESSFUL
        logging.warning(f"Failed auth attempt username={username}")
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "password"

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

def get_info_line():
    hostname = platform.node()
    username = getpass.getuser()
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                    for ele in range(0, 8*6, 8)][::-1])
    # format exactly like client expects: INFO|Hostname:...|Username:...|MAC:...
    return f"INFO|Hostname:{hostname}|Username:{username}|MAC:{mac}\n"

def send_in_chunks(chan, data, chunk_size=1024):
    for i in range(0, len(data), chunk_size):
        chan.send(data[i:i+chunk_size])

def handle_client(sock, addr):
    logging.info(f"Incoming connection from {addr}")
    transport = None
    chan = None
    try:
        transport = paramiko.Transport(sock)
        transport.add_server_key(host_key)
        server = SimpleServer()
        try:
            transport.start_server(server=server)
        except paramiko.SSHException:
            logging.error("SSH negotiation failed")
            return

        chan = transport.accept(20)
        if chan is None:
            logging.info("No channel from client")
            return

        # send the INFO line first (client's get_server_info() reads this)
        info_line = get_info_line()
        chan.send(info_line)
        chan.send("Welcome. Type commands, they will be executed.\n")

        while True:
            chan.send("$ ")
            # read a line
            data = b""
            while not data.endswith(b"\n"):
                part = chan.recv(1024)
                if not part:
                    break
                data += part
            if not data:
                break
            cmd = data.decode(errors="replace").strip()
            if cmd.lower() in ("exit", "quit"):
                chan.send("Goodbye.\n")
                break

            logging.info(f"[{addr}] Executing: {cmd}")
            try:
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                out = proc.stdout or ""
                err = proc.stderr or ""
                combined = out + err
                if not combined:
                    combined = "(no output)\n"
                send_in_chunks(chan, combined)
            except Exception as e:
                send_in_chunks(chan, f"Command execution error: {e}\n")
    except Exception as e:
        logging.exception(f"Error handling client {addr}: {e}")
    finally:
        try:
            if chan:
                chan.close()
        except Exception:
            pass
        try:
            if transport:
                transport.close()
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass
        logging.info(f"Connection {addr} closed")

def start_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((BIND_HOST, BIND_PORT))
    srv.listen(100)
    logging.info(f"SSH-like server listening on {BIND_HOST}:{BIND_PORT}")
    try:
        while True:
            client_sock, addr = srv.accept()
            t = threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        logging.info("Shutting down (KeyboardInterrupt)")
    finally:
        srv.close()

if __name__ == "__main__":
    logging.info(f"Allowed credentials: {ALLOWED_USERNAME}/{ALLOWED_PASSWORD}")
    start_server()
