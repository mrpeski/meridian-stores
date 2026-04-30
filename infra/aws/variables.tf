variable "aws_region" {
  type    = string
  default = "us-east-1"
}

# Keep aligned with meridian-stores `PROJECT_NAME` / Terraform `project_name` convention.
variable "project" {
  type        = string
  default     = "meridian-stores"
  description = "Name prefix for AWS resources (ECR, Lambda, API Gateway, tags)."
}

variable "lambda_memory_mb" {
  type        = number
  default     = 256
  description = "Lambda memory for the minimal meridian-stores API."
}

variable "lambda_timeout_sec" {
  type    = number
  default = 30
}

variable "env_vars" {
  type        = map(string)
  default     = {}
  description = "Extra Lambda environment variables (e.g. PROJECT_NAME, MERIDIAN_STORES_*)."
}

variable "secret_env_vars" {
  type        = map(string)
  sensitive   = true
  default     = {}
  description = "Sensitive Lambda env vars (same trade-offs as main infra/variables.tf)."
}

variable "cors_allow_origin" {
  type        = string
  default     = "*"
  description = "Browser origin allowed by API Gateway CORS and forwarded to FastAPI as MERIDIAN_STORES_CORS_ORIGINS."
}

variable "clerk_enabled" {
  type        = bool
  default     = false
  description = "When true, Lambda receives CLERK_ENABLED, CLERK_ISSUER, CLERK_JWKS_URL (match SPA VITE_CLERK_PUBLISHABLE_KEY if you add Clerk to the API)."
}

variable "clerk_issuer" {
  type        = string
  default     = ""
  description = "Clerk Frontend API URL (JWT iss), e.g. https://xxx.clerk.accounts.com"
}

variable "clerk_jwks_url" {
  type        = string
  default     = ""
  description = "Clerk JWKS URL, e.g. https://xxx.clerk.accounts.com/.well-known/jwks.json"
}

data "aws_caller_identity" "me" {}

resource "random_id" "suffix" {
  byte_length = 3
}

locals {
  name        = var.project
  bucket_name = "${var.project}-web-${data.aws_caller_identity.me.account_id}-${random_id.suffix.hex}"
  image_uri   = "${aws_ecr_repository.api.repository_url}:latest"
}
