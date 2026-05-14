variable "resource_name_prefix" {
  description = "Optional base name for cloud resources. Defaults to remote-pdf-extractor."
  type        = string
  default     = ""
}

variable "environment" {
  description = "Optional deployment label for resource labels. When empty, derive from Terraform workspace or fall back to shared."
  type        = string
  default     = ""
}

variable "gcp_project_id" {
  description = "Google Cloud project ID where the Cloud Function will be deployed"
  type        = string
}

variable "gcp_region" {
  description = "Google Cloud region for the Cloud Function"
  type        = string
  default     = "us-central1"
}

variable "billing_project_override" {
  description = "Optional billing project for the Terraform provider itself when required by your auth setup"
  type        = string
  default     = ""
}

variable "service_account_email" {
  description = "Service account email used for Terraform credentials, Cloud Build, Cloud Function runtime, and function invocation"
  type        = string

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.iam\\.gserviceaccount\\.com$", trimspace(var.service_account_email)))
    error_message = "service_account_email must be a service account email, for example remote-pdf-extractor@PROJECT_ID.iam.gserviceaccount.com."
  }
}

variable "ingress_settings" {
  description = "Ingress mode for the Cloud Function HTTP endpoint"
  type        = string
  default     = "ALLOW_ALL"

  validation {
    condition = contains(
      ["ALLOW_ALL", "ALLOW_INTERNAL_ONLY", "ALLOW_INTERNAL_AND_GCLB"],
      var.ingress_settings,
    )
    error_message = "ingress_settings must be ALLOW_ALL, ALLOW_INTERNAL_ONLY, or ALLOW_INTERNAL_AND_GCLB."
  }
}

variable "max_instance_count" {
  description = "Maximum number of Cloud Function instances"
  type        = number
  default     = 10
}

variable "min_instance_count" {
  description = "Minimum number of Cloud Function instances (0 = scale to zero)"
  type        = number
  default     = 0
}

variable "available_memory" {
  description = "Memory allocated to each Cloud Function instance"
  type        = string
  default     = "512Mi"
}

variable "timeout_seconds" {
  description = "Maximum execution time for the Cloud Function in seconds"
  type        = number
  default     = 120
}

variable "available_cpu" {
  description = "CPU allocated to each Cloud Function instance"
  type        = string
  default     = "1"
}
