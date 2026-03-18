import time
import requests
from pythonping import ping
from tabulate import tabulate
import socket
from datetime import datetime
from colorama import init, Fore, Style
import csv
import os

init(autoreset=True)

ENDPOINTS = [
    {
        "name": "GenLayer Studio Public RPC (/api)",
        "host": "studio.genlayer.com",
        "port": 443,
        "path": "/api",
        "type": "https",
        "rpc": True
    },
    {
        "name": "GenLayer Studio Root (Basic Health)",
        "host": "studio.genlayer.com",
        "port": 443,
        "path": "/",
        "type": "https"
    },
]

def tcp_ping(host, port, timeout=2):
    start = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        latency = (time.time() - start) * 1000
        return round(latency, 2), "Alive"
    except Exception as e:
        return None, f"Down ({str(e)[:30]})"

def http_ping(url, timeout=5):
    start = time.time()
    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "GenLayer-Ping-Monitor"})
        latency = (time.time() - start) * 1000
        status = f"OK ({response.status_code})" if response.status_code == 200 else f"Error {response.status_code}"
        return round(latency, 2), status
    except Exception as e:
        return None, f"Down ({str(e)[:30]})"

def genlayer_rpc_health_check(rpc_url):
    payloads = [
        {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
        {"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1},
        {"jsonrpc": "2.0", "method": "gen_dbg_ping", "params": [], "id": 1},
    ]

    start = time.time()
    for payload in payloads:
        try:
            response = requests.post(rpc_url, json=payload, timeout=5, headers={
                "User-Agent": "GenLayer-Ping-Monitor",
                "Content-Type": "application/json"
            })
            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                try:
                    data = response.json()
                    if "result" in data:
                        result_val = data["result"]
                        method = payload["method"]

                        if method == "eth_blockNumber":
                            return round(latency, 2), f"Alive (block: {result_val})"
                        elif method == "eth_chainId":
                            return round(latency, 2), f"Alive (chainId: {result_val})"
                        elif method == "gen_dbg_ping" and result_val == "pong":
                            return round(latency, 2), "Pong OK"
                        else:
                            return round(latency, 2), f"OK ({method} → {result_val})"
                    elif "error" in data:
                        err_msg = data["error"].get("message", "Unknown error")
                        return round(latency, 2), f"RPC error ({err_msg})"
                    else:
                        return round(latency, 2), "RPC OK (no result)"
                except ValueError:
                    return round(latency, 2), "RPC OK (non-JSON)"
            else:
                return round(latency, 2), f"HTTP {response.status_code}"
        except Exception:
            continue

    return None, "Down (all methods failed)"

def monitor():
    results = []
    csv_rows = []

    for ep in ENDPOINTS:
        host = ep["host"]
        path = ep["path"]
        typ = ep["type"]

        if ep.get("rpc", False):
            rpc_url = f"{typ}://{host}{path}"
            latency, status = genlayer_rpc_health_check(rpc_url)
        else:
            base_url = f"{typ}://{host}{path}"
            latency, status = http_ping(base_url)

        icmp_result = ping(host, count=2, timeout=2)
        icmp_latency = round(icmp_result.rtt_avg_ms, 2) if icmp_result.success() else "N/A"

        colored_status = status
        if "Alive" in status or "Pong" in status or "OK" in status:
            colored_status = Fore.GREEN + status + Style.RESET_ALL
        elif "Down" in status or "error" in status.lower():
            colored_status = Fore.RED + status + Style.RESET_ALL

        results.append([
            ep["name"],
            host,
            f"{latency} ms" if latency is not None else "N/A",
            icmp_latency,
            colored_status,
            datetime.now().strftime("%H:%M:%S")
        ])

        csv_rows.append([
            ep["name"],
            host,
            latency if latency is not None else "N/A",
            icmp_latency,
            status,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])

    print("\033c", end="")
    print("=== GenLayer Global Ping Monitor ===")
    print(f"Monitoring from: Ivano-Frankivsk, UA | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(tabulate(results, headers=["Endpoint", "Host", "Latency (ms)", "ICMP (ms)", "Status", "Last Check"], tablefmt="grid"))
    print("\nCtrl+C to exit. Refresh every 30 seconds.")

    csv_file = "genlayer_ping_log.csv"
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Endpoint", "Host", "Latency_ms", "ICMP_ms", "Status", "Timestamp"])
        writer.writerows(csv_rows)

    print(Fore.CYAN + f"Saved to {csv_file}" + Style.RESET_ALL)

if __name__ == "__main__":
    print("Starting GenLayer Ping Monitor")
    try:
        while True:
            monitor()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n" + Fore.YELLOW + "Stopped by user." + Style.RESET_ALL)