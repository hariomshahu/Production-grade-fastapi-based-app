terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Local backend for learning; for production use S3 + DynamoDB for state locking
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for all resources"
}

variable "project_name" {
  type        = string
  default     = "items-crud"
  description = "Project name for tagging"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment (dev, staging, prod)"
}

variable "app_repo_url" {
  type        = string
  description = "Git repo URL to clone for app (e.g. https://github.com/you/items-crud.git). Must be public or use SSH key on instances."

  validation {
    condition     = length(var.app_repo_url) > 0
    error_message = "app_repo_url must be set (e.g. in terraform.tfvars or -var app_repo_url=...)."
  }
}

variable "app_repo_branch" {
  type        = string
  default     = "main"
  description = "Branch to checkout"
}
