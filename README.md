# photo-feed

Instagram-shop backend with Django + AWS Lambda (lab 4).

## Quick start

```bash
make up                # start postgres + redis + django + mailhog
make migrate           # apply database migrations
make seed-all          # populate 10 users, 50 posts, sample orders
```

Default demo login: `kyrylo@photo-feed.local` / `pass1234` —
see [docs/operations/seeds.md](docs/operations/seeds.md) for the full
demo-data layout, and `bruno/photo-feed/` for a ready-to-use HTTP
collection.

## Common tasks

```bash
make check             # lint + api tests
make test-lambdas      # moto-backed cut_image + generate_image tests
make reset-demo        # flush demo data and reseed from scratch
make help              # full target list
```
