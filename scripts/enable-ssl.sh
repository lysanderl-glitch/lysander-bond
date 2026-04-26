#!/bin/bash
# Enable HTTPS for synapsehd.com via Let's Encrypt certbot
# Run after ICP filing is approved
# Expected to run on synapsehd-server (118.196.41.252)

set -e

echo "=== Step 1: Verify nginx config ==="
nginx -t

echo "=== Step 2: Install certbot if needed ==="
which certbot || apt install -y certbot python3-certbot-nginx

echo "=== Step 3: Verify domains resolve to this server ==="
DOMAIN_IP=$(dig +short synapsehd.com @8.8.8.8 | head -1)
SERVER_IP=$(curl -s ifconfig.me)
if [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
  echo "WARNING: synapsehd.com resolves to $DOMAIN_IP but server is $SERVER_IP"
  read -p "Continue anyway? (y/N) " -n 1 -r
  [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

echo "=== Step 4: Verify HTTP 200 (not WAF blocked) ==="
HTTP=$(curl -sIL --max-time 15 http://synapsehd.com/ | grep "^HTTP" | tail -1 | awk '{print $2}')
if [ "$HTTP" != "200" ]; then
  echo "ERROR: http://synapsehd.com/ returns $HTTP (expected 200)"
  echo "ICP filing may not be active yet. Try again later."
  exit 1
fi

echo "=== Step 5: Apply Let's Encrypt certificate ==="
certbot --nginx \
  -d synapsehd.com \
  -d www.synapsehd.com \
  --non-interactive \
  --agree-tos \
  --email lysanderl@janusd.io \
  --redirect

echo "=== Step 6: Verify HTTPS ==="
curl -sIL --max-time 15 https://synapsehd.com/ | head -3
curl -sIL --max-time 15 https://www.synapsehd.com/ | head -3

echo "=== Done ==="
echo "synapsehd.com is now live with HTTPS"
echo "Auto-renewal configured (certbot.timer)"
