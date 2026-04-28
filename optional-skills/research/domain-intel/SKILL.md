---
name: domain-intel
description: Passive domain reconnaissance using Python stdlib. Subdomain discovery, SSL certificate inspection, WHOIS lookups, DNS records, domain availability checks, and bulk multi-domain analysis. No API keys required.
---

# Domain Intelligence â€?Passive OSINT

Passive domain reconnaissance using only Python stdlib.
**Zero dependencies. Zero API keys. Works on Linux, macOS, and Windows.**

## Helper script

This skill includes `scripts/domain_intel.py` â€?a complete CLI tool for all domain intelligence operations.

```bash
# Subdomain discovery via Certificate Transparency logs
python3 SKILL_DIR/scripts/domain_intel.py subdomains example.com

# SSL certificate inspection (expiry, cipher, SANs, issuer)
python3 SKILL_DIR/scripts/domain_intel.py ssl example.com

# WHOIS lookup (registrar, dates, name servers â€?100+ TLDs)
python3 SKILL_DIR/scripts/domain_intel.py whois example.com

# DNS records (A, AAAA, MX, NS, TXT, CNAME)
python3 SKILL_DIR/scripts/domain_intel.py dns example.com

# Domain availability check (passive: DNS + WHOIS + SSL signals)
python3 SKILL_DIR/scripts/domain_intel.py available coolstartup.io

# Bulk analysis â€?multiple domains, multiple checks in parallel
python3 SKILL_DIR/scripts/domain_intel.py bulk example.com github.com google.com
python3 SKILL_DIR/scripts/domain_intel.py bulk example.com github.com --checks ssl,dns
```

`SKILL_DIR` is the directory containing this SKILL.md file. All output is structured JSON.

## Available commands

| Command | What it does | Data source |
|---------|-------------|-------------|
| `subdomains` | Find subdomains from certificate logs | crt.sh (HTTPS) |
| `ssl` | Inspect TLS certificate details | Direct TCP:443 to target |
| `whois` | Registration info, registrar, dates | WHOIS servers (TCP:43) |
| `dns` | A, AAAA, MX, NS, TXT, CNAME records | System DNS + Google DoH |
| `available` | Check if domain is registered | DNS + WHOIS + SSL signals |
| `bulk` | Run multiple checks on multiple domains | All of the above |

## When to use this vs built-in tools

- **Use this skill** for infrastructure questions: subdomains, SSL certs, WHOIS, DNS records, availability
- **Use `web_extract`** for general research about what a domain/company does
- **Use `web_extract`** to get the actual content of a webpage
- **Use `terminal` with `curl -I`** for a simple "is this URL reachable" check

| Task | Better tool | Why |
|------|-------------|-----|
| "What does example.com do?" | `web_extract` | Gets page content, not DNS/WHOIS data |
| "Find info about a company" | `web_extract` | General research, not domain-specific |
| "Is this website safe?" | `web_extract` | Reputation checks need web context |
| "Check if a URL is reachable" | `terminal` with `curl -I` | Simple HTTP check |
| "Find subdomains of X" | **This skill** | Only passive source for this |
| "When does the SSL cert expire?" | **This skill** | Built-in tools can't inspect TLS |
| "Who registered this domain?" | **This skill** | WHOIS data not in web search |
| "Is coolstartup.io available?" | **This skill** | Passive availability via DNS+WHOIS+SSL |

## Platform compatibility

Pure Python stdlib (`socket`, `ssl`, `urllib`, `json`, `concurrent.futures`).
Works identically on Linux, macOS, and Windows with no dependencies.

- **crt.sh queries** use HTTPS (port 443) â€?works behind most firewalls
- **WHOIS queries** use TCP port 43 â€?may be blocked on restrictive networks
- **DNS queries** use Google DoH (HTTPS) for MX/NS/TXT â€?firewall-friendly
- **SSL checks** connect to the target on port 443 â€?the only "active" operation

## Data sources

All queries are **passive** â€?no port scanning, no vulnerability testing:

- **crt.sh** â€?Certificate Transparency logs (subdomain discovery, HTTPS only)
- **WHOIS servers** â€?Direct TCP to 100+ authoritative TLD registrars
- **Google DNS-over-HTTPS** â€?MX, NS, TXT, CNAME resolution (firewall-friendly)
- **System DNS** â€?A/AAAA record resolution
- **SSL check** is the only "active" operation (TCP connection to target:443)

## Notes

- WHOIS queries use TCP port 43 â€?may be blocked on restrictive networks
- Some WHOIS servers redact registrant info (GDPR) â€?mention this to the user
- crt.sh can be slow for very popular domains (thousands of certs) â€?set reasonable expectations
- The availability check is heuristic-based (3 passive signals) â€?not authoritative like a registrar API

---

*Contributed by [@FurkanL0](https://github.com/FurkanL0)*
