variable "project_name" {
  type        = string
  description = "Slug for this stack (Compose project name, default image tags, API PROJECT_NAME)."
  default     = "meridian-stores"
}

variable "fastapi_react_aws_template_api_image" {
  type        = string
  description = "OCI image for the FastAPI service. Leave empty to use \"{project_name}-api:local\"."
  default     = ""
}

variable "fastapi_react_aws_template_web_image" {
  type        = string
  description = "OCI image for the static UI + reverse proxy. Leave empty to use \"{project_name}-web:local\"."
  default     = ""
}

variable "fastapi_react_aws_template_api_port" {
  type        = number
  description = "Container port the API listens on (must match MERIDIAN_STORES_API_PORT inside the image)."
  default     = 8000
}

variable "fastapi_react_aws_template_web_port" {
  type        = number
  description = "Container port the web tier listens on (nginx default 80 unless you change the image)."
  default     = 80
}

variable "fastapi_react_aws_template_public_hostname" {
  type        = string
  description = "Hostname users open in the browser (used for documentation / outputs only)."
  default     = "meridian-stores.example.com"
}

variable "fastapi_react_aws_template_api_desired_count" {
  type        = number
  description = "Example placement hint for schedulers (documented only; not used by resources in this stub)."
  default     = 1
}
