# Logs

How to watch what every service is saying — local and prod.

## Local

Defined in [`makefiles/docker/logs.mk`](../../makefiles/docker/logs.mk).
The stack must be up (`make up`) first.

| Command | What it tails |
|---|---|
| `make logs` | Every service in the dev compose file |
| `make logs-web` | Just Django (gunicorn / runserver stdout) |
| `make logs-db` | Postgres |
| `make logs-redis` | Redis |
| `make logs-mailhog` | Mailhog (captured outbound mail) |

All of them follow the stream — Ctrl-C to stop. For a one-shot dump
of recent lines:

```bash
make logs-web | head -100
```

## Prod

Same `make` targets as Local — the EC2 box has the same Makefile
checked out at `/srv/photo-feed/`. SSH in (see
[`../quick-start/ec2.md`](../quick-start/ec2.md) for `~/.ssh/config`
setup), then use the same commands:

```bash
ssh photo-feed
cd /srv/photo-feed
make logs-web    # or logs-db, logs-redis, logs (everything)
```

`cd /srv/photo-feed` matters — without it compose can't see `.env`
and complains about missing variables, which is misleading noise.

## Lambda logs (CloudWatch)

The two Lambdas don't run on EC2; their logs live in CloudWatch.

```bash
# cut_image (eu-central-1)
aws logs tail /aws/lambda/photo-feed-cut-image \
    --follow --profile cx9-gmail --region eu-central-1

# generate_image (us-west-2)
aws logs tail /aws/lambda/photo-feed-generate-image \
    --follow --profile cx9-gmail --region us-west-2
```

Filter to errors only:

```bash
aws logs tail /aws/lambda/photo-feed-cut-image \
    --filter-pattern 'ERROR' \
    --since 1h --profile cx9-gmail --region eu-central-1
```
