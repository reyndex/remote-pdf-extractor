# ---------- APIs ----------

resource "google_project_service" "cloud_functions_api" {
  service            = "cloudfunctions.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_build_api" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_run_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry_api" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_storage_api" {
  service            = "storage.googleapis.com"
  disable_on_destroy = false
}

# ---------- Source bucket ----------

resource "google_storage_bucket" "function_source" {
  name                        = local.function_source_bucket
  location                    = var.gcp_region
  uniform_bucket_level_access = true
  force_destroy               = true
  labels                      = local.resource_labels

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 3
    }
    action {
      type = "Delete"
    }
  }

  lifecycle {
    precondition {
      condition     = length(local.function_source_bucket) <= 63 && can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", local.function_source_bucket))
      error_message = "The function source bucket name must be 63 characters or fewer and contain only lowercase letters, numbers, and hyphens. Adjust resource_name_prefix."
    }
  }
}

# ---------- Source archive ----------

resource "google_storage_bucket_object" "function_source_archive" {
  # Keep object name stable so GCS versioning can retain only latest generations.
  name           = local.function_source_object
  bucket         = google_storage_bucket.function_source.name
  source         = local.function_source_zip
  source_md5hash = local.function_source_hash

  lifecycle {
    precondition {
      condition     = local.function_source_exists
      error_message = "Missing ../package/gcp-cloud-function.zip. Run ./scripts/build-function-zip.sh from the repository root before terraform apply."
    }
  }
}

# ---------- Cloud Function (2nd gen) ----------

resource "google_cloudfunctions2_function" "remote_pdf_extractor" {
  name     = local.cloud_function_name
  location = var.gcp_region
  labels   = local.resource_labels

  build_config {
    # Google Cloud's runtime ID for Python 3.13 is python313.
    runtime         = "python313"
    entry_point     = "extract_document"
    service_account = local.service_account_resource_name
    environment_variables = {
      GOOGLE_VENDOR_PIP_DEPENDENCIES = local.function_vendor_directory
    }

    source {
      storage_source {
        bucket     = google_storage_bucket.function_source.name
        object     = google_storage_bucket_object.function_source_archive.name
        generation = google_storage_bucket_object.function_source_archive.generation
      }
    }
  }

  service_config {
    max_instance_count    = var.max_instance_count
    min_instance_count    = var.min_instance_count
    available_memory      = var.available_memory
    available_cpu         = var.available_cpu
    timeout_seconds       = var.timeout_seconds
    ingress_settings      = var.ingress_settings
    service_account_email = local.service_account_email
  }

  depends_on = [
    google_project_service.cloud_functions_api,
    google_project_service.cloud_build_api,
    google_project_service.cloud_run_api,
    google_project_service.artifact_registry_api,
    google_project_service.cloud_storage_api,
  ]

  lifecycle {
    precondition {
      condition     = length(local.cloud_function_name) <= 63 && can(regex("^[a-z]([-a-z0-9]*[a-z0-9])?$", local.cloud_function_name))
      error_message = "The Cloud Function name must be 63 characters or fewer, start with a lowercase letter, and contain only lowercase letters, numbers, and hyphens. Adjust resource_name_prefix."
    }
  }
}

# ---------- IAM: the same service account is allowed to invoke ----------

resource "google_cloud_run_service_iam_member" "function_invoker" {
  project  = google_cloudfunctions2_function.remote_pdf_extractor.project
  location = google_cloudfunctions2_function.remote_pdf_extractor.location
  service  = google_cloudfunctions2_function.remote_pdf_extractor.name
  role     = "roles/run.invoker"
  member   = local.service_account_member
}
