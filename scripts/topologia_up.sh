#!/bin/bash
# topologia_up.sh
# Cria a topologia de 5 roteadores (r1-r5) em anel + diagonal (r1-r3),
# cada um com uma rede de acesso e um host (h1-h5).
# Inicia uma instância isolada do FRR (mgmtd + zebra + ripd) em cada roteador.

set -e

echo "==> Criando namespaces dos roteadores..."
for r in r1 r2 r3 r4 r5; do
    sudo ip netns add $r
done

echo "==> Criando namespaces dos hosts..."
for h in h1 h2 h3 h4 h5; do
    sudo ip netns add $h
done

echo "==> Ativando loopback em todos os namespaces..."
for ns in r1 r2 r3 r4 r5 h1 h2 h3 h4 h5; do
    sudo ip netns exec $ns ip link set lo up
done

echo "==> Habilitando IP forwarding nos roteadores..."
for r in r1 r2 r3 r4 r5; do
    sudo ip netns exec $r sysctl -w net.ipv4.ip_forward=1 > /dev/null
done

# ---------------------------------------------------------
# Links entre roteadores (anel + diagonal), redes /30
# ---------------------------------------------------------
declare -A ROUTER_LINKS=(
    ["r1-r2"]="10.2.12.1/30 10.2.12.2/30"
    ["r2-r3"]="10.2.23.1/30 10.2.23.2/30"
    ["r3-r4"]="10.2.34.1/30 10.2.34.2/30"
    ["r4-r5"]="10.2.45.1/30 10.2.45.2/30"
    ["r5-r1"]="10.2.51.1/30 10.2.51.2/30"
    ["r1-r3"]="10.2.13.1/30 10.2.13.2/30"
)

echo "==> Criando links entre roteadores..."
for link in "${!ROUTER_LINKS[@]}"; do
    A=$(echo $link | cut -d'-' -f1)
    B=$(echo $link | cut -d'-' -f2)
    IPS=(${ROUTER_LINKS[$link]})
    IP_A=${IPS[0]}
    IP_B=${IPS[1]}

    VETH_A="veth-${A}${B}"
    VETH_B="veth-${B}${A}"

    sudo ip link add $VETH_A type veth peer name $VETH_B
    sudo ip link set $VETH_A netns $A
    sudo ip link set $VETH_B netns $B

    sudo ip netns exec $A ip addr add $IP_A dev $VETH_A
    sudo ip netns exec $B ip addr add $IP_B dev $VETH_B
    sudo ip netns exec $A ip link set $VETH_A up
    sudo ip netns exec $B ip link set $VETH_B up

    echo "    $A ($IP_A) <-> $B ($IP_B)"
done

# ---------------------------------------------------------
# Links roteador-host (redes de acesso /24)
# ---------------------------------------------------------
declare -A ACCESS_LINKS=(
    ["r1-h1"]="10.1.1.1/24 10.1.1.2/24"
    ["r2-h2"]="10.1.2.1/24 10.1.2.2/24"
    ["r3-h3"]="10.1.3.1/24 10.1.3.2/24"
    ["r4-h4"]="10.1.4.1/24 10.1.4.2/24"
    ["r5-h5"]="10.1.5.1/24 10.1.5.2/24"
)

echo "==> Criando redes de acesso (roteador-host)..."
for link in "${!ACCESS_LINKS[@]}"; do
    R=$(echo $link | cut -d'-' -f1)
    H=$(echo $link | cut -d'-' -f2)
    IPS=(${ACCESS_LINKS[$link]})
    IP_R=${IPS[0]}
    IP_H=${IPS[1]}

    VETH_R="veth-${R}${H}"
    VETH_H="veth-${H}${R}"

    sudo ip link add $VETH_R type veth peer name $VETH_H
    sudo ip link set $VETH_R netns $R
    sudo ip link set $VETH_H netns $H

    sudo ip netns exec $R ip addr add $IP_R dev $VETH_R
    sudo ip netns exec $H ip addr add $IP_H dev $VETH_H
    sudo ip netns exec $R ip link set $VETH_R up
    sudo ip netns exec $H ip link set $VETH_H up

    # gateway padrao do host aponta para o roteador
    GW=$(echo $IP_R | cut -d'/' -f1)
    sudo ip netns exec $H ip route add default via $GW

    echo "    $R ($IP_R) <-> $H ($IP_H), gateway do host: $GW"
done

# ---------------------------------------------------------
# Inicia instancias FRR isoladas em cada roteador
# ---------------------------------------------------------
echo "==> Iniciando FRR (mgmtd + zebra + ripd) em cada roteador..."
for r in r1 r2 r3 r4 r5; do
    sudo mkdir -p /etc/frr/$r
    sudo chown frr:frr /etc/frr/$r

    sudo ip netns exec $r /usr/lib/frr/mgmtd -d -N $r
    sudo ip netns exec $r /usr/lib/frr/zebra -d -N $r
    sudo ip netns exec $r /usr/lib/frr/ripd  -d -N $r
    sudo ip netns exec $r /usr/lib/frr/ospfd -d -N $r

    echo "    FRR iniciado em $r"
done

echo ""
echo "==> Topologia criada com sucesso!"
echo "    Conecte-se a um roteador com: sudo vtysh -N r1  (por exemplo)"
