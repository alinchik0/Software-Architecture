# infrastructure/terraform/main.tf
terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

# 1. Создаем выделенный namespace для приложения
resource "kubernetes_namespace" "app_namespace" {
  metadata {
    name = "micromusic"
    labels = {
      environment = "development"
      managed-by  = "terraform"
    }
  }
}

# 2. Создаем ServiceAccount для микросервисов (принцип наименьших привилегий)
resource "kubernetes_service_account" "app_sa" {
  metadata {
    name      = "microservices-sa"
    namespace = kubernetes_namespace.app_namespace.metadata[0].name
  }
}

# 3. Создаем базовый Secret для учетных данных (пример)
resource "kubernetes_secret" "db_credentials" {
  metadata {
    name      = "db-credentials"
    namespace = kubernetes_namespace.app_namespace.metadata[0].name
  }
  data = {
    username = "postgres"
    password = "postgres" # В продакшене использовать external secrets manager
  }
  type = "Opaque"
}