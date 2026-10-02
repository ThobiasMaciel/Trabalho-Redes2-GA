#!/usr/bin/env python3
"""
routing_daemon.py
Daemon do algoritmo proprio ("RIP com backup rapido").
Roda DENTRO de um namespace de roteador (via ip netns exec).

Uso:
    sudo ip netns exec r1 python3 routing_daemon.py --config r1.json

O arquivo de config (JSON) descreve: o id do roteador, suas redes
diretamente conectadas e seus vizinhos (com o IP do link ponto-a-ponto).
"""

import argparse
import json
import socket
import threading
import time

from pyroute2 import IPRoute
from routing_logic import RoutingTable

UDP_PORT = 5000
HELLO_INTERVAL = 1.0      
UPDATE_INTERVAL = 5.0     
HELLO_TIMEOUT = 3.0       


class RoutingDaemon:
    def __init__(self, config_path):
        with open(config_path) as f:
            cfg = json.load(f)

        self.router_id = cfg["router_id"]
        self.neighbors = cfg["neighbors"]  # {vizinho_id: {"my_ip": ..., "neighbor_ip": ...}}
        self.table = RoutingTable(self.router_id)

        for net in cfg["direct_networks"]:
            self.table.add_direct_network(net)

        self.last_hello = {n: time.time() for n in self.neighbors}
        self.lock = threading.Lock()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", UDP_PORT))

        self.ipr = IPRoute()
        self.installed_routes = {}  # destino -> gateway atualmente instalado no kernel

    # ---------------- comunicacao ----------------

    def send(self, neighbor_id, message):
        ip = self.neighbors[neighbor_id]["neighbor_ip"]
        data = json.dumps(message).encode()
        try:
            self.sock.sendto(data, (ip, UDP_PORT))
        except OSError:
            pass

    def broadcast_hello(self):
        while True:
            for n in self.neighbors:
                self.send(n, {"type": "hello", "origin": self.router_id})
            time.sleep(HELLO_INTERVAL)

    def broadcast_updates(self):
        while True:
            vector = self.build_vector()
            for n in self.neighbors:
                # split horizon: nao reanuncia pro vizinho de quem a rota principal veio
                filtered = {
                    dest: routes["principal"].cost
                    for dest, routes in self.table.table.items()
                    if routes["principal"].next_hop != n and routes["principal"].cost < 16
                }
                self.send(n, {"type": "update", "origin": self.router_id, "routes": filtered})
            time.sleep(UPDATE_INTERVAL)

    def build_vector(self):
        return {
            dest: routes["principal"].cost
            for dest, routes in self.table.table.items()
            if routes["principal"].cost < 16
        }

    def listen(self):
        while True:
            data, _ = self.sock.recvfrom(65535)
            try:
                msg = json.loads(data.decode())
            except ValueError:
                continue

            origin = msg.get("origin")
            if origin not in self.neighbors:
                continue

            with self.lock:
                self.last_hello[origin] = time.time()

                if msg["type"] == "update":
                    changed = self.table.update_from_vector(origin, msg["routes"])
                    if changed:
                        self.apply_routes()
                        print(f"[{self.router_id}] rotas atualizadas apos update de {origin}")

    # ---------------- deteccao de falha ----------------

    def watch_neighbors(self):
        while True:
            time.sleep(0.5)
            now = time.time()
            with self.lock:
                for n, last in list(self.last_hello.items()):
                    if now - last > HELLO_TIMEOUT:
                        print(f"[{self.router_id}] vizinho {n} nao responde -> tratando como morto")
                        changed = self.table.handle_neighbor_failure(n)
                        if changed:
                            self.apply_routes()
                        # evita disparar de novo repetidamente pro mesmo vizinho
                        self.last_hello[n] = now

    # ---------------- aplicacao no kernel ----------------

    def apply_routes(self):
        for dest, routes in self.table.table.items():
            principal = routes["principal"]

            if principal.next_hop in (None, "DIRECT"):
                # sem rota valida (ou rede local, que ja esta na tabela do kernel por si so)
                if dest in self.installed_routes:
                    self._remove_route(dest)
                continue

            gateway = self.neighbors.get(principal.next_hop, {}).get("neighbor_ip")
            if not gateway:
                continue

            if self.installed_routes.get(dest) == gateway:
                continue  # ja esta instalada corretamente, nada a fazer

            self._remove_route(dest)
            try:
                self.ipr.route("replace", dst=dest, gateway=gateway)
                self.installed_routes[dest] = gateway
                print(f"[{self.router_id}] rota {dest} -> via {gateway} ({principal.next_hop})")
            except Exception as e:
                print(f"[{self.router_id}] erro ao instalar rota {dest}: {e}")

    def _remove_route(self, dest):
        try:
            self.ipr.route("del", dst=dest)
        except Exception:
            pass
        self.installed_routes.pop(dest, None)

    # ---------------- loop principal ----------------

    def run(self):
        print(f"[{self.router_id}] iniciando daemon de roteamento proprio...")
        threading.Thread(target=self.broadcast_hello, daemon=True).start()
        threading.Thread(target=self.broadcast_updates, daemon=True).start()
        threading.Thread(target=self.watch_neighbors, daemon=True).start()
        self.listen()  # thread principal fica ouvindo


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Arquivo JSON de configuracao do roteador")
    args = parser.parse_args()

    daemon = RoutingDaemon(args.config)
    daemon.run()
