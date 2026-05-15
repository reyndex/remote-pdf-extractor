terraform {
  backend "remote" {
    organization = "core-services"

    workspaces {
      prefix = "remote-pdf-extractor-aws-"
    }
  }

  required_version = ">= 1.15.3"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
