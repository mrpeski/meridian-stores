terraform {
  required_version = ">= 1.5"
}

# This folder is a **variable contract** only: wire these inputs from your own root module
# (VPC, ECS/Kubernetes, etc.). No cloud resources are created here on purpose.

locals {
  project_name      = var.project_name
  default_api_image = "${local.project_name}-api:local"
  default_web_image = "${local.project_name}-web:local"
}
