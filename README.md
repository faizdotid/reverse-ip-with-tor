# Reverse IP with Tor

Modern concurrent reverse IP lookup scanner using HackerTarget and ViewDNS APIs with automatic Tor circuit rotation on rate limits.

## Features

- `ThreadPoolExecutor` for efficient concurrency
- Automatic Tor circuit rotation on API rate limits
- Duplicate IP detection with `set()`
- Buffered output writing
- CLI flags (no more interactive prompts)
- Cleaner domain filtering (removes cpanel, webmail, etc.)

## Installation

```bash
git clone https://github.com/faizdotid/reverse-ip-with-tor
cd reverse-ip-with-tor
pip install -r requirements.txt
# Ensure tor is installed
apt install tor   # Debian/Ubuntu
brew install tor  # macOS
```

## Usage

```bash
python3 rev.py -l targets.txt -t 20
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-l, --list` | *(required)* | File containing target URLs/IPs |
| `-t, --threads` | `20` | Concurrent threads |
| `-o, --output` | `rev.txt` | Output file |
| `--proxy` | `socks5://127.0.0.1:9050` | SOCKS proxy URL |
| `--timeout` | `14` | Request timeout in seconds |
| `--retries` | `5` | Max retries per API on rate limit |
| `--no-tor` | `false` | Skip Tor service management |

### Examples

Scan with 50 threads and custom output:

```bash
python3 rev.py -l targets.txt -t 50 -o results.txt
```

Use custom proxy without Tor management:

```bash
python3 rev.py -l targets.txt -t 20 --proxy socks5://127.0.0.1:1080 --no-tor
```

## Disclaimer

This tool is intended for authorized security testing and research only. Always obtain proper permission before testing systems you do not own.
