---
title: "AWS DevOps Essentials"
sidebar:
  order: 0
  label: "AWS Essentials"
---
**Everything you need to be productive on AWS — before touching EKS.**

Not everything goes into Kubernetes. This track covers the core AWS services every DevOps engineer needs: identity, networking, compute, containers, serverless, secrets, observability, CI/CD, and infrastructure as code.

---

## Modules

| # | Module | Time | What You'll Learn |
|---|--------|------|-------------------|
| 1 | [AWS Identity & Access Management (IAM) Deep Dive](module-1.1-iam/) | 2h | Roles, policies, cross-account, permission boundaries |
| 2 | [Virtual Private Cloud (VPC) & Core Networking](module-1.2-vpc/) | 3h | Subnets, NAT, Security Groups, Transit Gateway |
| 3 | [Elastic Compute Cloud (EC2) & Compute Foundations](module-1.3-ec2/) | 2.5h | Instance types, Spot, ASGs, ALBs |
| 4 | [Amazon S3 & Object Storage](module-1.4-s3/) | 1.5h | Storage classes, lifecycle, bucket policies |
| 5 | [Route 53 & DNS Management](module-1.5-route53/) | 1.5h | Routing policies, health checks, DNSSEC |
| 6 | [Elastic Container Registry (ECR)](module-1.6-ecr/) | 1h | Image management, scanning, lifecycle |
| 7 | [Elastic Container Service (ECS) & Fargate](module-1.7-ecs-fargate/) | 3h | Standalone containers without K8s |
| 8 | [AWS Lambda & Serverless Patterns](module-1.8-lambda/) | 2h | Triggers, cold starts, Step Functions |
| 9 | [Secrets Management & Configuration](module-1.9-secrets/) | 1.5h | SSM, Secrets Manager, KMS |
| 10 | [CloudWatch & Observability](module-1.10-cloudwatch/) | 2h | Metrics, alarms, logs, X-Ray |
| 11 | [CI/CD on AWS (Code Suite)](module-1.11-cicd/) | 2h | CodePipeline, CodeBuild, GitHub Actions OIDC |
| 12 | [Infrastructure as Code on AWS](module-1.12-cloudformation/) | 1.5h | Templates, stacks, CDK overview |
| 13 | [AWS Data Ingestion + Transformation](module-1.13-data-ingestion/) | 2h | Kinesis, Firehose, Glue, Athena |

**Total time**: ~25 hours

---

## Prerequisites

- [Cloud Native 101](../../prerequisites/cloud-native-101/) — containers, Docker basics
- [Hyperscaler Rosetta Stone](../hyperscaler-rosetta-stone/) — recommended

## What's Next

After AWS Essentials, continue to [AWS EKS Deep Dive](../eks-deep-dive/) for production Kubernetes on AWS.
