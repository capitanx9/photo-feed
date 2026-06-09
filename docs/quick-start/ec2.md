# Quick start — production EC2

How to reach the running prod box from your laptop. You need SSH
access (your public key authorized on the host).

## Prereqs (on macOS)

Nothing special — an SSH client is built into macOS, and a key in
`~/.ssh/`.

Add an entry to `~/.ssh/config`:

```
Host photo-feed
  HostName 52.58.226.63
  User ubuntu
  IdentityFile ~/.ssh/<your-key>
  IdentitiesOnly yes
  ServerAliveInterval 30
  ServerAliveCountMax 6
```

Connect:

```bash
ssh photo-feed
cd /srv/photo-feed
make logs-web
```

You should land in `/home/ubuntu/`. From there `cd /srv/photo-feed/`
and use the same `make` targets you use locally — see
[`../debug/`](../debug/).
