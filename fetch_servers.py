"""
fetch_servers.py
Запускается GitHub Actions каждые 6 часов.
Качает список серверов VPNGate и сохраняет в servers.json.
"""

import csv
import io
import json
import ssl
import sys
import urllib.request
from datetime import datetime, timezone

SOURCES = [
    "http://www.vpngate.net/api/iphone/",
    "https://www.vpngate.net/api/iphone/",
    "http://122.249.238.67/api/iphone/",
]

SSL_NO_VERIFY = ssl.create_default_context()
SSL_NO_VERIFY.check_hostname = False
SSL_NO_VERIFY.verify_mode    = ssl.CERT_NONE


def parse(raw: str) -> list[dict]:
    lines = [
        l for l in raw.splitlines()
        if not l.startswith("*") and l.strip()
    ]

    if len(lines) < 2:
        raise ValueError("Пустой ответ")

    reader = csv.DictReader(
        io.StringIO("\n".join(lines))
    )

    servers = []

    for row in reader:

        ip = (
            row.get("IP")
            or row.get("IP Address")
            or ""
        ).strip()


        tcp_raw = (
            row.get("TCP Port")
            or row.get("TCPPort")
            or ""
        ).strip()


        tcp_port = next(
            (
                int(p.strip())
                for p in tcp_raw.split(",")
                if p.strip().isdigit()
            ),
            443
        )


        country = (
            row.get("CountryLong")
            or row.get("Country")
            or "?"
        ).strip()


        speed = (
            row.get("Speed")
            or "0"
        ).strip()


        sessions = (
            row.get("NumVpnSessions")
            or "?"
        ).strip()


        ping = (
            row.get("Ping")
            or "?"
        ).strip()



        if ip:

            servers.append(
                {
                    "ip": ip,
                    "port": tcp_port,
                    "country": country,
                    "speed": speed,
                    "sessions": sessions,
                    "ping": ping,
                }
            )


    return servers

def main():
    servers = None
    for url in SOURCES:
        print(f"Пробую: {url}")
        try:
            raw = fetch_raw(url)
            if "#HostName" in raw or "*vpn_servers" in raw:
                servers = parse(raw)
                print(f"✓ Загружено {len(servers)} серверов с {url}")
                break
        except Exception as e:
            print(f"  ✗ {e}")

    if not servers:
        print("Все источники недоступны — выход без изменений")
        sys.exit(1)

    out = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count":      len(servers),
        "servers":    servers,
    }
    with open("servers.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Сохранено в servers.json ({len(servers)} серверов)")


if __name__ == "__main__":
    main()
