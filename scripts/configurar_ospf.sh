#!/bin/bash
# configurar_ospf.sh
# Configura OSPF (area 0) em todos os 5 roteadores.

set -e

echo "==> Configurando OSPF no r1..."
sudo vtysh -N r1 \
  -c "configure terminal" \
  -c "router ospf" \
  -c "network 10.1.1.0/24 area 0" \
  -c "network 10.2.12.0/30 area 0" \
  -c "network 10.2.51.0/30 area 0" \
  -c "network 10.2.13.0/30 area 0" \
  -c "end" \
  -c "write memory"

echo "==> Configurando OSPF no r2..."
sudo vtysh -N r2 \
  -c "configure terminal" \
  -c "router ospf" \
  -c "network 10.1.2.0/24 area 0" \
  -c "network 10.2.12.0/30 area 0" \
  -c "network 10.2.23.0/30 area 0" \
  -c "end" \
  -c "write memory"

echo "==> Configurando OSPF no r3..."
sudo vtysh -N r3 \
  -c "configure terminal" \
  -c "router ospf" \
  -c "network 10.1.3.0/24 area 0" \
  -c "network 10.2.23.0/30 area 0" \
  -c "network 10.2.34.0/30 area 0" \
  -c "network 10.2.13.0/30 area 0" \
  -c "end" \
  -c "write memory"

echo "==> Configurando OSPF no r4..."
sudo vtysh -N r4 \
  -c "configure terminal" \
  -c "router ospf" \
  -c "network 10.1.4.0/24 area 0" \
  -c "network 10.2.34.0/30 area 0" \
  -c "network 10.2.45.0/30 area 0" \
  -c "end" \
  -c "write memory"

echo "==> Configurando OSPF no r5..."
sudo vtysh -N r5 \
  -c "configure terminal" \
  -c "router ospf" \
  -c "network 10.1.5.0/24 area 0" \
  -c "network 10.2.45.0/30 area 0" \
  -c "network 10.2.51.0/30 area 0" \
  -c "end" \
  -c "write memory"

echo ""
echo "==> OSPF configurado em todos os roteadores!"
