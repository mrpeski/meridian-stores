output "fastapi_react_aws_template_deploy_inputs" {
  description = "Echo of the knobs your outer Terraform module should pass into ECS/Kubernetes/etc."
  value = {
    project_name       = var.project_name
    api_image          = var.fastapi_react_aws_template_api_image != "" ? var.fastapi_react_aws_template_api_image : local.default_api_image
    web_image          = var.fastapi_react_aws_template_web_image != "" ? var.fastapi_react_aws_template_web_image : local.default_web_image
    api_port           = var.fastapi_react_aws_template_api_port
    web_port           = var.fastapi_react_aws_template_web_port
    public_hostname    = var.fastapi_react_aws_template_public_hostname
    api_desired_count  = var.fastapi_react_aws_template_api_desired_count
    api_env_prefix     = "MERIDIAN_STORES_"
    project_env_var    = "PROJECT_NAME"
    shared_config_file = "meridian-stores/config/.env (or your secret manager equivalent)"
  }
}
