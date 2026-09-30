# Trabalho 1 — Roteamento IP: RIP, OSPF e Algoritmo Próprio

**Disciplina:** Fundamentos de Sistemas Operacionais — UNISINOS
**Professor:** Cristiano Bonato Both
**Autores:** Thobias Ferreira Maciel e [nome da dupla]

## Objetivo

Investigar, na prática, o funcionamento do roteamento IP construindo um ambiente experimental onde diferentes protocolos de roteamento (RIP, OSPF) e um algoritmo de roteamento próprio são configurados, observados e comparados sobre a mesma topologia.

## Plataforma utilizada

**FRRouting (FRR)** — sucessor ativo do Quagga (citado no enunciado como plataforma de referência). Cada roteador da topologia roda como um processo FRR isolado, dentro de um [network namespace](https://man7.org/linux/man-pages/man7/network_namespaces.7.html) do Linux, simulando roteadores independentes numa única máquina.

## Topologia

5 roteadores (R1 a R5) conectados em **anel + 1 diagonal**, garantindo múltiplos caminhos entre pontos da rede. Cada roteador tem uma rede de acesso própria com um host conectado.

```
        R1
       /  \
      /    \
    R5      R2
    |        |
    |        |
    R4------R3

Diagonal extra: R1 -- R3
```

**Redes de acesso (roteador ↔ host), /24:**
| Roteador | Rede | Host |
|---|---|---|
| R1 | 10.1.1.0/24 | h1 (10.1.1.2) |
| R2 | 10.1.2.0/24 | h2 (10.1.2.2) |
| R3 | 10.1.3.0/24 | h3 (10.1.3.2) |
| R4 | 10.1.4.0/24 | h4 (10.1.4.2) |
| R5 | 10.1.5.0/24 | h5 (10.1.5.2) |

**Links entre roteadores, /30:**
| Link | Rede |
|---|---|
| R1 ↔ R2 | 10.2.12.0/30 |
| R2 ↔ R3 | 10.2.23.0/30 |
| R3 ↔ R4 | 10.2.34.0/30 |
| R4 ↔ R5 | 10.2.45.0/30 |
| R5 ↔ R1 | 10.2.51.0/30 |
| R1 ↔ R3 (diagonal) | 10.2.13.0/30 |

## Estrutura do repositório

```
/scripts
  topologia_up.sh       -> cria toda a topologia (namespaces, links, FRR)
  topologia_down.sh     -> desfaz a topologia
  configurar_rip.sh     -> configura RIPv2 nos 5 roteadores
  remover_rip.sh        -> remove a configuração RIP (antes de testar OSPF)
  configurar_ospf.sh    -> configura OSPF (area 0) nos 5 roteadores
  routing_logic.py      -> lógica do algoritmo próprio (tabela de rotas, principal/backup)
  routing_daemon.py     -> daemon que roda em cada roteador: comunicação UDP,
                            detecção de falha via Hello, aplica rotas no kernel
  r1.json ... r5.json   -> configuração de cada roteador para o algoritmo próprio
/metrics
  metricas_coletadas.csv -> métricas comparativas dos 3 sistemas
  *.pcap                 -> capturas de tráfego de controle de cada protocolo
/docs
  (prints e evidências)
```

## Como usar

### Pré-requisitos
```bash
sudo apt install frr frr-pythontools
pip install pyroute2 --break-system-packages
```

### 1. Criar o ambiente
```bash
cd scripts
sudo ./topologia_up.sh
```
Isso cria os 10 namespaces (5 roteadores + 5 hosts), os 11 links, habilita IP forwarding e inicia uma instância isolada do FRR (mgmtd + zebra + ripd + ospfd) em cada roteador.

### 2. Testar RIP
```bash
sudo ./configurar_rip.sh
sleep 30
sudo vtysh -N r1 -c "show ip route rip"
```

### 3. Testar OSPF
```bash
sudo ./remover_rip.sh
sudo ./configurar_ospf.sh
sleep 30
sudo vtysh -N r1 -c "show ip ospf neighbor"
sudo vtysh -N r1 -c "show ip route ospf"
```

### 4. Testar o algoritmo próprio
Primeiro, remova o OSPF (`no router ospf` em cada roteador via vtysh), depois inicie um daemon por roteador, cada um em um terminal:
```bash
sudo ip netns exec r1 python3 ../routing_daemon.py --config r1.json
sudo ip netns exec r2 python3 ../routing_daemon.py --config r2.json
sudo ip netns exec r3 python3 ../routing_daemon.py --config r3.json
sudo ip netns exec r4 python3 ../routing_daemon.py --config r4.json
sudo ip netns exec r5 python3 ../routing_daemon.py --config r5.json
```

### 5. Testar conectividade
```bash
sudo ip netns exec h1 ping 10.1.4.2
```

### 6. Desfazer o ambiente
```bash
sudo ./topologia_down.sh
```

## O algoritmo próprio: "RIP com backup rápido"

**Motivação:** RIP e OSPF, ao perderem um link, precisam recalcular a rota — RIP espera um timeout de até 180s, OSPF reage mais rápido mas ainda depende de um Dead Timer. A ideia do algoritmo proposto é manter **duas rotas por destino** (principal e backup, com next-hops diferentes) já calculadas, permitindo troca **imediata** assim que uma falha é detectada.

**Lógica de funcionamento:**
1. Cada roteador troca vetores de distância com vizinhos (como RIP), com split horizon para evitar loops.
2. Para cada destino, mantém a **melhor rota (principal)** e a **segunda melhor com next-hop diferente (backup)**.
3. Critério de seleção: menor número de saltos.
4. Detecção de falha: mensagens **Hello** a cada 1s entre vizinhos diretos; se não houver resposta por 3s, o vizinho é considerado morto.
5. Ao detectar falha, a rota backup é **promovida a principal instantaneamente**, sem esperar nova rodada de cálculo.
6. As rotas escolhidas são aplicadas diretamente na tabela de rotas do kernel Linux via `pyroute2`.

## Resultados comparativos

Ver `metrics/metricas_coletadas.csv` para os dados completos. Resumo:

| Métrica | RIP | OSPF | Algoritmo próprio |
|---|---|---|---|
| Tamanho da tabela (r1) | 7 rotas | 7 rotas | 4 rotas* |
| Pacotes de controle (60s) | 4 | 12 | 142 |
| Taxa de transmissão de controle | ~11,5 B/s | ~13,6 B/s | ~155 B/s |
| Tempo de convergência (teste real) | ~4s | <1s | ~3,5s |

*O algoritmo próprio anuncia apenas as redes de acesso, não as sub-redes de trânsito entre roteadores — por isso o número de rotas é menor, sem impacto na conectividade fim-a-fim.

**Principal conclusão:** o algoritmo proposto não superou o OSPF em velocidade de convergência no teste realizado, mas demonstrou o mecanismo de rota backup funcionando corretamente — a limitação observada (~3,5s) é determinada pelo parâmetro `HELLO_TIMEOUT`, que poderia ser reduzido às custas de maior overhead de controle (já a métrica mais alta entre os três sistemas testados). Isso evidencia o trade-off central de protocolos de roteamento: velocidade de detecção de falha versus tráfego de controle gerado.

## Uso de Inteligência Artificial

Ferramenta utilizada: Claude (Anthropic), como apoio ao longo de todas as etapas — desde o planejamento da topologia e do ambiente (namespaces + FRR) até a implementação da camada de comunicação de rede do algoritmo próprio (routing_daemon.py) e a investigação de resultados inesperados durante os testes. Todas as configurações foram executadas e validadas no ambiente real; hipóteses sugeridas (como o comportamento esperado de convergência) foram testadas e, quando o resultado divergiu do esperado, investigadas com evidências reais (ex.: o primeiro teste de convergência via desligamento de interface mostrou 0% de perda por interferência do kernel Linux, não do protocolo — isso foi identificado e um segundo teste, bloqueando apenas o tráfego de controle via iptables, foi necessário para isolar o comportamento real de cada protocolo).

