# AWS Bootstrap

Run this once from a workstation with AWS administrator credentials. It creates:

- An encrypted, versioned S3 bucket for Terraform remote state.
- A GitHub Actions OIDC provider and deployment role for this repository.

```bash
cd infra/bootstrap
cp terraform.tfvars.example terraform.tfvars
# edit github_owner, github_repo, and optionally project/aws_region
terraform init
terraform apply
```

From the repository root, the equivalent Makefile flow is:

```bash
make bootstrap-init
make bootstrap-apply
```

Add these Terraform outputs to GitHub repository variables:

- `MERIDIAN_STORES_TF_STATE_BUCKET`: `tf_state_bucket`
- `MERIDIAN_STORES_AWS_ROLE_TO_ASSUME`: `github_actions_role_arn`
- `MERIDIAN_STORES_AWS_REGION`: the same region used here, default `us-east-1`
- `MERIDIAN_STORES_PROJECT`: your project slug, default `meridian-stores`

If you ran `scripts/init-project.sh` or `make init` with a different environment prefix, use that prefix instead. For example, `PREFIX=MYAPP` means `MYAPP_TF_STATE_BUCKET`, `MYAPP_AWS_ROLE_TO_ASSUME`, `MYAPP_AWS_REGION`, and `MYAPP_PROJECT`.

See `../../DEPLOY.md` for the complete GitHub variables/secrets checklist.

The starter role attaches `AdministratorAccess` so the template can deploy immediately. For production, replace `role_policy_arns` with a least-privilege policy after the first successful deploy.

If your AWS account already has a `token.actions.githubusercontent.com` OIDC provider, set `github_oidc_provider_arn` in `terraform.tfvars` instead of creating a duplicate provider.
