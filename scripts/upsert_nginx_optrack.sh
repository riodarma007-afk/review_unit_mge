#!/bin/bash
# Upsert location /optrack ke planning.mge.co.id.conf (tambah atau replace jika sudah ada)
# Dipanggil otomatis oleh CI/CD setiap deploy.

set -e

CONF="/data/nginx/sites-available/planning.mge.co.id.conf"

if [ ! -f "$CONF" ]; then
  echo "ERROR: $CONF tidak ditemukan"
  exit 1
fi

sudo cp "$CONF" "${CONF}.bak.$(date +%Y%m%d_%H%M%S)"
echo "Backup dibuat: ${CONF}.bak.*"

sudo python3 - "$CONF" <<'PYEOF'
import sys, re

path = sys.argv[1]
with open(path, 'r') as f:
    content = f.read()

NEW_BLOCK = """
    # ── Optrack: Backend API ──────────────────────────────────────────────────
    location /api/optrack/ {
        proxy_pass         http://127.0.0.1:8002/api/v1/;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # ── Optrack: Frontend SPA ─────────────────────────────────────────────────
    location = /optrack {
        return 301 https://$host/optrack/;
    }
    location /optrack/ {
        alias /data/www/planning/frontend/optrack/;
        try_files $uri $uri/ @optrack_fallback;

        location ~* \\.(js|css|woff2?|ttf|eot|svg|png|jpg|ico)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    location @optrack_fallback {
        rewrite ^ /optrack/index.html last;
    }
    location = /optrack/index.html {
        alias /data/www/planning/frontend/optrack/index.html;
        add_header Cache-Control "no-cache";
    }
"""

# Hapus block lama jika sudah ada
content = re.sub(
    r'\n\s*# ── Optrack:.*?location = /optrack/index\.html \{.*?\n\s*\}',
    '',
    content,
    flags=re.DOTALL,
)

# Sisipkan sebelum penutup server block terakhir
last_brace = content.rfind('\n}')
if last_brace == -1:
    print("ERROR: tidak menemukan penutup server block")
    sys.exit(1)

content = content[:last_brace] + NEW_BLOCK + content[last_brace:]

with open(path, 'w') as f:
    f.write(content)

print("OK: block /optrack di-upsert")
PYEOF

sudo nginx -t && sudo systemctl reload nginx
echo "DONE: nginx reload berhasil"
