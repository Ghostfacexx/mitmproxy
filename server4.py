#!/root/nfcgatepin/server/nfcgate-venv/bin/python3
import argparse
import socket
import socketserver
import ssl
import struct
import datetime
import sys
import logging
import os
from logging.handlers import RotatingFileHandler
from binascii import hexlify

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Constants
HOST = "0.0.0.0"
PORT = 5566
LOG_DIR = "/root/nfcgatepin/server/logs"
LOG_FILE = os.path.join(LOG_DIR, "nfcgate_server.log")

# Ensure log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure logging
logger = logging.getLogger('NFCGateServer')
logger.setLevel(logging.DEBUG)

# Formatter with detailed output
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] [%(name)s] [PID:%(process)d] [Thread:%(thread)d] '
    '[Client:%(client_addr)s] [Session:%(session_id)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S.%f'
)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler with rotation (10MB per file, keep 5 backups)
file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=10*1024*1024, backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Logging with client-specific context
def log_with_context(message, level=logging.INFO, client=None, session=None, extra_data=None):
    extra = {
        'client_addr': client.client_address if client else 'N/A',
        'session_id': str(session) if session else 'None'
    }
    if extra_data:
        extra.update(extra_data)
    logger.log(level, message, extra=extra)

class PluginHandler:
    def __init__(self, plugins):
        self.plugin_list = []
        for modname in plugins:
            try:
                print(f"Attempting to import plugins.mod_{modname}")
                plugin = __import__(f"plugins.mod_{modname}", fromlist=["plugins"])
                self.plugin_list.append((modname, plugin))
                log_with_context(f"Loaded plugin: mod_{modname}", logging.INFO)
            except ImportError as e:
                log_with_context(f"Failed to load plugin mod_{modname}: {str(e)}", logging.ERROR)
                print(f"ImportError details: {str(e)}")
                raise

    def filter(self, client, data):
        log_with_context(f"Filtering data: {hexlify(data).decode()}", logging.DEBUG, client=client)
        for modname, plugin in self.plugin_list:
            try:
                if type(data) == list:
                    first = data[0]
                else:
                    first = data
                first = plugin.handle_data(
                    lambda *x: log_with_context(*x, client=client, extra_data={'tag': modname}),
                    first,
                    client.state
                )
                if type(data) == list:
                    data = [first] + data[1:]
                else:
                    data = first
                log_with_context(f"Plugin {modname} processed data: {hexlify(data if type(data) != list else data[0]).decode()}", logging.DEBUG, client=client)
            except Exception as e:
                log_with_context(f"Plugin {modname} failed: {str(e)}", logging.ERROR, client=client)
        return data

class NFCGateClientHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, srv):
        self.session = None
        self.state = {}
        super().__init__(request, client_address, srv)

    def setup(self):
        super().setup()
        self.request.settimeout(300)
        log_with_context("Client connected", logging.INFO, client=self)
        log_with_context(f"Socket details: timeout={self.request.gettimeout()}, peer={self.request.getpeername()}", logging.DEBUG, client=self)

    def handle(self):
        super().handle()
        log_with_context("Starting client handler loop", logging.DEBUG, client=self)

        while True:
            try:
                msg_len_data = self.rfile.read(5)
                log_with_context(f"Read message length data: {hexlify(msg_len_data).decode()}", logging.DEBUG, client=self)
            except socket.timeout:
                log_with_context("Client timed out after 300s", logging.WARNING, client=self)
                break
            except Exception as e:
                log_with_context(f"Error reading message length: {str(e)}", logging.ERROR, client=self)
                break

            if len(msg_len_data) < 5:
                log_with_context(f"Received incomplete length data ({len(msg_len_data)} bytes), disconnecting", logging.WARNING, client=self)
                break

            try:
                msg_len, session = struct.unpack("!IB", msg_len_data)
                log_with_context(f"Parsed message: length={msg_len}, session={session}", logging.DEBUG, client=self)
            except struct.error as e:
                log_with_context(f"Failed to unpack message length: {str(e)}", logging.ERROR, client=self)
                break

            data = self.rfile.read(msg_len)
            log_with_context(f"Received data: {hexlify(data).decode()}", logging.INFO, client=self)

            if msg_len == 0 or (session == 0 and self.session is None):
                log_with_context("Empty message or no session, disconnecting", logging.WARNING, client=self)
                break

            if self.session != session:
                log_with_context(f"Session change detected: old={self.session}, new={session}", logging.INFO, client=self)
                self.server.remove_client(self, self.session)
                self.session = session
                self.server.add_client(self, session)

            try:
                filtered_data = self.server.plugins.filter(self, data)
                self.server.send_to_clients(self.session, filtered_data, self)
            except Exception as e:
                log_with_context(f"Error processing or sending data: {str(e)}", logging.ERROR, client=self)

    def finish(self):
        log_with_context("Client disconnecting", logging.INFO, client=self)
        self.server.remove_client(self, self.session)
        super().finish()

class NFCGateServer(socketserver.ThreadingTCPServer):
    def __init__(self, server_address, request_handler, plugins, tls_options=None, bind_and_activate=True):
        self.allow_reuse_address = True
        super().__init__(server_address, request_handler, bind_and_activate)
        self.clients = {}
        self.plugins = PluginHandler(plugins)
        self.tls_options = tls_options

        log_with_context(f"NFCGate server initialized on {server_address}", logging.INFO)
        if self.tls_options:
            log_with_context(f"TLS enabled: cert={self.tls_options['cert_file']}, key={self.tls_options['key_file']}", logging.INFO)

    def get_request(self):
        client_socket, from_addr = super().get_request()
        log_with_context(f"New connection from {from_addr}", logging.DEBUG)
        if not self.tls_options:
            return client_socket, from_addr
        try:
            wrapped_socket = self.tls_options["context"].wrap_socket(client_socket, server_side=True)
            log_with_context(f"TLS handshake completed for {from_addr}", logging.DEBUG)
            return wrapped_socket, from_addr
        except ssl.SSLError as e:
            log_with_context(f"TLS handshake failed: {str(e)}", logging.ERROR)
            raise

    def add_client(self, client, session):
        if session is None:
            log_with_context("Attempted to add client to null session", logging.WARNING, client=client)
            return

        if session not in self.clients:
            self.clients[session] = []
            log_with_context(f"Created new session {session}", logging.INFO, client=client)

        self.clients[session].append(client)
        log_with_context(f"Client joined session {session}, total clients={len(self.clients[session])}", logging.INFO, client=client)

    def remove_client(self, client, session):
        if session is None or session not in self.clients:
            log_with_context("Attempted to remove client from null or unknown session", logging.WARNING, client=client)
            return

        self.clients[session].remove(client)
        log_with_context(f"Client left session {session}, remaining clients={len(self.clients[session])}", logging.INFO, client=client)
        if not self.clients[session]:
            del self.clients[session]
            log_with_context(f"Session {session} emptied and removed", logging.INFO, client=client)

    def send_to_clients(self, session, msgs, origin):
        if session is None or session not in self.clients:
            log_with_context(f"Cannot send to null or unknown session {session}", logging.WARNING, client=origin)
            return

        if type(msgs) != list:
            msgs = [msgs]

        for client in self.clients[session]:
            if client is origin:
                continue
            try:
                for msg in msgs:
                    msg_len = len(msg)
                    client.wfile.write(int.to_bytes(msg_len, 4, byteorder='big'))
                    client.wfile.write(msg)
                    log_with_context(f"Sent {msg_len} bytes to client: {hexlify(msg).decode()}", logging.DEBUG, client=client, session=session)
            except Exception as e:
                log_with_context(f"Failed to send to client: {str(e)}", logging.ERROR, client=client, session=session)

        log_with_context(f"Published to {len(self.clients[session]) - 1} clients in session {session}", logging.INFO, client=origin)

def parse_args():
    parser = argparse.ArgumentParser(prog="NFCGate server")
    parser.add_argument("plugins", type=str, nargs="*", help="List of plugin modules to load.")
    parser.add_argument("-s", "--tls", help="Enable TLS. You must specify certificate and key.",
                        default=False, action="store_true")
    parser.add_argument("--tls_cert", help="TLS certificate file in PEM format.", action="store")
    parser.add_argument("--tls_key", help="TLS key file in PEM format.", action="store")

    args = parser.parse_args()
    tls_options = None

    if args.tls:
        if args.tls_cert is None or args.tls_key is None:
            log_with_context("TLS enabled but cert or key missing", logging.CRITICAL)
            sys.exit(1)

        tls_options = {
            "cert_file": args.tls_cert,
            "key_file": args.tls_key
        }
        try:
            tls_options["context"] = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            tls_options["context"].load_cert_chain(tls_options["cert_file"], tls_options["key_file"])
            log_with_context("TLS context loaded successfully", logging.INFO)
        except ssl.SSLError as e:
            log_with_context(f"TLS cert/key load failed: {str(e)}", logging.CRITICAL)
            sys.exit(1)

    return args.plugins, tls_options

def main():
    plugins, tls_options = parse_args()
    log_with_context(f"Starting server with plugins: {plugins}", logging.INFO)
    server = NFCGateServer((HOST, PORT), NFCGateClientHandler, plugins, tls_options)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log_with_context("Server interrupted by user, shutting down", logging.INFO)
        server.shutdown()
    except Exception as e:
        log_with_context(f"Server crashed: {str(e)}", logging.CRITICAL)

if __name__ == "__main__":
    main()