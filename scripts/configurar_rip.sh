#!/bin/bash
# configurar_rip.sh
# Configura RIPv2 em todos os 5 roteadores, anunciando as redes
# diretamente conectadas de cada um (acesso + links com vizinhos).

set -e

echo "==> Configurando RIP no r1..."
sudo vtysh -N r1 \
  -c "configure terminal" \
  -c "router rip" \
  -c "version 2" \
  -c "network 10.1.1.0/24" \
  -c "network 10.2.12.0/30" \
  -c "network 10.2.51.0/30" \
  -c "network 10.2.13.0/30" \
  -c "end" \
  -c "write memory"

echo "==> Configurando RIP no r2..."
sudo vtysh -N r2 \
  -c "configure terminal" \
  -c "router rip" \
  -c "version 2" \
  -c "network 10.1.2.0/24" \
  -c "network 10.2.12.0/30" \
  -c "network 10.2.23.0/30" \
  -c "end" \
  -c "write memory"

echo "==> Configurando RIP no r3..."
sudo vtysh -N r3 \
  -c "configure terminal" \
  -c "router rip" \
  -c "version 2" \
  -c "network 10.1.3.0/24" \
  -c "network 10.2.23.0/30" \
  -c "network 10.2.34.0/30" \
  -c "network 10.2.13.0/30" \
  -c "end" \
  -c "write memory"

echo "==> Configurando RIP no r4..."
sudo vtysh -N r4 \
  -c "configure terminal" \
  -c "router rip" \
  -c "version 2" \
  -c "network 10.1.4.0/24" \
  -c "network 10.2.34.0/30" \
  -c "network 10.2.45.0/30" \
  -c "end" \
  -c "write memory"

echo "==> Configurando RIP no r5..."
sudo vtysh -N r5 \
  -c "configure terminal" \
  -c "router rip" \
  -c "version 2" \
  -c "network 10.1.5.0/24" \
  -c "network 10.2.45.0/30" \
  -c "network 10.2.51.0/30" \
  -c "end" \
  -c "write memory"

echo ""
echo "==> RIP configurado em todos os roteadores!"
echo "    Aguarde ~30s para convergencia e confira com:"
echo "    sudo vtysh -N r1 -c 'show ip route rip'"
