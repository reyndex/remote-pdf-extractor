terraform {
  backend "remote" {
    organization = "core-services"

    workspaces {
      prefix = "remote-pdf-extractor-gcp-"
    }
  }

  required_version = ">= 1.15.3"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}
