# Meridian Stores AWS Stack

This folder is a standalone AWS starter stack:

| Piece | AWS service | Notes |
| --- | --- | --- |
| API | **Lambda** (container) + **HTTP API Gateway** | `ANY /{proxy+}` → Lambda Web Adapter → uvicorn. |
| Frontend | **S3** static website + **CloudFront** | SPA fallback + HTTPS default cert. |
| Images | **ECR** | CI (or you) push `:latest`; Terraform pins initial image; `lifecycle.ignore_changes` on `image_uri` matches root infra. |

## First Deploy

1. Run `infra/bootstrap` once to create the S3 state bucket and GitHub OIDC role.
2. Add the bootstrap outputs as GitHub repository variables.
3. Run the `Deploy AWS` workflow manually from GitHub Actions.

The deploy workflow intentionally applies `aws_ecr_repository.api` first, pushes the Lambda image, then applies the full stack. That avoids the first-deploy Lambda/ECR chicken-and-egg problem.

If you initialized the template with a custom prefix, use that prefix for GitHub variables. For example, `PREFIX=MYAPP` means `MYAPP_TF_STATE_BUCKET`, `MYAPP_AWS_ROLE_TO_ASSUME`, `MYAPP_AWS_REGION`, and `MYAPP_PROJECT`.

See `../../DEPLOY.md` for the full GitHub variables/secrets checklist.

## Quick apply (local state)

From this directory:

```bash
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply
```

The Makefile wrappers use remote state and are better aligned with CI/CD:

```bash
make aws-plan TF_STATE_BUCKET=<state-bucket>
make aws-apply TF_STATE_BUCKET=<state-bucket>
```

Then build and push the **Lambda** image (must be **linux/amd64**):

```bash
cd ../../backend
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build --platform linux/amd64 -f Dockerfile.lambda -t $(terraform -chdir=../aws output -raw ecr_repo):latest .
docker push $(terraform -chdir=../aws output -raw ecr_repo):latest
aws lambda update-function-code --function-name $(terraform -chdir=../aws output -raw lambda_function_name) --image-uri $(terraform -chdir=../aws output -raw ecr_repo):latest
```

(Adjust paths if you run commands from a different working directory.)

## Frontend build vs API URL

Production SPA needs the API Gateway origin at **build time** (same as main app’s `VITE_API_BASE_URL`). After first `terraform apply`, set that to `api_url` output, rebuild `meridian-stores/frontend`, sync `dist/` to `frontend_bucket`, invalidate `cloudfront_distribution_id`.

## Destroy

Use the **Destroy AWS** GitHub Actions workflow for the easiest teardown. It is manual-only and requires typing `DESTROY`.

For local teardown:

```bash
cp backend.tf.example backend.tf
terraform init -backend-config=bucket=<state-bucket> -backend-config=region=us-east-1
terraform destroy
```

Or:

```bash
make aws-destroy TF_STATE_BUCKET=<state-bucket>
```

This destroys the application stack in `infra/aws`. It does not destroy `infra/bootstrap`; keep bootstrap resources if you plan to deploy again, or destroy them separately from `infra/bootstrap` after all stacks using that state bucket and OIDC role are gone.

## Remote state

Remote state is opt-in so local validation and quick applies can use local state. The deploy and destroy workflows copy [`backend.tf.example`](./backend.tf.example) to `backend.tf` before initializing Terraform. For local remote-state commands, use the Makefile wrappers, or run:

```bash
cp backend.tf.example backend.tf
terraform init -backend-config=bucket=<state-bucket> -backend-config=region=us-east-1
```
