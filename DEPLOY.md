# Deploy To AWS

This template deploys to AWS with GitHub Actions, Terraform, Docker, Lambda, API Gateway, ECR, S3, and CloudFront.

Important: the variable/secret prefix is project-specific. The tables use this checkout's current prefix. In a fresh template copy, that is the starter prefix; after `make init`, this file is rewritten to the selected project prefix. Use the prefix shown in your initialized copy.

Examples:

| Init command | GitHub variable/secret prefix |
| --- | --- |
| `make init PROJECT=my-calendar NAME="My Calendar"` | `MY_CALENDAR_*` |
| `make init PROJECT=my-calendar NAME="My Calendar" PREFIX=VOICECAL` | `VOICECAL_*` |

The tables below show the current prefix for this checkout. If you have not initialized the template yet, initialize it before adding GitHub variables/secrets.

## 1. Bootstrap AWS

Run this once from a machine with AWS administrator credentials:

```bash
cd infra/bootstrap
cp terraform.tfvars.example terraform.tfvars
# edit github_owner, github_repo, github_branch, project, and aws_region
terraform init
terraform apply
```

Or from the repo root:

```bash
make bootstrap-init
make bootstrap-apply
```

Bootstrap creates:

- An encrypted S3 bucket for Terraform remote state.
- A GitHub Actions OIDC role allowed to deploy from the configured repo and branch.

If your AWS account already has a `token.actions.githubusercontent.com` OIDC provider, set `github_oidc_provider_arn` in `infra/bootstrap/terraform.tfvars`.

## 2. Add GitHub Repository Variables

Add these under **GitHub repo → Settings → Secrets and variables → Actions → Variables**.

Use the same prefix shown in the table below.

Required:

| Variable | Value |
| --- | --- |
| `MERIDIAN_STORES_TF_STATE_BUCKET` | Output `tf_state_bucket` from `infra/bootstrap` |
| `MERIDIAN_STORES_AWS_ROLE_TO_ASSUME` | Output `github_actions_role_arn` from `infra/bootstrap` |
| `MERIDIAN_STORES_PROJECT` | Project slug, for example `meridian-stores` |

Recommended:

| Variable | Default | Purpose |
| --- | --- | --- |
| `MERIDIAN_STORES_AWS_REGION` | `us-east-1` | AWS region for Terraform, ECR, Lambda, and API Gateway |
| `MERIDIAN_STORES_CORS_ALLOW_ORIGIN` | `*` | Browser origin allowed by API Gateway and FastAPI CORS |

Optional Clerk variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `MERIDIAN_STORES_CLERK_ENABLED` | `false` | Set to `true` only if the API uses Clerk |
| `MERIDIAN_STORES_CLERK_ISSUER` | empty | Clerk JWT issuer |
| `MERIDIAN_STORES_CLERK_JWKS_URL` | empty | Clerk JWKS URL |

Fallback names are also supported by the workflows:

| Preferred | Fallback |
| --- | --- |
| `MERIDIAN_STORES_AWS_ROLE_TO_ASSUME` | `AWS_ROLE_TO_ASSUME` |
| `MERIDIAN_STORES_AWS_REGION` | `AWS_REGION` |
| `MERIDIAN_STORES_TF_STATE_BUCKET` | `TF_STATE_BUCKET` |
| `MERIDIAN_STORES_CORS_ALLOW_ORIGIN` | `CORS_ALLOW_ORIGIN` |
| `MERIDIAN_STORES_CLERK_ISSUER` | `CLERK_ISSUER` |
| `MERIDIAN_STORES_CLERK_JWKS_URL` | `CLERK_JWKS_URL` |

## 3. Add GitHub Secrets

Secrets are optional for the meridian-stores app. Add this only if your Lambda needs sensitive environment variables.

Add under **GitHub repo → Settings → Secrets and variables → Actions → Secrets**:

Use the same prefix shown in the table below.

| Secret | Value |
| --- | --- |
| `MERIDIAN_STORES_SECRET_ENV_VARS_JSON` | JSON object merged into Lambda environment variables |

Example:

```json
{
  "OPENAI_API_KEY": "sk-...",
  "ANTHROPIC_API_KEY": "...",
  "GOOGLE_CLIENT_ID": "...",
  "GOOGLE_CLIENT_SECRET": "...",
  "GOOGLE_REFRESH_TOKEN": "..."
}
```

Use a single-line JSON value in GitHub Secrets. Leave it unset if there are no secrets.

## 4. Deploy

Deployment is handled by `.github/workflows/deploy-aws.yml`.

It is manual-only by default so you can test CI before deploying. Run it from **Actions → Deploy AWS → Run workflow** when you are ready.

The workflow:

- Initializes Terraform with the remote state bucket.
- Creates the ECR repository first if needed.
- Builds and pushes the Lambda image for `linux/amd64`.
- Applies the full AWS stack.
- Updates Lambda to the image for the current commit SHA.
- Builds the frontend with `VITE_API_BASE_URL` set to the API Gateway URL.
- Syncs `frontend/dist` to S3 and invalidates CloudFront.

## 5. Destroy

The easiest teardown is **Actions → Destroy AWS → Run workflow** and type:

```text
DESTROY
```

This destroys only the application stack in `infra/aws`. It intentionally leaves bootstrap resources in place so the Terraform state bucket and GitHub OIDC role can be reused.

For local teardown:

```bash
make aws-destroy TF_STATE_BUCKET=<state-bucket>
```

Destroy `infra/bootstrap` separately only after all stacks using that state bucket and OIDC role are gone.

## Prefix Check

Add GitHub variables and secrets with the exact prefix shown in this file after initialization. Do not mix prefixes from an older template copy. For example, if the initializer prints `Environment prefix: MY_CALENDAR_`, add `MY_CALENDAR_TF_STATE_BUCKET`, `MY_CALENDAR_AWS_ROLE_TO_ASSUME`, and `MY_CALENDAR_SECRET_ENV_VARS_JSON`.
