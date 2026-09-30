INFINITY = 16  # Evitar loops infinitos.

class RouteEntry:
    def __init__(self, next_hop=None, cost=INFINITY):
        self.next_hop = next_hop
        self.cost = cost


class RoutingTable:
    def __init__(self, router_id):
        self.router_id = router_id
        self.table = {}  # {destino: {"principal": RouteEntry, "backup": RouteEntry}}
        self.neighbors_alive = {}

    def add_direct_network(self, network_prefix):
        self.table[network_prefix] = {
            "principal": RouteEntry(next_hop="DIRECT", cost=0),
            "backup": RouteEntry(next_hop=None, cost=INFINITY)
        }

    def update_from_vector(self, neighbor_id, vector):
        changed = False
        for destination, reported_cost in vector.items():
            new_cost = reported_cost + 1
            if new_cost >= INFINITY:
                continue

            if destination not in self.table:
                self.table[destination] = {
                    "principal": RouteEntry(next_hop=neighbor_id, cost=new_cost),
                    "backup": RouteEntry(next_hop=None, cost=INFINITY)
                }
                changed = True
                continue

            routes = self.table[destination]
            principal = routes["principal"]
            backup = routes["backup"]

            if principal.next_hop == "DIRECT":
                continue

            if principal.next_hop == neighbor_id:
                if principal.cost != new_cost:
                    principal.cost = new_cost
                    changed = True
                if backup.next_hop is not None and principal.cost > backup.cost:
                    routes["principal"], routes["backup"] = backup, principal
                    changed = True

            elif backup.next_hop == neighbor_id:
                backup.cost = new_cost
                if backup.cost < principal.cost:
                    routes["principal"], routes["backup"] = backup, principal
                    changed = True

            else:
                if new_cost < principal.cost:
                    routes["backup"] = principal
                    routes["principal"] = RouteEntry(next_hop=neighbor_id, cost=new_cost)
                    changed = True
                elif new_cost < backup.cost:
                    routes["backup"] = RouteEntry(next_hop=neighbor_id, cost=new_cost)
                    changed = True

        return changed

    def handle_neighbor_failure(self, dead_neighbor):
        changed = False
        for destination, routes in self.table.items():
            principal = routes["principal"]
            backup = routes["backup"]

            if principal.next_hop == dead_neighbor:
                if backup.next_hop is not None and backup.cost < INFINITY:
                    routes["principal"] = backup
                    routes["backup"] = RouteEntry(next_hop=None, cost=INFINITY)
                else:
                    routes["principal"] = RouteEntry(next_hop=None, cost=INFINITY)
                changed = True
            elif backup.next_hop == dead_neighbor:
                routes["backup"] = RouteEntry(next_hop=None, cost=INFINITY)
                changed = True
        return changed

    def print_table(self):
        print(f"\nTabela de Roteamento de [{self.router_id.upper()}]")
        print(f"{'Destino':<16} | {'Principal':<26} | {'Backup':<26}")
        for dest, routes in self.table.items():
            p = routes["principal"]
            b = routes["backup"]
            p_str = f"via {p.next_hop} (custo {p.cost})" if p.next_hop and p.cost < INFINITY else "Inalcancavel"
            b_str = f"via {b.next_hop} (custo {b.cost})" if b.next_hop and b.cost < INFINITY else "Nenhum"
            print(f"{dest:<16} | {p_str:<26} | {b_str:<26}")
