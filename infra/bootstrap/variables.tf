variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type        = string
  default     = "meridian-stores"
  description = "Project slug used for bootstrap resource names."
}

variable "github_owner" {
  type        = string
  description = "GitHub organization or username that owns the repository."
}

variable "github_repo" {
  type        = string
  description = "GitHub repository name."
}

variable "github_branch" {
  type        = string
  default     = "main"
  description = "Branch allowed to assume the deployment role."
}

variable "state_bucket_name" {
  type        = string
  default     = ""
  description = "Optional explicit Terraform state bucket name. Defaults to <project>-tfstate-<account-id>."
}

variable "role_name" {
  type        = string
  default     = ""
  description = "Optional explicit GitHub OIDC role name. Defaults to <project>-github-actions."
}

variable "github_oidc_provider_arn" {
  type        = string
  default     = ""
  description = "Optional existing token.actions.githubusercontent.com OIDC provider ARN. Leave empty to create one."
}

variable "role_policy_arns" {
  type        = list(string)
  default     = ["arn:aws:iam::aws:policy/AdministratorAccess"]
  description = "Policies attached to the GitHub Actions role. Tighten this after the starter deploys."
}
