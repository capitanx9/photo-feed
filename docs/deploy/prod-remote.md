# Production deploy — end to end

How a commit on `main` ends up running on EC2 or as a Lambda. Every
role, every secret, every step.

## Bird's-eye view

```
  ┌──────────────────┐   push: main
  │   GitHub repo    │ ─────────────►  GitHub Actions
  └──────────────────┘                       │
                                             │ OIDC AssumeRoleWithWebIdentity
                                             ▼
                                ┌────────────────────────────┐
                                │ STS — short-lived creds    │
                                │ for the workflow's deployer│
                                │ role                       │
                                └──────────┬─────────────────┘
                                           │
            ┌──────────────────────────────┴──────────────────────────────┐
            ▼                                                             ▼
 ┌────────────────────────────┐                          ┌──────────────────────────────┐
 │ cd-api                     │                          │ cd-lambdas                   │
 │  1. Build api image        │                          │  1. SAM validate / build     │
 │  2. Push to ECR            │                          │  2. Pull WEBHOOK secret       │
 │  3. SSM SendCommand on EC2 │                          │     from SSM (masked)         │
 │  4. Poll until done        │                          │  3. SAM deploy euc1 + usw2   │
 └──────────┬─────────────────┘                          │     (parallel)               │
            │                                            └──────────────┬───────────────┘
            ▼                                                           ▼
 ┌────────────────────────────┐                          ┌──────────────────────────────┐
 │ EC2 (eu-central-1)         │                          │ CloudFormation per region    │
 │  deploy.sh:                │                          │  - S3 app bucket             │
 │   - read SSM → .env        │                          │  - Lambda function           │
 │   - docker pull            │                          │  - exec-role per Lambda      │
 │   - compose up -d          │                          │  - S3 event trigger          │
 │   - migrate                │                          └──────────────────────────────┘
 │   - smoke /api/health/     │
 └────────────────────────────┘
```

## Identity — who can do what

### GitHub OIDC provider (one-time setup)

AWS validates GitHub-issued OIDC tokens via this registered
provider:

```
arn:aws:iam::797890596022:oidc-provider/token.actions.githubusercontent.com
```

No long-lived AWS access keys live in GitHub. Each run gets a fresh
STS session.

### Deployer role — `photo-feed-api-github-actions`

Used by `cd-api`. Trust policy: only `repo:capitanx9/photo-feed`
`ref:refs/heads/main` may assume it.

Permissions:

- ECR — `GetAuthorizationToken` on `*`; push/get on the
  `photo-feed-api` repository ARN only.
- EC2 — `DescribeInstances` on `*` (used to look the instance up by tag).
- SSM — `SendCommand` on instance ARNs with Condition
  `aws:ResourceTag/Application=photo-feed-api`, plus the
  `AWS-RunShellScript` document. `GetCommandInvocation` /
  `ListCommandInvocations` on `*` **without** a Condition — those
  command-invocation resources can't carry tags, so the Condition
  above would always deny them.

### Deployer role — `photo-feed-lambdas-github-actions`

Used by `cd-lambdas`. Same trust shape. Permissions cover SAM:

- CloudFormation — full action set on `photo-feed-euc1`,
  `photo-feed-usw2`, and `aws-sam-cli-managed-default` stacks.
- CloudFormation — `CreateChangeSet` on
  `arn:aws:cloudformation:*:aws:transform/Serverless-2016-10-31`
  (the AWS-owned SAM transform ARN; without this SAM can't expand
  `Transform: AWS::Serverless-2016-10-31`).
- CloudFormation read-only — `DescribeStacks` /
  `GetTemplateSummary` / `ListStacks` / `ValidateTemplate` on `*`
  (SAM bootstrap needs them before it knows the stack ARN).
- S3 — bucket lifecycle on `aws-sam-cli-managed-default*` (SAM
  artifacts) and on `photo-feed-uploads`, `photo-feed-generated-usw2`.
- Lambda — function lifecycle on the two function ARNs.
- IAM — scoped to `photo-feed-{euc1,usw2}-*` role names; SAM creates
  Lambda exec roles named like the stack.
- SSM — `GetParameter*` on `/photo-feed/prod/WEBHOOK_SHARED_SECRET`
  plus `kms:Decrypt` via SSM.

### EC2 instance role — `PhotoFeedInstanceRole`

Attached as instance profile on the EC2.

Managed:
- `AmazonSSMManagedInstanceCore`
- `AmazonEC2ContainerRegistryReadOnly`
- `CloudWatchAgentServerPolicy`

Inline (`PhotoFeedInstanceRole-SSMParameters`):
- `ssm:GetParameter` / `GetParameters` on `/photo-feed/prod/*`
- `kms:Decrypt` with Condition `kms:ViaService=ssm.eu-central-1.amazonaws.com`

## Secrets — where each one lives

| Secret | Where | Read by |
|---|---|---|
| `AWS_DEPLOY_ROLE_ARN` | GitHub repo secret | `cd-api` (OIDC `role-to-assume`) |
| `AWS_DEPLOY_ROLE_ARN_LAMBDAS` | GitHub repo secret | `cd-lambdas` (OIDC `role-to-assume`) |
| `DJANGO_SECRET_KEY` | SSM `/photo-feed/prod/DJANGO_SECRET_KEY` (SecureString) | `deploy.sh` → `.env` → Django |
| `POSTGRES_PASSWORD` | SSM `/photo-feed/prod/POSTGRES_PASSWORD` (SecureString) | `deploy.sh` → `.env` → compose → Postgres + Django |
| `WEBHOOK_SHARED_SECRET` | SSM `/photo-feed/prod/WEBHOOK_SHARED_SECRET` (SecureString) | `deploy.sh` → `.env` → Django; `cd-lambdas` reads it at deploy and passes via `--parameter-overrides` to cut_image |

Rule:

- **GitHub secrets** = what the pipeline needs to reach AWS.
- **SSM Parameter Store** = what the running app needs. KMS-encrypted,
  CloudTrail-audited, rotatable without touching the repo.

`WEBHOOK_SHARED_SECRET` is shared between Django and the cut_image
Lambda; the single source of truth is SSM. `cd-lambdas` reads it at
deploy time, masks the value with `::add-mask::` so it never lands
in workflow logs, and passes it as a CloudFormation parameter
override.

## cd-api — push to main → live on EC2

Triggers on `push: main` with `paths:` covering `packages/api/**`,
`docker-compose.prod.yml`, `infra/nginx/**`, `infra/ec2/**`, and the
workflow file itself.

Steps:

1. `actions/checkout@v4`.
2. `aws-actions/configure-aws-credentials@v4` — OIDC into the api
   deployer role.
3. `docker/setup-buildx-action@v3` — switches to the
   `docker-container` driver, needed by `cache-to: type=gha`.
4. `aws-actions/amazon-ecr-login@v2`.
5. Compute `IMAGE_URI` (`<registry>/photo-feed-api:<sha12>`) and a
   `:latest` tag.
6. `docker/build-push-action@v6` — build + push both tags, GHA cache
   for fast subsequent builds.
7. `aws ec2 describe-instances` to resolve the EC2 by tag
   `Application=photo-feed-api`.
8. `aws ssm send-command` — runs `deploy.sh` on the box:
   ```bash
   sudo -u ubuntu \
     AWS_REGION=eu-central-1 \
     ECR_REGISTRY=<registry> \
     ECR_REPO=photo-feed-api \
     IMAGE_TAG=<sha12> \
     bash infra/ec2/deploy.sh
   ```
   `sudo -u ubuntu VAR=… bash` (inline env) because Ubuntu sudoers
   strips `sudo -E` silently — `VAR=… ` form preserves env across the
   user switch deterministically.
9. Polling loop: every 10s, `aws ssm get-command-invocation` for the
   command id. Exits on `Success`; bails with stdout + stderr on
   `Failed` / `Cancelled` / `TimedOut`. Caps at 60 iterations (10 min).

### What `deploy.sh` does on the host

`/srv/photo-feed/infra/ec2/deploy.sh`:

```
1. Pull DJANGO_SECRET_KEY, POSTGRES_PASSWORD, WEBHOOK_SHARED_SECRET
   from SSM. Write them + IMAGE_URI into /srv/photo-feed/.env
   (atomic: write .env.new then rename).
2. ECR login: aws ecr get-login-password | docker login --password-stdin
3. docker pull $IMAGE_URI
4. docker compose -f docker-compose.prod.yml up -d --remove-orphans
   (recreates web because IMAGE_URI changed; db/redis/nginx/certbot
    stay up unless their image changed too)
5. docker compose ... exec -T web python manage.py migrate --noinput
6. Smoke test: curl https://photo-feed.gotdns.ch/api/health/ up to
   5 times with backoff. Exit 0 on 200, else exit 1 + dump web logs.
```

`IMAGE_URI` is written into `.env` (not just exported) because
`compose` re-reads `.env` from disk on every invocation — without it,
the next compose call would expand `image: ${IMAGE_URI}` to empty
and fail with `'neither an image nor a build context'`.

## cd-lambdas — push to main → live Lambdas

Triggers on `push: main` with `paths:` covering
`packages/cut_image/**`, `packages/generate_image/**`,
`infra/template-*.yaml`, and the workflow file.

Two jobs **in parallel** — `deploy-euc1` and `deploy-usw2`. Each:

1. `actions/checkout@v4`.
2. OIDC into `photo-feed-lambdas-github-actions`.
3. `aws-actions/setup-sam@v2` (binary installer).
4. `sam validate --lint`.
5. `sam build`.
6. `sam deploy --resolve-s3 --no-confirm-changeset
   --no-fail-on-empty-changeset --capabilities CAPABILITY_IAM`.

`deploy-euc1` has one extra step before `sam deploy`: pull
`WEBHOOK_SHARED_SECRET` from SSM with `--with-decryption`, mask the
value via `echo "::add-mask::$SECRET"`, and pass it via
`--parameter-overrides WebhookSharedSecret=…`. `deploy-usw2`
doesn't need it.

### What SAM creates per region

| Region | Stack | Resources |
|---|---|---|
| euc1 | `aws-sam-cli-managed-default` | S3 bucket for SAM artifacts |
| euc1 | `photo-feed-euc1` | S3 `photo-feed-uploads`, Lambda `photo-feed-cut-image`, exec-role, S3 event mapping on `raw/` prefix |
| usw2 | `aws-sam-cli-managed-default` | S3 bucket for SAM artifacts |
| usw2 | `photo-feed-usw2` | S3 `photo-feed-generated-usw2`, Lambda `photo-feed-generate-image`, exec-role with Bedrock InvokeModel scoped to Stability Core/Ultra/SD3.5 |

## Bootstrap a fresh EC2 (one-time, manual)

Everything below is the wiring that has to happen by hand before
`cd-api` can deploy.

### 1. Launch the instance

- AMI: Ubuntu 24.04 LTS.
- Type: `t3.small` (works) or `t3.medium` (more headroom for Postgres).
- Tags: **both** `Name=photo-feed-api` **and**
  `Application=photo-feed-api`. The workflow filters by
  `Application`; AWS console default is only `Name`.
- IAM instance profile: attach `PhotoFeedInstanceRole` (at launch or
  via Actions → Security → Modify IAM role).
- Allocate an Elastic IP and associate it.

### 2. Security group

```
80   tcp  0.0.0.0/0     (HTTP — Let's Encrypt ACME + 80→443 redirect)
443  tcp  0.0.0.0/0     (HTTPS — real traffic)
22   tcp  <your IP>/32  (SSH for bootstrap)
```

### 3. DNS → Elastic IP

NoIP A-record `photo-feed.gotdns.ch` → `<elastic-ip>`. Verify:

```bash
dig +short photo-feed.gotdns.ch
```

### 4. Install Docker + AWS CLI on the host

```bash
ssh photo-feed
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin awscli
sudo usermod -aG docker ubuntu
exit                 # log out so docker group takes effect
ssh photo-feed
docker --version && docker compose version && aws --version
```

### 5. Drop the prod config on the host

From your laptop, in the repo root:

```bash
ssh photo-feed 'sudo mkdir -p /srv/photo-feed/infra/nginx /srv/photo-feed/infra/ec2 && sudo chown -R ubuntu:ubuntu /srv/photo-feed'
scp docker-compose.prod.yml photo-feed:/srv/photo-feed/
scp infra/nginx/photo-feed.conf photo-feed:/srv/photo-feed/infra/nginx/
scp infra/ec2/deploy.sh photo-feed:/srv/photo-feed/infra/ec2/
ssh photo-feed 'chmod +x /srv/photo-feed/infra/ec2/deploy.sh'
```

### 6. First Let's Encrypt cert

nginx in compose mounts the cert from a named volume
(`certbot_data:/etc/letsencrypt:ro`), so it can't serve until a cert
exists. Bootstrap it with a standalone certbot run that binds port
80 itself:

```bash
ssh photo-feed
sudo docker run --rm -p 80:80 \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  certbot/certbot certonly --standalone \
  --non-interactive --agree-tos \
  --email <your-email> \
  -d photo-feed.gotdns.ch
```

The cert lands on the **host** at
`/etc/letsencrypt/live/photo-feed.gotdns.ch/`.

### 7. Copy the cert into the named volume

The host `/etc/letsencrypt/` is **not** the same storage as the named
volume. Compose's nginx will not see the cert until we copy it in.

```bash
# Create the volume first so its mountpoint exists. Project name comes
# from the compose dir name (here, photo-feed).
sudo docker volume create photo-feed_certbot_data
sudo cp -a /etc/letsencrypt/. /var/lib/docker/volumes/photo-feed_certbot_data/_data/
```

`cp -a` preserves the `live/`→`archive/` symlinks. Verify:

```bash
sudo ls -la /var/lib/docker/volumes/photo-feed_certbot_data/_data/live/photo-feed.gotdns.ch/
```

Expect four symlinks (`cert.pem`, `chain.pem`, `fullchain.pem`,
`privkey.pem`) plus a `README`.

### 8. Confirm SSM agent is online

From your laptop:

```bash
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=<instance-id>" \
  --profile cx9-gmail --region eu-central-1 \
  --query 'InstanceInformationList[].PingStatus' --output text
```

Must print `Online`. If empty / `ConnectionLost`, the instance
profile isn't attached or `amazon-ssm-agent` isn't running.

### 9. Trigger the first cd-api deploy

```bash
gh workflow run cd-api.yml --ref main
gh run watch
```

After this, every push to `main` (touching the api paths) deploys
itself.

## Failure modes seen during the first real deploy

| Symptom | Cause | Fix |
|---|---|---|
| `bash: infra/ec2/deploy.sh: No such file or directory` | `/srv/photo-feed/` not bootstrapped (step 5) | scp the configs |
| `ECR_REGISTRY must be set` | `sudo -E` ignored by Ubuntu sudoers | Workflow uses inline `sudo -u ubuntu VAR=…` form |
| `not authorized to perform: ssm:GetCommandInvocation` | Read action wrapped in a tag-Condition (command-invocation has no tags) | Split write (with Condition) and read (no Condition) into two statements |
| `not authorized to perform: cloudformation:CreateChangeSet on ...:transform/Serverless-2016-10-31` | Lambdas role missing the AWS-owned transform ARN | Add the `ServerlessTransform` statement |
| `aws-sam-cli-managed-default … missing Tags and/or Outputs … REVIEW_IN_PROGRESS` | Earlier SAM run created the stack stub but failed before tagging | `aws cloudformation delete-stack --stack-name aws-sam-cli-managed-default --region <r>` then re-run |
| `ModuleNotFoundError: No module named 'api'` | gunicorn doesn't go through `manage.py`, so `src/` isn't on `sys.path` | `PYTHONPATH=/app/packages/api/src` in compose `environment:` |
| `service "web" has neither an image nor a build context` | `.env` missing `IMAGE_URI` because only `export` was used, not `.env` write | `deploy.sh` writes `IMAGE_URI=…` into `.env` alongside the secrets |
| nginx `cannot load certificate ... no such file` | Cert on host, not in the named volume | Step 7 above |
