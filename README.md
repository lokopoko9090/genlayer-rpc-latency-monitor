# genlayer-rpc-latency-monitor
GenLayer Public RPC Latency Monitor from Ukraine
# GenLayer Public RPC Latency & Health Monitor

A simple open-source tool to monitor latency, ICMP ping and health of GenLayer's public Studio RPC (`https://studio.genlayer.com/api`).

### Features
- Checks `eth_blockNumber` (proves the network is alive and producing blocks)
- Measures real HTTP latency + ICMP ping
- Logs all data to `genlayer_ping_log.csv`
- Auto-refreshes every 30 seconds with colorful output

### Results from Ivano-Frankivsk, Ukraine (March 18, 2026)
- **RPC Latency**: 400–810 ms (typically 500–600 ms)
- **ICMP Ping**: stable 16–17 ms
- Network is active — new blocks every ~30 seconds

### Installation & Run
```bash
pip install requests pythonping tabulate colorama
python genlayer_ping_monitor.py
