# Automatic deploy of master

`/home/ubuntu/veniss-app` is mounted live into ResearchSpace, so the server
serves whatever is checked out there. This setup keeps it on the latest
`master` without anyone running `git pull`.

## How it works

1. A merge to `master` makes GitHub send a signed `push` webhook to
   `https://veniss.net/_hooks/deploy`.
2. Traefik routes that path to `veniss-autopull-listener` (`listener.py`).
   It checks the HMAC signature and the ref, then only touches
   `~/veniss-autopull/trigger/deploy`. The container runs read-only, without
   capabilities, git or the Docker socket.
3. A cron job checks for the trigger file every minute and runs
   `~/bin/veniss-autopull.sh`. The script fast-forwards the checkout and
   restarts `veniss-researchspace-1` if `config/` changed. It also runs once
   an hour without a trigger, in case a webhook was missed.

The script **skips** (and logs why) when the checkout is not on `master` or
has local changes, so work in progress on the server is never overwritten.

Merging to `master` therefore deploys to production within about a minute.

## Setup (once, on the server)

```bash
cd /home/ubuntu/veniss-app/deploy/autopull
mkdir -p ~/bin ~/veniss-autopull/trigger
install -m 755 veniss-autopull.sh ~/bin/

echo "WEBHOOK_SECRET=$(openssl rand -hex 32)" > .env && chmod 600 .env
docker compose up -d --build
```

Add to `crontab -e`:

```
* * * * * /home/ubuntu/bin/veniss-autopull.sh --if-triggered /home/ubuntu/veniss-autopull/trigger/deploy
7 * * * * /home/ubuntu/bin/veniss-autopull.sh
```

Then, in GitHub → villaitatti/VeNiss → Settings → Webhooks → Add webhook:

| Field | Value |
|-------|-------|
| Payload URL | `https://veniss.net/_hooks/deploy` |
| Content type | `application/json` |
| Secret | the `WEBHOOK_SECRET` from `.env` |
| Events | Just the push event |

GitHub sends a `ping` straight away. *Recent Deliveries* should show `200`.

## Changing the deploy script

The crontab runs the copy in `~/bin`, not the one in the repo, so a merged PR
cannot change what runs on the host. After a reviewed change to
`veniss-autopull.sh`, reinstall it by hand:

```bash
install -m 755 deploy/autopull/veniss-autopull.sh ~/bin/
```

## Operations

| Task | Command |
|------|---------|
| Deploy log | `tail -f ~/veniss-autopull/autopull.log` |
| Listener log | `docker logs veniss-autopull-listener` |
| Deploy now | `~/bin/veniss-autopull.sh` |
| Pause webhooks | `docker compose stop` (here), and comment out the cron lines |
