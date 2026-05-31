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
# Allow SSH first (do not lock yourself out)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow Cloudflare IPv4 ranges on port 80
for ip in $(curl -s https://www.cloudflare.com/ips-v4); do
  iptables -A INPUT -p tcp --dport 80 -s $ip -j ACCEPT
done

# Drop all other traffic on port 80
iptables -A INPUT -p tcp --dport 80 -j DROP

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
3. Send 25 rapid messages → should get 429 from Traefik after the burst
4. Direct IP access `http://<OVH-IP>/` → should be blocked by firewall

## Cloudflare IP ranges

Always fetch fresh from https://www.cloudflare.com/ips-v4 — do not hardcode these in scripts.
