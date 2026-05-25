#!/usr/bin/env python3
"""
Reverse IP Lookup with Tor
============================
Modern concurrent reverse IP scanner using HackerTarget and ViewDNS APIs
with automatic Tor circuit rotation on rate limits.
"""

from __future__ import annotations

import argparse
import re
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

# ANSI color codes (no external dependency)
C_RED = "\033[31m"
C_GREEN = "\033[32m"
C_BLUE = "\033[34m"
C_YELLOW = "\033[33m"
C_RESET = "\033[0m"

_CLEAN_PREFIXES = (
    "webdisk.", "cpanel.", "autodiscover.", "cpcalendars.",
    "cpcontacts.", "webmail.", "mail.",
)


def _log_info(msg: str) -> None:
    print(f"{C_BLUE}[*]{C_RESET} {msg}")


def _log_success(msg: str) -> None:
    print(f"{C_GREEN}[+]{C_RESET} {msg}")


def _log_error(msg: str) -> None:
    print(f"{C_RED}[-]{C_RESET} {msg}", file=sys.stderr)


def _start_tor() -> None:
    try:
        subprocess.run(["service", "tor", "start"], check=False, capture_output=True)
        time.sleep(3)
        _log_info("Tor service started")
    except FileNotFoundError:
        _log_error("Could not start tor. Ensure tor is installed and in PATH.")


def _reload_tor() -> None:
    try:
        subprocess.run(["service", "tor", "reload"], check=False, capture_output=True)
        time.sleep(2)
    except FileNotFoundError:
        pass


def _create_session(proxy: str) -> requests.Session:
    session = requests.Session()
    session.proxies.update({"http": proxy, "https": proxy})
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    return session


def _reverse_hackertarget(
    session: requests.Session, ip: str, timeout: int, max_retries: int
) -> list[str]:
    url = f"https://api.hackertarget.com/reverseiplookup/?q={ip}"
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, timeout=timeout)
            text = resp.text
            if "No DNS" in text:
                return []
            if "API count" in text or "429 Too Many" in text or resp.status_code == 429:
                _log_error(f"HT rate limited ({ip}), rotating Tor... ({attempt}/{max_retries})")
                _reload_tor()
                continue
            domains = [d.strip() for d in text.splitlines() if d.strip()]
            _log_success(f"HT | {ip} => {len(domains)} domains")
            return domains
        except requests.RequestException as exc:
            _log_error(f"HT request error ({ip}): {exc}")
            time.sleep(2)
    return []


def _reverse_viewdns(
    session: requests.Session, ip: str, timeout: int, max_retries: int
) -> list[str]:
    url = f"https://viewdns.com/reverse-ip-lookup/{ip}"
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, timeout=timeout)
            text = resp.text
            if "We found" in text:
                domains = re.findall(
                    r'<a href="https://viewdns\.com/view-dns-records/(.*?)">', text
                )
                _log_success(f"ViewDns | {ip} => {len(domains)} domains")
                return domains
            if "Unable to do" in text:
                return []
            _log_error(
                f"ViewDns rate limited ({ip}), rotating Tor... ({attempt}/{max_retries})"
            )
            _reload_tor()
        except requests.RequestException as exc:
            _log_error(f"ViewDns request error ({ip}): {exc}")
            time.sleep(2)
    return []


def _clean_domain(domain: str) -> str:
    for prefix in _CLEAN_PREFIXES:
        domain = domain.replace(prefix, "")
    return domain.strip()


def _resolve_ip(target: str) -> str | None:
    cleaned = target.removeprefix("http://").removeprefix("https://").replace("/", "")
    try:
        return socket.gethostbyname(cleaned)
    except socket.gaierror as exc:
        _log_error(f"DNS failed for {target}: {exc}")
        return None


def process_target(
    session: requests.Session, target: str, timeout: int, max_retries: int
) -> tuple[str | None, list[str]]:
    ip = _resolve_ip(target)
    if not ip:
        return None, []

    domains = _reverse_hackertarget(session, ip, timeout, max_retries)
    if not domains:
        domains = _reverse_viewdns(session, ip, timeout, max_retries)

    return ip, domains


def _banner() -> None:
    print(
        f"""{C_GREEN}
───────╔════╦═══╦═══╗
───────║╔╗╔╗║╔═╗║╔═╗║
╔═╦══╦╗╠╣║║╚╣║─║║╚═╝║
║╔╣║═╣╚╝║║║─║║─║║╔╗╔╝
║║║║═╬╗╔╝║║─║╚═╝║║║╚╗
╚╝╚══╝╚╝─╚╝─╚═══╩╝╚═╝  v2.0.0
{C_RESET}"""
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reverse IP lookup with Tor support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  %(prog)s -l targets.txt -t 20
  %(prog)s -l targets.txt -t 50 --proxy socks5://127.0.0.1:9050 -o results.txt
        """,
    )
    parser.add_argument("-l", "--list", required=True, help="File containing target URLs/IPs")
    parser.add_argument("-t", "--threads", type=int, default=20, help="Concurrent threads")
    parser.add_argument("-o", "--output", type=Path, default=Path("rev.txt"), help="Output file")
    parser.add_argument(
        "--proxy", default="socks5://127.0.0.1:9050", help="SOCKS proxy URL"
    )
    parser.add_argument("--timeout", type=int, default=14, help="Request timeout in seconds")
    parser.add_argument("--no-tor", action="store_true", help="Skip Tor service management")
    parser.add_argument("--retries", type=int, default=5, help="Max retries per API on rate limit")
    args = parser.parse_args()

    _banner()

    list_path = Path(args.list)
    if not list_path.exists():
        _log_error(f"File not found: {list_path}")
        sys.exit(1)

    targets = [
        line.strip()
        for line in list_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if not args.no_tor:
        _start_tor()

    session = _create_session(args.proxy)
    seen_ips: set[str] = set()

    with (
        args.output.open("a", encoding="utf-8") as fh,
        ThreadPoolExecutor(max_workers=args.threads) as executor,
    ):
        futures = {
            executor.submit(
                process_target, session, target, args.timeout, args.retries
            ): target
            for target in targets
        }
        for future in as_completed(futures):
            try:
                ip, domains = future.result()
            except Exception as exc:
                _log_error(f"Unhandled error for {futures[future]}: {exc}")
                continue

            if not ip:
                continue
            if ip in seen_ips:
                _log_error(f"DUPLICATE! > {ip}")
                continue
            seen_ips.add(ip)

            if domains:
                for domain in domains:
                    fh.write(_clean_domain(domain) + "\n")


if __name__ == "__main__":
    main()
