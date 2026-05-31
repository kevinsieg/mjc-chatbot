# Cloudflare + OVH Firewall Setup

## Prerequisites
- Domain DNS managed in Cloudflare (free account)
- OVH server admin access (firewall rules via OVH Control Panel or `iptables`)

## 1. Cloudflare DNS

1. Log in to Cloudflare → select your domain
2. DNS → Add record:
   - Type: `A`
   - Name: `@` (or `www`)
   - IPv4 address: your OVH server IP
   - **Proxy status: Proxied (orange cloud)** ← required, do not set to DNS-only
3. Verify the record shows "Proxied" (not "DNS only")

## 2. Enable Bot Fight Mode

1. Cloudflare dashboard → Security → Bots
2. Enable **Bot Fight Mode** (free tier)
3. This blocks known bad bots (scrapers, credential stuffers) before they reach your server

## 3. Rate limiting (Cloudflare Pro — optional)

The free tier does not support custom rate limiting rules. Rate limiting is handled by Traefik (see docker-compose.yml). If you upgrade to Pro ($20/mo), you can add a Cloudflare rule:
- Path: `/api/backend/api/v1/chat`
- Threshold: 10 requests / 1 minute per IP
- Action: Block

## 4. Lock OVH firewall to Cloudflare IPs only

This is critical. Without it, attackers can bypass Cloudflare by hitting your OVH IP directly.

Cloudflare publishes its IP ranges at:
- https://www.cloudflare.com/ips-v4
- https://www.cloudflare.com/ips-v6

### Via iptables (run as root on OVH server)

```bash
# IMPORTANT: Verify your current rules first — this script assumes no prior DROP rules on port 80.
# Run: iptables -L INPUT -n --line-numbers
# and ip6tables -L INPUT -n --line-numbers

# Insert SSH rule at the top so it is always evaluated first
iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT

# Fetch Cloudflare IPv4 ranges and allow them on port 80
CF_IPV4=$(curl -sf https://www.cloudflare.com/ips-v4)
if [ -z "$CF_IPV4" ]; then
  echo "ERROR: Failed to fetch Cloudflare IPv4 ranges. Aborting — no DROP rule added."
  exit 1
fi
for ip in $CF_IPV4; do
  iptables -A INPUT -p tcp --dport 80 -s $ip -j ACCEPT
done
iptables -A INPUT -p tcp --dport 80 -j DROP

# If your server has a public IPv6 address, repeat for IPv6:
CF_IPV6=$(curl -sf https://www.cloudflare.com/ips-v6)
if [ -z "$CF_IPV6" ]; then
  echo "ERROR: Failed to fetch Cloudflare IPv6 ranges. Aborting — no IPv6 DROP rule added."
  exit 1
fi
for ip in $CF_IPV6; do
  ip6tables -A INPUT -p tcp --dport 80 -s $ip -j ACCEPT
done
ip6tables -I INPUT 1 -p tcp --dport 22 -j ACCEPT
ip6tables -A INPUT -p tcp --dport 80 -j DROP

# Persist rules (Debian/Ubuntu)
apt-get install iptables-persistent -y
netfilter-persistent save
```

### Verify

From a machine NOT behind Cloudflare, try to connect directly:
```bash
curl -v http://<OVH-IP>/
```
Expected: connection refused or timeout (not a response from the app).

From a browser via the domain:
```bash
curl -v http://<your-domain>/
```
Expected: 200 response served through Cloudflare.

## 5. Verify full chain

1. Browser → `http://<your-domain>/` → should load the chatbot UI
2. Send a chat message → should work (200)
3. Send 25 rapid messages → should get 429 from Traefik after the burst (Traefik rate limit, not Cloudflare — Cloudflare Pro rate limiting is optional)
4. Direct IP access `http://<OVH-IP>/` → should be blocked by firewall

## Cloudflare IP ranges

Always fetch fresh from https://www.cloudflare.com/ips-v4 — do not hardcode these in scripts.
