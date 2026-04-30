output "tf_state_bucket" {
  value       = aws_s3_bucket.terraform_state.id
  description = "Set this as MERIDIAN_STORES_TF_STATE_BUCKET in GitHub repository variables."
}

output "github_actions_role_arn" {
  value       = aws_iam_role.github_actions.arn
  description = "Set this as MERIDIAN_STORES_AWS_ROLE_TO_ASSUME in GitHub repository variables."
}
