---
title: "Module 7.5: AWS CloudFormation"
slug: platform/toolkits/infrastructure-networking/iac-tools/module-7.5-cloudformation
sidebar:
  order: 6
---
## Complexity: [COMPLEX]
## Time to Complete: 90 minutes

---

## Prerequisites

Before starting this module, you should have completed:
- [Module 6.1: IaC Fundamentals](../../disciplines/delivery-automation/iac/module-6.1-iac-fundamentals/)
- [Module 7.1: Terraform Deep Dive](module-7.1-terraform/) (for comparison)
- AWS account with administrator access
- Basic understanding of AWS services

---

## Why This Module Matters

*The deployment screen blinked red: "ROLLBACK_COMPLETE."*

It was 2:47 AM when the healthcare startup's engineering lead realized their Terraform state file was corrupted. Three production databases, two Lambda functions, and an entire VPC—all managed by state that now showed conflicting information. The state file said the resources existed. AWS said they didn't. Manual intervention would take hours.

Then she remembered: their compliance team had mandated CloudFormation for patient data infrastructure. Those stacks were untouched. CloudFormation's state lives in AWS—not in a file that can corrupt. Within 15 minutes, she created a new CloudFormation stack, imported the orphaned resources, and production was stable.

**CloudFormation isn't sexy.** It doesn't have Terraform's ecosystem or Pulumi's programming languages. But when AWS is your entire world—when you need native integration, automatic rollbacks, and state that can't corrupt—CloudFormation delivers.

**This module teaches you** CloudFormation's architecture, template design, stack management, and when to choose it over alternatives. You'll learn to leverage AWS-native features that third-party tools can't match.

---

## War Story: The Accidental Multi-Region Disaster Recovery

**Characters:**
- Chen: Cloud Architect (5 years AWS experience)
- Finance Corp: 500-person financial services company
- Compliance: SOC 2 + PCI DSS requirements

**The Incident:**

Finance Corp needed disaster recovery across regions—a compliance requirement. Chen had built everything in Terraform, but the DR project revealed problems:

**Timeline:**

```
Month 1: DR Project Begins
         Requirement: Replicate production to us-west-2
         Chen: "Easy, I'll duplicate the Terraform"

Week 2:  Reality hits
         - State file per region = state coordination nightmare
         - Cross-region references require complex data sources
         - Terraform doesn't support StackSets (multi-region deployment)

Week 4:  First DR test fails
         - us-west-2 resources created out of order
         - Dependencies between regions not handled
         - Manual intervention required

Week 6:  Compliance audit approaching
         Auditor: "Show me automated DR failover"
         Chen: "Um... we have scripts?"

Week 7:  Chen discovers CloudFormation StackSets
         - Single template deploys to multiple regions
         - Built-in dependency ordering
         - Native AWS service = native AWS compliance

Week 8:  Migration begins
         - Day 1: Convert VPC template
         - Day 2: Convert RDS with cross-region read replicas
         - Day 3: Convert Lambda + API Gateway
         - Day 4: StackSet deployment to both regions
         - Day 5: DR test... success!

Week 9:  Compliance audit
         Auditor: "How do you ensure consistency across regions?"
         Chen: Shows StackSets console
         Auditor: "This is exactly what we need"

         Audit: PASSED
```

**What CloudFormation Provided:**

1. **StackSets**: One template, multiple regions/accounts, automatic consistency
2. **Native drift detection**: AWS detects changes made outside CloudFormation
3. **Service-linked resources**: Some AWS features only work with CloudFormation
4. **Compliance documentation**: CloudFormation templates = auditable infrastructure

**Lessons Learned:**
1. Native tools have native advantages
2. Multi-region is CloudFormation's strength
3. Compliance teams love AWS-native solutions
4. "Best tool" depends on the use case

---

## CloudFormation Architecture

### How CloudFormation Works

```
┌─────────────────────────────────────────────────────────────────┐
│                   CLOUDFORMATION ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     TEMPLATE                              │   │
│  │  (YAML/JSON)                                              │   │
│  │                                                           │   │
│  │  • Parameters                                             │   │
│  │  • Resources                                              │   │
│  │  • Outputs                                                │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               CLOUDFORMATION SERVICE                      │   │
│  │                                                           │   │
│  │  • Parses template                                        │   │
│  │  • Determines dependencies                                │   │
│  │  • Orchestrates API calls                                 │   │
│  │  • Tracks state (SERVER-SIDE)                            │   │
│  │  • Handles rollbacks                                      │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            │                                     │
│            ┌───────────────┼───────────────┐                    │
│            ▼               ▼               ▼                    │
│       ┌────────┐      ┌────────┐      ┌────────┐               │
│       │  EC2   │      │  RDS   │      │  S3    │               │
│       │  API   │      │  API   │      │  API   │               │
│       └────────┘      └────────┘      └────────┘               │
│                                                                  │
│  STATE LIVES IN AWS (not in files you manage)                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### CloudFormation vs. Terraform: Honest Comparison

| Aspect | CloudFormation | Terraform |
|--------|---------------|-----------|
| **State management** | AWS-managed (can't corrupt) | File-based (your responsibility) |
| **Multi-cloud** | AWS only | Multi-cloud |
| **New AWS features** | Day-0 support | Days-to-weeks delay |
| **Language** | YAML/JSON (verbose) | HCL (concise) |
| **Rollback** | Automatic on failure | Manual |
| **Drift detection** | Native | Requires `terraform plan` |
| **Multi-region** | StackSets (built-in) | Requires modules/workspaces |
| **Cross-account** | StackSets (built-in) | Complex provider configuration |
| **Learning curve** | Steep (AWS-specific) | Moderate (transferable skills) |
| **Community modules** | Limited | Extensive |
| **IDE support** | Basic | Excellent |

**When to choose CloudFormation:**
- AWS-only environment
- Compliance requirements favor native tools
- Need multi-region/multi-account deployment (StackSets)
- Using AWS services that require CloudFormation (Service Catalog, Control Tower)
- Worried about state file management

**When to choose Terraform:**
- Multi-cloud environment
- Team prefers HCL syntax
- Need extensive community modules
- Already have Terraform expertise

---

## Template Anatomy

### Complete Template Structure

```yaml
# infrastructure/vpc-template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: |
  Production VPC with public and private subnets across 3 AZs.
  Includes NAT Gateways, Internet Gateway, and flow logs.

# ============================================
# METADATA - Template documentation
# ============================================
Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: Network Configuration
        Parameters:
          - Environment
          - VPCCidr
          - EnableFlowLogs
      - Label:
          default: Availability Zone Configuration
        Parameters:
          - AZ1
          - AZ2
          - AZ3
    ParameterLabels:
      Environment:
        default: Environment Name
      VPCCidr:
        default: VPC CIDR Block

# ============================================
# PARAMETERS - User inputs
# ============================================
Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues:
      - development
      - staging
      - production
    Description: Environment name for tagging

  VPCCidr:
    Type: String
    Default: 10.0.0.0/16
    AllowedPattern: ^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$
    Description: CIDR block for the VPC

  EnableFlowLogs:
    Type: String
    Default: 'true'
    AllowedValues:
      - 'true'
      - 'false'
    Description: Enable VPC Flow Logs

  AZ1:
    Type: AWS::EC2::AvailabilityZone::Name
    Description: First Availability Zone

  AZ2:
    Type: AWS::EC2::AvailabilityZone::Name
    Description: Second Availability Zone

  AZ3:
    Type: AWS::EC2::AvailabilityZone::Name
    Description: Third Availability Zone

# ============================================
# MAPPINGS - Static lookup tables
# ============================================
Mappings:
  SubnetConfig:
    Public1:
      CIDR: 10.0.1.0/24
    Public2:
      CIDR: 10.0.2.0/24
    Public3:
      CIDR: 10.0.3.0/24
    Private1:
      CIDR: 10.0.11.0/24
    Private2:
      CIDR: 10.0.12.0/24
    Private3:
      CIDR: 10.0.13.0/24
    Database1:
      CIDR: 10.0.21.0/24
    Database2:
      CIDR: 10.0.22.0/24
    Database3:
      CIDR: 10.0.23.0/24

  EnvironmentConfig:
    development:
      NATGatewayCount: 1
    staging:
      NATGatewayCount: 2
    production:
      NATGatewayCount: 3

# ============================================
# CONDITIONS - Conditional logic
# ============================================
Conditions:
  CreateFlowLogs: !Equals [!Ref EnableFlowLogs, 'true']
  IsProduction: !Equals [!Ref Environment, 'production']
  CreateNAT2: !Or
    - !Equals [!Ref Environment, 'staging']
    - !Equals [!Ref Environment, 'production']
  CreateNAT3: !Equals [!Ref Environment, 'production']

# ============================================
# RESOURCES - AWS resources to create
# ============================================
Resources:
  # ----- VPC -----
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VPCCidr
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-vpc
        - Key: Environment
          Value: !Ref Environment

  # ----- Internet Gateway -----
  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-igw

  InternetGatewayAttachment:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  # ----- Public Subnets -----
  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Ref AZ1
      CidrBlock: !FindInMap [SubnetConfig, Public1, CIDR]
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-public-1
        - Key: kubernetes.io/role/elb
          Value: '1'

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Ref AZ2
      CidrBlock: !FindInMap [SubnetConfig, Public2, CIDR]
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-public-2
        - Key: kubernetes.io/role/elb
          Value: '1'

  PublicSubnet3:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Ref AZ3
      CidrBlock: !FindInMap [SubnetConfig, Public3, CIDR]
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-public-3
        - Key: kubernetes.io/role/elb
          Value: '1'

  # ----- Private Subnets -----
  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Ref AZ1
      CidrBlock: !FindInMap [SubnetConfig, Private1, CIDR]
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-private-1
        - Key: kubernetes.io/role/internal-elb
          Value: '1'

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Ref AZ2
      CidrBlock: !FindInMap [SubnetConfig, Private2, CIDR]
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-private-2
        - Key: kubernetes.io/role/internal-elb
          Value: '1'

  PrivateSubnet3:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Ref AZ3
      CidrBlock: !FindInMap [SubnetConfig, Private3, CIDR]
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-private-3
        - Key: kubernetes.io/role/internal-elb
          Value: '1'

  # ----- NAT Gateways -----
  NATGateway1EIP:
    Type: AWS::EC2::EIP
    DependsOn: InternetGatewayAttachment
    Properties:
      Domain: vpc
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-nat-1-eip

  NATGateway1:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt NATGateway1EIP.AllocationId
      SubnetId: !Ref PublicSubnet1
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-nat-1

  NATGateway2EIP:
    Type: AWS::EC2::EIP
    Condition: CreateNAT2
    DependsOn: InternetGatewayAttachment
    Properties:
      Domain: vpc
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-nat-2-eip

  NATGateway2:
    Type: AWS::EC2::NatGateway
    Condition: CreateNAT2
    Properties:
      AllocationId: !GetAtt NATGateway2EIP.AllocationId
      SubnetId: !Ref PublicSubnet2
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-nat-2

  NATGateway3EIP:
    Type: AWS::EC2::EIP
    Condition: CreateNAT3
    DependsOn: InternetGatewayAttachment
    Properties:
      Domain: vpc
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-nat-3-eip

  NATGateway3:
    Type: AWS::EC2::NatGateway
    Condition: CreateNAT3
    Properties:
      AllocationId: !GetAtt NATGateway3EIP.AllocationId
      SubnetId: !Ref PublicSubnet3
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-nat-3

  # ----- Route Tables -----
  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-public-rt

  PublicRoute:
    Type: AWS::EC2::Route
    DependsOn: InternetGatewayAttachment
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  PublicSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnet1
      RouteTableId: !Ref PublicRouteTable

  PublicSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnet2
      RouteTableId: !Ref PublicRouteTable

  PublicSubnet3RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnet3
      RouteTableId: !Ref PublicRouteTable

  PrivateRouteTable1:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-private-rt-1

  PrivateRoute1:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable1
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NATGateway1

  PrivateSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PrivateSubnet1
      RouteTableId: !Ref PrivateRouteTable1

  # ----- VPC Flow Logs -----
  FlowLogsRole:
    Type: AWS::IAM::Role
    Condition: CreateFlowLogs
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: vpc-flow-logs.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: FlowLogsPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                  - logs:DescribeLogGroups
                  - logs:DescribeLogStreams
                Resource: '*'

  FlowLogsGroup:
    Type: AWS::Logs::LogGroup
    Condition: CreateFlowLogs
    Properties:
      LogGroupName: !Sub /vpc/${Environment}-flow-logs
      RetentionInDays: !If [IsProduction, 365, 30]

  VPCFlowLogs:
    Type: AWS::EC2::FlowLog
    Condition: CreateFlowLogs
    Properties:
      DeliverLogsPermissionArn: !GetAtt FlowLogsRole.Arn
      LogGroupName: !Ref FlowLogsGroup
      ResourceId: !Ref VPC
      ResourceType: VPC
      TrafficType: ALL
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-flow-logs

# ============================================
# OUTPUTS - Values to export
# ============================================
Outputs:
  VPCId:
    Description: VPC ID
    Value: !Ref VPC
    Export:
      Name: !Sub ${Environment}-VPCId

  PublicSubnets:
    Description: List of public subnet IDs
    Value: !Join
      - ','
      - - !Ref PublicSubnet1
        - !Ref PublicSubnet2
        - !Ref PublicSubnet3
    Export:
      Name: !Sub ${Environment}-PublicSubnets

  PrivateSubnets:
    Description: List of private subnet IDs
    Value: !Join
      - ','
      - - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2
        - !Ref PrivateSubnet3
    Export:
      Name: !Sub ${Environment}-PrivateSubnets

  VPCCidrBlock:
    Description: VPC CIDR block
    Value: !GetAtt VPC.CidrBlock
    Export:
      Name: !Sub ${Environment}-VPCCidr
```

---

## Intrinsic Functions Deep Dive

### Essential Functions

```yaml
# Reference resources and parameters
!Ref MyResource
!Ref MyParameter

# Get resource attributes
!GetAtt MyResource.Arn
!GetAtt MyResource.DomainName

# String substitution
!Sub '${AWS::StackName}-bucket'
!Sub
  - 'arn:aws:s3:::${BucketName}/*'
  - BucketName: !Ref MyBucket

# Conditional logic
!If [IsProduction, 'r5.large', 't3.medium']

# Join strings
!Join
  - ','
  - - !Ref Subnet1
    - !Ref Subnet2
    - !Ref Subnet3

# Split strings
!Split [',', !Ref SubnetList]

# Select from list
!Select [0, !GetAZs '']

# Get Availability Zones
!GetAZs ''  # Returns AZs for current region
!GetAZs 'us-west-2'

# Find in map
!FindInMap [MapName, TopLevelKey, SecondLevelKey]

# Import from other stacks
!ImportValue ${Environment}-VPCId

# Base64 encode (for UserData)
!Base64 |
  #!/bin/bash
  yum update -y
  yum install -y httpd

# CIDR function (new!)
!Cidr [!GetAtt VPC.CidrBlock, 6, 8]
# Generates 6 /24 subnets from VPC CIDR
```

### Advanced Function Combinations

```yaml
# Nested functions
UserData:
  Fn::Base64:
    Fn::Sub: |
      #!/bin/bash
      aws s3 cp s3://${ConfigBucket}/config.yml /etc/myapp/
      systemctl start myapp

# Complex conditionals
MyResource:
  Type: AWS::EC2::Instance
  Properties:
    InstanceType: !If
      - IsProduction
      - !If [IsHighMemory, 'r5.2xlarge', 'r5.large']
      - 't3.medium'

# Conditional with multiple outputs
SecurityGroupIngress:
  - IpProtocol: tcp
    FromPort: 443
    ToPort: 443
    CidrIp: !If
      - IsProduction
      - 10.0.0.0/8
      - 0.0.0.0/0
```

---

## Nested Stacks and Cross-Stack References

### Nested Stack Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ROOT STACK                                │
│                      (main.yaml)                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │   Network   │    │  Security   │    │    App      │        │
│   │   Stack     │───▶│   Stack     │───▶│   Stack     │        │
│   │             │    │             │    │             │        │
│   │ • VPC       │    │ • IAM Roles │    │ • ECS       │        │
│   │ • Subnets   │    │ • SGs       │    │ • ALB       │        │
│   │ • NAT       │    │ • KMS       │    │ • RDS       │        │
│   └─────────────┘    └─────────────┘    └─────────────┘        │
│                                                                  │
│   Outputs flow between stacks via parameters                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Root Stack Template

```yaml
# infrastructure/main.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Root stack that orchestrates nested stacks

Parameters:
  Environment:
    Type: String
    Default: production

  TemplateBucket:
    Type: String
    Description: S3 bucket containing nested templates

Resources:
  NetworkStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: !Sub https://${TemplateBucket}.s3.amazonaws.com/network.yaml
      Parameters:
        Environment: !Ref Environment
      Tags:
        - Key: Environment
          Value: !Ref Environment

  SecurityStack:
    Type: AWS::CloudFormation::Stack
    DependsOn: NetworkStack
    Properties:
      TemplateURL: !Sub https://${TemplateBucket}.s3.amazonaws.com/security.yaml
      Parameters:
        Environment: !Ref Environment
        VPCId: !GetAtt NetworkStack.Outputs.VPCId
      Tags:
        - Key: Environment
          Value: !Ref Environment

  ApplicationStack:
    Type: AWS::CloudFormation::Stack
    DependsOn:
      - NetworkStack
      - SecurityStack
    Properties:
      TemplateURL: !Sub https://${TemplateBucket}.s3.amazonaws.com/application.yaml
      Parameters:
        Environment: !Ref Environment
        VPCId: !GetAtt NetworkStack.Outputs.VPCId
        PrivateSubnets: !GetAtt NetworkStack.Outputs.PrivateSubnets
        PublicSubnets: !GetAtt NetworkStack.Outputs.PublicSubnets
        AppSecurityGroup: !GetAtt SecurityStack.Outputs.AppSecurityGroup
        DatabaseSecurityGroup: !GetAtt SecurityStack.Outputs.DatabaseSecurityGroup
      Tags:
        - Key: Environment
          Value: !Ref Environment

Outputs:
  LoadBalancerDNS:
    Description: Application Load Balancer DNS
    Value: !GetAtt ApplicationStack.Outputs.LoadBalancerDNS

  DatabaseEndpoint:
    Description: RDS Database Endpoint
    Value: !GetAtt ApplicationStack.Outputs.DatabaseEndpoint
```

### Cross-Stack References with Exports

```yaml
# network-stack.yaml (exports values)
Outputs:
  VPCId:
    Value: !Ref VPC
    Export:
      Name: !Sub ${Environment}-VPCId

  PrivateSubnets:
    Value: !Join [',', [!Ref PrivateSubnet1, !Ref PrivateSubnet2]]
    Export:
      Name: !Sub ${Environment}-PrivateSubnets
```

```yaml
# application-stack.yaml (imports values)
Resources:
  MyService:
    Type: AWS::ECS::Service
    Properties:
      NetworkConfiguration:
        AwsvpcConfiguration:
          Subnets: !Split
            - ','
            - Fn::ImportValue: !Sub ${Environment}-PrivateSubnets
          SecurityGroups:
            - Fn::ImportValue: !Sub ${Environment}-AppSecurityGroup
```

---

## CloudFormation StackSets

### Multi-Region, Multi-Account Deployment

```yaml
# stacksets/security-baseline.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Security baseline deployed to all accounts via StackSets

Resources:
  # CloudTrail in every account
  CloudTrail:
    Type: AWS::CloudTrail::Trail
    Properties:
      TrailName: organization-trail
      S3BucketName: !Sub ${CentralLogBucket}
      IsMultiRegionTrail: true
      EnableLogFileValidation: true
      IncludeGlobalServiceEvents: true

  # Config recorder in every account
  ConfigRecorder:
    Type: AWS::Config::ConfigurationRecorder
    Properties:
      Name: default
      RoleARN: !GetAtt ConfigRole.Arn
      RecordingGroup:
        AllSupported: true
        IncludeGlobalResourceTypes: true

  # Security Hub enabled
  SecurityHub:
    Type: AWS::SecurityHub::Hub
    Properties:
      EnableDefaultStandards: true

  # GuardDuty enabled
  GuardDutyDetector:
    Type: AWS::GuardDuty::Detector
    Properties:
      Enable: true
      FindingPublishingFrequency: FIFTEEN_MINUTES
```

### StackSet Deployment via CLI

```bash
# Create StackSet
aws cloudformation create-stack-set \
  --stack-set-name security-baseline \
  --template-body file://security-baseline.yaml \
  --capabilities CAPABILITY_IAM \
  --permission-model SERVICE_MANAGED \
  --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=false

# Deploy to organization units
aws cloudformation create-stack-instances \
  --stack-set-name security-baseline \
  --deployment-targets OrganizationalUnitIds=ou-xxxx-xxxxxxxx \
  --regions us-east-1 us-west-2 eu-west-1 \
  --operation-preferences \
    FailureTolerancePercentage=10,MaxConcurrentPercentage=25

# Check deployment status
aws cloudformation describe-stack-set-operation \
  --stack-set-name security-baseline \
  --operation-id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## Change Sets and Stack Updates

### Change Set Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHANGE SET WORKFLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Create Change Set                                            │
│     ┌───────────────┐                                           │
│     │  New Template │──────┐                                    │
│     └───────────────┘      │                                    │
│                            ▼                                     │
│     ┌───────────────┐  ┌──────────────────┐                     │
│     │ Current Stack │──│ Compare & Analyze │                    │
│     └───────────────┘  └────────┬─────────┘                     │
│                                 │                                │
│  2. Review Changes              ▼                                │
│     ┌──────────────────────────────────────┐                    │
│     │          CHANGE SET                   │                    │
│     │                                       │                    │
│     │  Resource       Action   Replacement │                    │
│     │  ────────       ──────   ─────────── │                    │
│     │  MyDatabase     Modify   False       │                    │
│     │  MyInstance     Replace  True  ⚠️    │                    │
│     │  MyBucket       Add      -           │                    │
│     │  OldQueue       Remove   -           │                    │
│     └──────────────────────────────────────┘                    │
│                                                                  │
│  3. Execute or Delete                                            │
│     ┌──────────┐    ┌──────────┐                                │
│     │ Execute  │ or │  Delete  │                                │
│     │ (Apply)  │    │ (Cancel) │                                │
│     └──────────┘    └──────────┘                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Change Set Commands

```bash
# Create change set
aws cloudformation create-change-set \
  --stack-name my-stack \
  --change-set-name my-changes \
  --template-body file://template.yaml \
  --parameters ParameterKey=Environment,ParameterValue=production \
  --capabilities CAPABILITY_IAM

# Describe changes (wait for CREATE_COMPLETE)
aws cloudformation describe-change-set \
  --stack-name my-stack \
  --change-set-name my-changes

# Execute change set (apply changes)
aws cloudformation execute-change-set \
  --stack-name my-stack \
  --change-set-name my-changes

# Delete change set (cancel)
aws cloudformation delete-change-set \
  --stack-name my-stack \
  --change-set-name my-changes
```

### Understanding Replacement

```yaml
# Changes that cause REPLACEMENT (resource destroyed and recreated):
#
# EC2 Instance:
#   - ImageId change
#   - InstanceType change (if not EBS-optimized)
#   - SubnetId change
#   - AvailabilityZone change
#
# RDS Instance:
#   - DBInstanceIdentifier change
#   - Engine change
#   - MasterUsername change
#
# S3 Bucket:
#   - BucketName change (always causes replacement!)
#
# Lambda Function:
#   - FunctionName change
#   - Runtime change does NOT cause replacement
#
# Use UpdateReplacePolicy to control behavior:
Resources:
  MyDatabase:
    Type: AWS::RDS::DBInstance
    UpdateReplacePolicy: Snapshot  # Take snapshot before replacement
    DeletionPolicy: Snapshot       # Take snapshot on stack delete
    Properties:
      # ...
```

---

## Drift Detection

### Detecting Configuration Drift

```bash
# Initiate drift detection
aws cloudformation detect-stack-drift \
  --stack-name my-stack

# Check drift detection status
aws cloudformation describe-stack-drift-detection-status \
  --stack-drift-detection-id xxxxx-xxxx-xxxx

# Get drift results
aws cloudformation describe-stack-resource-drifts \
  --stack-name my-stack \
  --stack-resource-drift-status-filters MODIFIED DELETED
```

### Drift Detection Output Example

```json
{
  "StackResourceDrifts": [
    {
      "LogicalResourceId": "WebServerSecurityGroup",
      "PhysicalResourceId": "sg-0123456789abcdef0",
      "ResourceType": "AWS::EC2::SecurityGroup",
      "StackResourceDriftStatus": "MODIFIED",
      "PropertyDifferences": [
        {
          "PropertyPath": "/SecurityGroupIngress/0/CidrIp",
          "ExpectedValue": "10.0.0.0/8",
          "ActualValue": "0.0.0.0/0",
          "DifferenceType": "NOT_EQUAL"
        }
      ]
    }
  ]
}
```

### Automated Drift Remediation

```yaml
# drift-monitor.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Automated drift detection and alerting

Resources:
  DriftCheckFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: cfn-drift-checker
      Runtime: python3.11
      Handler: index.handler
      Role: !GetAtt DriftCheckRole.Arn
      Timeout: 300
      Code:
        ZipFile: |
          import boto3
          import json

          cfn = boto3.client('cloudformation')
          sns = boto3.client('sns')

          def handler(event, context):
              # Get all stacks
              stacks = cfn.list_stacks(
                  StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']
              )['StackSummaries']

              drifted_stacks = []

              for stack in stacks:
                  stack_name = stack['StackName']

                  # Initiate drift detection
                  response = cfn.detect_stack_drift(StackName=stack_name)
                  detection_id = response['StackDriftDetectionId']

                  # Wait for completion (simplified)
                  import time
                  time.sleep(30)

                  # Check results
                  result = cfn.describe_stack_drift_detection_status(
                      StackDriftDetectionId=detection_id
                  )

                  if result['StackDriftStatus'] == 'DRIFTED':
                      drifted_stacks.append({
                          'stack': stack_name,
                          'status': result['StackDriftStatus']
                      })

              if drifted_stacks:
                  sns.publish(
                      TopicArn=os.environ['SNS_TOPIC'],
                      Subject='CloudFormation Drift Detected',
                      Message=json.dumps(drifted_stacks, indent=2)
                  )

              return {'drifted_stacks': len(drifted_stacks)}

  DriftCheckSchedule:
    Type: AWS::Events::Rule
    Properties:
      ScheduleExpression: rate(1 day)
      Targets:
        - Id: DriftCheck
          Arn: !GetAtt DriftCheckFunction.Arn
```

---

## CloudFormation Custom Resources

### Lambda-Backed Custom Resource

```yaml
# Custom resource for operations CFN doesn't support natively
Resources:
  # Lambda function that handles the custom resource
  CustomResourceFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: cfn-custom-resource
      Runtime: python3.11
      Handler: index.handler
      Role: !GetAtt CustomResourceRole.Arn
      Timeout: 300
      Code:
        ZipFile: |
          import json
          import urllib3
          import boto3

          http = urllib3.PoolManager()

          def handler(event, context):
              response_data = {}
              physical_resource_id = event.get('PhysicalResourceId', 'custom-resource-id')

              try:
                  if event['RequestType'] == 'Create':
                      # Perform create operation
                      # Example: Create something CFN doesn't support
                      response_data['Result'] = 'Created successfully'
                      physical_resource_id = 'my-custom-resource-123'

                  elif event['RequestType'] == 'Update':
                      # Perform update operation
                      response_data['Result'] = 'Updated successfully'

                  elif event['RequestType'] == 'Delete':
                      # Perform cleanup
                      response_data['Result'] = 'Deleted successfully'

                  send_response(event, context, 'SUCCESS', response_data, physical_resource_id)

              except Exception as e:
                  send_response(event, context, 'FAILED', {'Error': str(e)}, physical_resource_id)

          def send_response(event, context, status, data, physical_id):
              response_body = json.dumps({
                  'Status': status,
                  'Reason': f'See CloudWatch Log Stream: {context.log_stream_name}',
                  'PhysicalResourceId': physical_id,
                  'StackId': event['StackId'],
                  'RequestId': event['RequestId'],
                  'LogicalResourceId': event['LogicalResourceId'],
                  'Data': data
              })

              http.request(
                  'PUT',
                  event['ResponseURL'],
                  body=response_body,
                  headers={'Content-Type': 'application/json'}
              )

  # The custom resource that triggers the Lambda
  MyCustomResource:
    Type: Custom::MyCustomThing
    Properties:
      ServiceToken: !GetAtt CustomResourceFunction.Arn
      Param1: value1
      Param2: value2

Outputs:
  CustomResourceResult:
    Value: !GetAtt MyCustomResource.Result
```

---

## CI/CD for CloudFormation

### GitHub Actions Pipeline

```yaml
# .github/workflows/cloudformation.yml
name: CloudFormation Deploy

on:
  push:
    branches: [main]
    paths:
      - 'infrastructure/**'
  pull_request:
    branches: [main]
    paths:
      - 'infrastructure/**'

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1

      - name: Validate templates
        run: |
          for template in infrastructure/*.yaml; do
            echo "Validating $template..."
            aws cloudformation validate-template \
              --template-body file://$template
          done

      - name: Run cfn-lint
        uses: scottbrenner/cfn-lint-action@v2
        with:
          command: cfn-lint infrastructure/*.yaml

      - name: Run cfn-nag (security)
        uses: stelligent/cfn_nag@master
        with:
          input_path: infrastructure

  plan:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1

      - name: Create change set
        id: changeset
        run: |
          STACK_NAME="my-app-stack"
          CHANGE_SET_NAME="pr-${{ github.event.pull_request.number }}-$(date +%s)"

          aws cloudformation create-change-set \
            --stack-name $STACK_NAME \
            --change-set-name $CHANGE_SET_NAME \
            --template-body file://infrastructure/main.yaml \
            --parameters file://infrastructure/params/production.json \
            --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

          # Wait for change set creation
          aws cloudformation wait change-set-create-complete \
            --stack-name $STACK_NAME \
            --change-set-name $CHANGE_SET_NAME

          # Get change set details
          aws cloudformation describe-change-set \
            --stack-name $STACK_NAME \
            --change-set-name $CHANGE_SET_NAME \
            --output json > changeset.json

          echo "changeset_name=$CHANGE_SET_NAME" >> $GITHUB_OUTPUT

      - name: Comment PR with changes
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const changeset = JSON.parse(fs.readFileSync('changeset.json', 'utf8'));

            let body = '## CloudFormation Change Set\n\n';
            body += '| Resource | Action | Replacement |\n';
            body += '|----------|--------|-------------|\n';

            for (const change of changeset.Changes || []) {
              const rc = change.ResourceChange;
              const replacement = rc.Replacement === 'True' ? '⚠️ Yes' : 'No';
              body += `| ${rc.LogicalResourceId} | ${rc.Action} | ${replacement} |\n`;
            }

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });

  deploy:
    needs: plan
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1

      - name: Deploy stack
        run: |
          aws cloudformation deploy \
            --stack-name my-app-stack \
            --template-file infrastructure/main.yaml \
            --parameter-overrides file://infrastructure/params/production.json \
            --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
            --no-fail-on-empty-changeset

      - name: Get stack outputs
        run: |
          aws cloudformation describe-stacks \
            --stack-name my-app-stack \
            --query 'Stacks[0].Outputs' \
            --output table
```

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| No DeletionPolicy | Data lost on stack delete | Set `DeletionPolicy: Retain` or `Snapshot` for stateful resources |
| Circular dependencies | Stack creation fails | Use `DependsOn` carefully; export/import for cross-stack |
| Hardcoded values | Templates not reusable | Use Parameters and Mappings |
| No change sets | Unexpected production changes | Always create change set first, review, then execute |
| Ignoring replacement | Resources destroyed unexpectedly | Check change set for "Replacement: True" warnings |
| No stack policy | Critical resources modified | Use stack policies to protect resources |
| Export name conflicts | Can't create stack in same region | Use `!Sub ${Environment}-` prefix in export names |
| Not using conditions | Duplicate templates per environment | Use Conditions for environment-specific resources |
| Missing timeouts | Stacks hang on failed resources | Set appropriate `CreationPolicy` and `UpdatePolicy` |
| No nested stacks | Templates become unmaintainable | Break large templates into nested stacks by concern |

---

## Quiz

Test your CloudFormation knowledge:

<details>
<summary>1. Where does CloudFormation store state, and why does this matter?</summary>

**Answer:** CloudFormation stores state server-side within AWS—you never manage state files. This matters because:

1. **No state corruption**: Unlike Terraform, there's no file that can become corrupted or out of sync
2. **No state locking concerns**: AWS handles concurrent access
3. **No backend configuration**: No S3 buckets or DynamoDB tables needed for state
4. **Automatic drift detection**: AWS can compare actual resources to stored state

The trade-off: You can't manipulate state directly (no `terraform state rm` equivalent), and you're locked to AWS.
</details>

<details>
<summary>2. What is a Change Set and why should you always use one?</summary>

**Answer:** A Change Set is a preview of changes CloudFormation will make before executing them. You should always use one because:

1. **See before you commit**: Review exactly what will be created, modified, or deleted
2. **Catch replacements**: See which resources will be destroyed and recreated (data loss risk)
3. **Approval workflow**: Review and approve changes before they're applied
4. **Rollback planning**: Understand the impact before committing

```bash
# Create change set (preview)
aws cloudformation create-change-set ...

# Review changes
aws cloudformation describe-change-set ...

# Apply only if changes look correct
aws cloudformation execute-change-set ...
```
</details>

<details>
<summary>3. What is the difference between Nested Stacks and Cross-Stack References?</summary>

**Answer:**

**Nested Stacks:**
- Parent stack creates and manages child stacks
- Child stacks are resources within the parent
- Lifecycle is tied together (delete parent = delete children)
- Pass values via Parameters and `!GetAtt NestedStack.Outputs.X`

**Cross-Stack References:**
- Independent stacks that export values
- Other stacks import those values
- Stacks have independent lifecycles
- Use `!ImportValue ExportName`
- Can't delete stack if another stack imports its values

**When to use which:**
- Nested: When stacks should be deployed/deleted together
- Cross-Stack: When stacks have independent lifecycles (e.g., shared VPC used by multiple app stacks)
</details>

<details>
<summary>4. What are StackSets and when would you use them?</summary>

**Answer:** StackSets deploy stacks across multiple AWS accounts and regions from a single template.

Use cases:
- **Security baseline**: Deploy GuardDuty, Config, CloudTrail to all accounts
- **Compliance**: Ensure consistent configuration across the organization
- **Multi-region deployment**: Deploy identical infrastructure to multiple regions
- **Governance**: Enforce organizational policies across all accounts

```bash
# Deploy to all accounts in an OU across 3 regions
aws cloudformation create-stack-instances \
  --stack-set-name security-baseline \
  --deployment-targets OrganizationalUnitIds=ou-xxxx-xxxxxxxx \
  --regions us-east-1 us-west-2 eu-west-1
```
</details>

<details>
<summary>5. What does "Replacement: True" in a change set mean, and why is it dangerous?</summary>

**Answer:** "Replacement: True" means CloudFormation will **delete the existing resource and create a new one**. This is dangerous because:

1. **Data loss**: For databases, the old data is gone (unless DeletionPolicy: Snapshot)
2. **Downtime**: Resource is unavailable during replacement
3. **New identifiers**: Physical IDs change (EC2 instance ID, RDS endpoint, etc.)
4. **Downstream impact**: Resources depending on the old resource may break

Example changes that cause replacement:
- Changing S3 bucket name (always)
- Changing EC2 subnet
- Changing RDS DBInstanceIdentifier
- Changing Lambda function name

**Mitigation:**
```yaml
UpdateReplacePolicy: Snapshot  # Take snapshot before replacement
DeletionPolicy: Retain         # Don't delete old resource
```
</details>

<details>
<summary>6. How does CloudFormation handle rollback on failure?</summary>

**Answer:** CloudFormation automatically rolls back to the previous stable state when stack creation or update fails:

1. **CREATE_FAILED → ROLLBACK_IN_PROGRESS → ROLLBACK_COMPLETE**
   - All resources created in this attempt are deleted
   - Stack returns to empty state

2. **UPDATE_FAILED → UPDATE_ROLLBACK_IN_PROGRESS → UPDATE_ROLLBACK_COMPLETE**
   - Resources return to their previous configuration
   - Stack returns to last successful state

You can disable rollback for debugging:
```bash
aws cloudformation create-stack \
  --disable-rollback \
  ...
```

This keeps failed resources for investigation but leaves stack in CREATE_FAILED state.
</details>

<details>
<summary>7. What is the purpose of DeletionPolicy and UpdateReplacePolicy?</summary>

**Answer:**

**DeletionPolicy**: What happens when a resource is removed from a template or the stack is deleted:
- `Delete` (default): Resource is deleted
- `Retain`: Resource is kept (orphaned from CloudFormation)
- `Snapshot`: Take a snapshot before deletion (RDS, EBS, etc.)

**UpdateReplacePolicy**: What happens during replacement (resource recreated):
- `Delete` (default): Old resource is deleted after new one is created
- `Retain`: Old resource is kept (you'll have two!)
- `Snapshot`: Snapshot old resource before deletion

```yaml
Resources:
  ProductionDatabase:
    Type: AWS::RDS::DBInstance
    DeletionPolicy: Snapshot        # Snapshot on stack delete
    UpdateReplacePolicy: Snapshot   # Snapshot if replaced during update
    Properties:
      # ...
```
</details>

<details>
<summary>8. How does CloudFormation drift detection work?</summary>

**Answer:** Drift detection compares actual resource configuration to the expected configuration stored in CloudFormation:

1. **Initiate detection**: `detect-stack-drift` API call
2. **AWS queries resources**: Gets current configuration from each resource
3. **Compares to template**: Identifies differences
4. **Reports status**:
   - `IN_SYNC`: Matches template
   - `MODIFIED`: Properties differ from template
   - `DELETED`: Resource was deleted outside CloudFormation
   - `NOT_CHECKED`: Resource type doesn't support drift detection

Limitations:
- Not real-time (you must initiate)
- Not all resource types supported
- Some properties excluded from detection
- Doesn't auto-remediate (just reports)
</details>

---

## Key Takeaways

1. **State is AWS-managed**: No state files to corrupt, backup, or lock
2. **Always use change sets**: Preview changes before applying
3. **Watch for replacements**: "Replacement: True" = resource destruction
4. **StackSets for multi-account/region**: Single template, deploy everywhere
5. **Nested stacks for organization**: Break large templates into manageable pieces
6. **DeletionPolicy protects data**: Snapshot databases before delete
7. **Native drift detection**: AWS knows when resources change outside CloudFormation
8. **Day-0 AWS feature support**: New AWS services work immediately in CloudFormation
9. **Automatic rollback**: Failed deployments return to last stable state
10. **Cross-stack references for sharing**: Export VPC IDs for other stacks to import

---

## Did You Know?

1. **CloudFormation was AWS's first IaC tool**, launched in 2011. It predates Terraform (2014) by three years. Despite this, Terraform became more popular due to multi-cloud support and HCL's readability.

2. **The 500-resource limit per stack** exists because CloudFormation makes API calls to create each resource. Too many resources = rate limiting and timeouts. The workaround: nested stacks.

3. **AWS CDK generates CloudFormation templates**. When you write CDK code in TypeScript or Python, it synthesizes to CloudFormation JSON. You're still using CloudFormation under the hood.

4. **Some AWS features only work through CloudFormation**, including AWS Service Catalog, AWS Control Tower landing zones, and certain AWS Service integrations. This is AWS's way of encouraging CloudFormation adoption.

---

## Hands-On Exercise

### Exercise: Multi-Environment Deployment with Change Sets

**Objective:** Deploy the same infrastructure to dev and prod with different configurations using parameters, conditions, and change sets.

**Tasks:**

1. Create a parameterized template:
```yaml
# infrastructure/webapp.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Web application with environment-specific configuration

Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, prod]

  InstanceType:
    Type: String
    Default: t3.micro

Conditions:
  IsProd: !Equals [!Ref Environment, prod]

Mappings:
  EnvironmentConfig:
    dev:
      DesiredCapacity: 1
      MaxCapacity: 2
    prod:
      DesiredCapacity: 2
      MaxCapacity: 10

Resources:
  # Your resources here with conditions
  # Use !If [IsProd, ...] for conditional properties
```

2. Create parameter files:
```json
// params/dev.json
[
  {"ParameterKey": "Environment", "ParameterValue": "dev"},
  {"ParameterKey": "InstanceType", "ParameterValue": "t3.micro"}
]
```

3. Deploy with change set workflow:
```bash
# Create change set
aws cloudformation create-change-set \
  --stack-name webapp-dev \
  --change-set-name initial-deploy \
  --template-body file://webapp.yaml \
  --parameters file://params/dev.json

# Review changes
aws cloudformation describe-change-set \
  --stack-name webapp-dev \
  --change-set-name initial-deploy

# Execute if changes look correct
aws cloudformation execute-change-set \
  --stack-name webapp-dev \
  --change-set-name initial-deploy
```

4. Test drift detection:
```bash
# Manually modify a resource in console
# Then run drift detection
aws cloudformation detect-stack-drift --stack-name webapp-dev
aws cloudformation describe-stack-resource-drifts --stack-name webapp-dev
```

**Success Criteria:**
- [ ] Template validates without errors
- [ ] Change set shows expected resources
- [ ] Dev environment deploys successfully
- [ ] Conditions create different resources per environment
- [ ] Drift detection identifies manual changes

---

## Next Module

Continue to [Module 7.6: Azure Bicep](module-7.6-bicep/) to learn Azure's native infrastructure as code language—a modern alternative to ARM templates.

---

## Further Reading

- [AWS CloudFormation User Guide](https://docs.aws.amazon.com/cloudformation/)
- [AWS CloudFormation Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)
- [CloudFormation Resource Reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html)
- [cfn-lint](https://github.com/aws-cloudformation/cfn-lint)
- [cfn-nag (security scanner)](https://github.com/stelligent/cfn_nag)
- [AWS CDK (CloudFormation with programming languages)](https://docs.aws.amazon.com/cdk/)
