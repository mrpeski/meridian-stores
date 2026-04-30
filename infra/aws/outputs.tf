output "ecr_repo" {
  value       = aws_ecr_repository.api.repository_url
  description = "ECR registry URL (no tag). Push linux/amd64 image built from meridian-stores/backend/Dockerfile.lambda."
}

output "lambda_function_name" {
  value = aws_lambda_function.api.function_name
}

output "api_url" {
  value       = aws_apigatewayv2_api.api.api_endpoint
  description = "HTTP API Gateway base URL — set as VITE_API_BASE_URL (no trailing slash) when building the SPA."
}

output "frontend_bucket" {
  value = aws_s3_bucket.web.id
}

output "frontend_url" {
  value       = "https://${aws_cloudfront_distribution.web.domain_name}"
  description = "HTTPS CloudFront URL — use in the browser and tighten cors_allow_origin after first deploy."
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.web.id
  description = "Pass to aws cloudfront create-invalidation after syncing new frontend assets."
}
