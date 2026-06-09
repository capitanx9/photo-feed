# Architecture

How the parts connect at runtime. For the list of technologies see
[`tech-stack.md`](tech-stack.md); for what the product does see
[`overview.md`](overview.md). This page only covers wiring.

## Components and data flow

```
                                      ┌──────────────────────┐
                                      │  browser / API client│
                                      └──────────┬───────────┘
                                                 │ HTTPS
                                                 ▼
                                      ┌──────────────────────┐
                                      │ nginx (TLS)          │
                                      │ photo-feed.gotdns.ch │
                                      └──────────┬───────────┘
                                                 │ http :8000
                                                 ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  gunicorn (Django + DRF) ──→ postgres   (rows)                        │
   │                          ──→ redis      (cache, celery broker)        │
   │                          ──→ S3 uploads (presigned PUT)               │
   │                                  │                                    │
   └──────────────────────────────────┼────────────────────────────────────┘
                                      │ s3:ObjectCreated (raw/)
                                      ▼
                          ┌──────────────────────────┐
                          │ Lambda cut_image (euc1)  │
                          │  • Pillow resize         │
                          │  • PUT resized/<key>     │
                          │  • webhook → Django      │
                          └──────────────────────────┘

   (separate path — text-to-image)

   gunicorn (Django) ──→ celery task ──→ Lambda generate_image (us-west-2)
                                              │
                                              │ Bedrock InvokeModel
                                              ▼
                                       Stability AI text-to-image
                                              │
                                              ▼
                                       S3 generated bucket (usw2)
                                              │
                                              ▼
                                       webhook → Django
```

## Where things live

| Resource | Region | Notes |
|---|---|---|
| EC2 (web / db / redis / nginx / celery / certbot) | eu-central-1 | One instance, Elastic IP, NoIP hostname |
| ECR `photo-feed-api` | eu-central-1 | Built and pushed by `cd-api` |
| S3 `photo-feed-uploads` | eu-central-1 | `raw/` + `resized/` |
| Lambda `photo-feed-cut-image` | eu-central-1 | Triggered by S3 ObjectCreated on `raw/` |
| S3 `photo-feed-generated-usw2` | us-west-2 | AI output only |
| Lambda `photo-feed-generate-image` | us-west-2 | Calls Bedrock Stability |
| SSM Parameter Store `/photo-feed/prod/*` | eu-central-1 | Three SecureStrings (secret_key, db pw, webhook secret) |

## Why two regions

Bedrock Stability text-to-image is only ACTIVE in `us-west-2`.
Amazon Nova Canvas and Titan Image v2 (eu-west-1) are LEGACY.
Generating in us-west-2 and writing to a same-region bucket avoids
cross-region S3 writes on the hot path.

The api in eu-central-1 talks to that us-west-2 bucket cross-region
only when finalizing a generation (cold path); reading the image for
display goes through a presigned URL that points directly at the
bucket.

## Identity (deploy-time)

GitHub Actions federate into AWS via OIDC. Two deployer roles, each
scoped to what its workflow needs:

- `photo-feed-api-github-actions` — used by `cd-api`. Permissions:
  ECR push, EC2 describe (lookup by tag), SSM SendCommand to the
  tagged instance only, SSM GetCommandInvocation.
- `photo-feed-lambdas-github-actions` — used by `cd-lambdas`.
  Permissions: CloudFormation on our two app stacks + the
  SAM-managed artifact stack, S3 on the app buckets, Lambda on the
  two functions, IAM scoped to the per-stack exec roles, the
  AWS-owned `Serverless-2016-10-31` transform.

EC2 itself carries `PhotoFeedInstanceRole`:
`AmazonSSMManagedInstanceCore` + `AmazonEC2ContainerRegistryReadOnly`
+ `CloudWatchAgentServerPolicy` + inline policy for SSM Parameter
Store read and KMS decrypt.

The Lambda exec roles are created by CloudFormation per stack and
only carry the permissions their SAM template asks for (S3 on the
relevant bucket plus, for generate_image, `bedrock:InvokeModel` on
three specific Stability model ARNs).

## Identity (runtime)

End-user requests are authenticated by JWT in `HttpOnly` cookies.
The api never sees `Authorization` headers from the frontend. See
[`api/auth.md`](api/auth.md) for the cookie flow.

Webhooks from Lambdas to Django carry an HMAC header signed with
`WEBHOOK_SHARED_SECRET` so a leaked URL alone can't post a fake
"media processed" event.
