# tempmail-vps

Apna khud ka **unlimited temp mail** system — apne VPS pe, apne domain pe, koi third-party API nahi.

- FastAPI backend + web UI
- SQLite storage (single container, no external DB)
- Unlimited inboxes (custom name option included)
- Auto OTP extraction from incoming mail
- Cloudflare Email Routing se real mail receive hota hai
- Dockerized — `docker compose up -d` aur ready

---

## Folder structure

```
tempmail-vps/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── nginx/
│   └── default.conf
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── schemas.py
│   ├── mail_parser.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   └── mail.py
│   └── static/
│       ├── index.html
│       ├── style.css
│       └── app.js
├── cloudflare/
│   └── worker.js
└── README.md
```

## VPS pe deploy (5 minutes)

### Step 1 — files upload karo
```bash
# apne PC se VPS tak folder bhejo
scp -r tempmail-vps root@YOUR_VPS_IP:/root/
```

### Step 2 — VPS pe env set karo
```bash
ssh root@YOUR_VPS_IP
cd /root/tempmail-vps
cp .env.example .env
nano .env
```
Ye 3 cheezein change karo:
- `MAIL_DOMAIN=mail.yourdomain.com` → tumhara actual domain
- `INGEST_KEY=koi-lamba-random-string` → strong password jaisa
- baaki default theek hai

### Step 3 — Docker install (agar nahi hai)
```bash
curl -fsSL https://get.docker.com | sh
```

### Step 4 — build aur run
```bash
docker compose up -d --build
# check
docker compose logs -f
```
Ab backend `localhost:8000` pe chal raha hai.

### Step 5 — nginx se expose karo (optional but recommended)
```bash
apt install -y nginx
cp nginx/default.conf /etc/nginx/conf.d/tempmail.conf
nano /etc/nginx/conf.d/tempmail.conf   # server_name me apna domain daalo
nginx -t && systemctl reload nginx
```

### Step 6 — HTTPS (Cloudflare free DNS pe chal jata hai easily)
Cloudflare dashboard me DNS record banao:
```
A record: mail.yourdomain.com → YOUR_VPS_IP (proxied ON)
```
SSL/TLS mode: **Full**. Bas — https live ho jayega.

---

## Cloudflare Email Routing (real mail receive karne ke liye)

Iske bina inbox bhi banega par mail **nahi** aayegi. Ye step zaroori hai.

1. **Domain Cloudflare pe add karo** (free plan chalega)
2. Cloudflare dashboard → domain → **Email → Email Routing** → enable
3. **Catch-all rule**: Action = "Send to Worker"
4. **Worker create karo**: Workers & Pages → Create Worker → paste `cloudflare/worker.js`
5. Worker me edit karo:
   - `APP_URL` → `https://mail.yourdomain.com` (ya jo bhi tumhara URL hai)
   - `INGEST_KEY` → same value jo `.env` me daali thi
6. Email Routing → Catch-all → action **Send to Worker** → ye worker select karo
7. Cloudflare khud hi MX records set karega. Done.

### Test
```bash
# web UI kholo: https://mail.yourdomain.com
# ya curl se:
curl -X POST https://mail.yourdomain.com/mail/inbox -H 'content-type: application/json' -d '{}'
curl -X POST https://mail.yourdomain.com/mail/inbox -H 'content-type: application/json' \
  -d '{"local_part":"mybox1"}'
```
Inbox address copy karo. Gmail / kisi bhi mail se us address pe mail bhejo.
Web UI pe ya `curl` se check karo:
```bash
curl https://mail.yourdomain.com/mail/inbox/{INBOX_ID}/messages
```
Mail 5 second ke andar dikhegi, OTP auto-extracted bhi dikhega.

---

## API

| Method | Path | Work |
|---|---|---|
| `GET` | `/health` | healthcheck |
| `GET` | `/` | web UI |
| `POST` | `/mail/inbox` | naya inbox (optional `local_part`) |
| `GET` | `/mail/inbox/{id}` | inbox info |
| `GET` | `/mail/inbox/{id}/messages` | messages, OTP extracted |
| `DELETE` | `/mail/inbox/{id}` | delete inbox |
| `GET` | `/mail/stats` | pool stats |

### Inbox banao (custom name)
```bash
curl -X POST https://mail.yourdomain.com/mail/inbox \
  -H 'content-type: application/json' \
  -d '{"local_part":"signup1"}'
# → signup1@yourdomain.com
```

### Messages dekho
```bash
curl https://mail.yourdomain.com/mail/inbox/{INBOX_ID}/messages | jq
```

---

## Notes

- **storage**: SQLite, single file. Backup = `data/app.db` copy.
- **cleanup**: har `CLEANUP_INTERVAL_SECONDS` pe expired inbox auto-delete.
- **unlimited**: default cap `MAX_INBOXES = 500` hai `app/routes/mail.py` me — badalna ho to wahan change karo.
- **security**: `INGEST_KEY` ke bina worker mails ingest nahi kar payega.
- **domain**: sirf 1 domain per instance; naya domain chahiye to `MAIL_DOMAIN` change karke re-deploy.

---

## Telegram bot me integrate karna (optional)

Bot me `/tempmail` command already hai (bot uses catchmail API). Ab apne self-hosted se wire karna ho to:

```js
// bot /tempmail command me bas ye API call karo:
POST https://mail.yourdomain.com/mail/inbox   → inbox.address
GET  https://mail.yourdomain.com/mail/inbox/{id}/messages  → messages + otp
```

Bot se bas jo result fetch karna hai, ye API endpoints hi use karo — same endpoints jo bot UI me dikhengi.

## Credits

Built by **@TrueNakshu** — single VPS pe self-hosted temp-mail stack.
