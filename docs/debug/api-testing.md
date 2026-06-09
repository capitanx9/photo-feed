# Debugging the API by hand

Fire a real request from one window, watch the server's reaction in
another. The fastest way to corner a bug.

Bruno on one side, logs on the other.

For installing Bruno and loading the collection see
[`../api/bruno.md`](../api/bruno.md). For resetting data between
attempts see [`seeds.md`](seeds.md).

## Local (dev)

```bash
make up
make logs-web
```

Open Bruno → environment **`local`** → pick a request → Send.

Compare Bruno's response with what `make logs-web` prints. The
gunicorn access line plus any Python traceback usually pin the bug
within 5 lines.

To reset data between attempts:

```bash
make reset && make seed-all
```

## Remote (prod)

Same workflow, same `make` targets. The EC2 box has the same
Makefile checked out at `/srv/photo-feed/`, so once you're SSH'd in
the commands are identical:

```bash
ssh photo-feed
cd /srv/photo-feed
make logs-web
```

Open Bruno → environment **`prod`** → Send.

Compare Bruno's response with what `make logs-web` prints on EC2.

Without SSH access (the right key in your `~/.ssh/config` for the
`photo-feed` host) this section doesn't apply.

