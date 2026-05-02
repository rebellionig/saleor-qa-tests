import requests
import subprocess
import time

API_URL = "http://localhost:8000/graphql/"

QUERY = '{"query": "{ products(first: 5, channel: \\"default-channel\\") { edges { node { id } } } }"}'
HEADERS = {"Content-Type": "application/json"}


def check_api(label):
    try:
        r = requests.post(API_URL, data=QUERY, headers=HEADERS, timeout=5)
        print(f"[{label}] Status: {r.status_code} | Response time: {r.elapsed.total_seconds():.3f}s")
        return r.status_code
    except requests.exceptions.ConnectionError:
        print(f"[{label}] UNAVAILABLE — Connection refused")
        return None
    except requests.exceptions.Timeout:
        print(f"[{label}] TIMEOUT — No response in 5s")
        return None


def run_chaos(container, stop_seconds=15):
    print(f"\n{'='*50}")
    print(f"CHAOS: Stopping {container} for {stop_seconds}s")
    print(f"{'='*50}")

    print("\n[BEFORE FAULT]")
    check_api("baseline")

    print(f"\n[INJECTING FAULT] docker stop {container}")
    subprocess.run(["docker", "stop", container], capture_output=True)
    time.sleep(2)

    print("\n[DURING FAULT]")
    for i in range(3):
        check_api(f"fault t+{(i+1)*2}s")
        time.sleep(2)

    print(f"\n[RECOVERING] docker start {container}")
    start_time = time.time()
    subprocess.run(["docker", "start", container], capture_output=True)

    print("\n[RECOVERY MONITORING]")
    recovered = False
    for i in range(10):
        time.sleep(3)
        status = check_api(f"recovery t+{(i+1)*3}s")
        if status == 200 and not recovered:
            recovery_time = time.time() - start_time
            print(f"  ✓ RECOVERED in {recovery_time:.1f}s")
            recovered = True
            break

    if not recovered:
        print("  ✗ NOT recovered within 30s")


if __name__ == "__main__":
    print("=== CHAOS TESTING — Saleor Platform ===\n")

    # Scenario 1: DB failure
    run_chaos("saleor-platform-db-1", stop_seconds=15)
    time.sleep(5)

    # Scenario 2: Cache failure
    run_chaos("saleor-platform-cache-1", stop_seconds=15)
    time.sleep(5)

    print("\n=== CHAOS TESTING COMPLETE ===")