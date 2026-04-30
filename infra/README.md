# Meridian Stores Infra Notes

- **Docker Compose**: root `docker-compose.yml` builds/runs both tiers; set `PROJECT_NAME` in `config/.env` and run `make compose-up` so the Compose **project name** matches the API.
- **AWS app stack**: `infra/aws/` provisions **Lambda + HTTP API Gateway + ECR + S3 + CloudFront** and is wired to `.github/workflows/deploy-aws.yml` / `destroy-aws.yml`.
- **AWS bootstrap**: `infra/bootstrap/` creates the Terraform state bucket and GitHub OIDC role needed by CI/CD.
- **Nginx override**: `infra/nginx/default.conf.example` — copy/edit and mount over `/etc/nginx/conf.d/default.conf` when the API service name or port is not `api:8000`.
- **Terraform contract**: `infra/terraform/` — variables + outputs only; no resources. Copy `terraform.tfvars.example` → `terraform.tfvars` in your wrapper module.
