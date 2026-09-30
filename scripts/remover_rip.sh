#!/bin/bash
# remover_rip.sh
# Remove a configuracao RIP de todos os 5 roteadores (usar antes de configurar OSPF).

set -e

for r in r1 r2 r3 r4 r5; do
    echo "==> Removendo RIP do $r..."
    sudo vtysh -N $r -c "configure terminal" -c "no router rip" -c "end" -c "write memory"
done

echo ""
echo "==> RIP removido de todos os roteadores."
