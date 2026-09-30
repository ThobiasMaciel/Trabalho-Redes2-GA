#!/bin/bash
# topologia_down.sh
# Remove todos os namespaces e processos FRR criados por topologia_up.sh

echo "==> Encerrando processos FRR..."
for r in r1 r2 r3 r4 r5; do
    sudo pkill -f "\-N $r" 2>/dev/null || true
done

sleep 1

echo "==> Removendo namespaces..."
for ns in r1 r2 r3 r4 r5 h1 h2 h3 h4 h5; do
    sudo ip netns del $ns 2>/dev/null || true
done

echo "==> Limpeza concluida."
