import pulumi
import pulumi_aws as aws
import pulumi_docker as docker
import base64
from pulumi_docker import Image, DockerBuild, ImageRegistry

def create_lambda_function(vpc_id, private_subnet_id, lambda_security_group_id):
    # Create IAM Role for Lambda
    lambda_role = aws.iam.Role("lambda-role",
                               assume_role_policy="""{
                                   "Version": "2012-10-17",
                                   "Statement": [
                                       {
                                           "Action": "sts:AssumeRole",
                                           "Principal": {
                                               "Service": "lambda.amazonaws.com"
                                           },
                                           "Effect": "Allow",
                                           "Sid": ""
                                       }
                                   ]
                               }""")

    # Attach IAM Policy to Lambda Role
    lambda_policy_attachment = aws.iam.RolePolicyAttachment("lambda-policy-attachment",
        role=lambda_role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
    )

    # Create IAM Policy for Lambda Role to access S3
    lambda_policy = aws.iam.Policy("lambda-policy",
        policy="""{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        "arn:aws:s3:::lambda-function-bucket-poridhi",
                        "arn:aws:s3:::lambda-function-bucket-poridhi/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "ec2:CreateNetworkInterface",
                        "ec2:DeleteNetworkInterface",
                        "ec2:DescribeNetworkInterfaces"
                    ],
                    "Resource": "*"
                }
            ]
        }"""
    )

    # Attach IAM Policy to Lambda Role
    lambda_policy_attachment_2 = aws.iam.RolePolicyAttachment("lambda-policy-attachment_2",
        role=lambda_role.name,
        policy_arn=lambda_policy.arn
    )

    # Create ECR Repository
    repo = aws.ecr.Repository('my-app-repo',
        image_tag_mutability="MUTABLE",
        image_scanning_configuration={
            "scanOnPush": True
        }
    )

    # Get repository credentials
    creds = repo.registry_id.apply(
        lambda registry_id: aws.ecr.get_credentials(registry_id=registry_id)
    )

    decoded_creds = creds.authorization_token.apply(
        lambda token: base64.b64decode(token).decode('utf-8').split(':')
    )

    registry_server = creds.proxy_endpoint

    # Define the ECR image name
    ecr_image_name = repo.repository_url.apply(lambda url: f"{url}:latest")

    # Push the Docker image to the ECR repository
    image = docker.Image('nginx-ecr-image',
        image_name=ecr_image_name,
        build=docker.DockerBuild(
            context=".",
            dockerfile="Dockerfile",
        ),
        registry=ImageRegistry(
          server=registry_server,
          username=decoded_creds.apply(lambda creds: creds[0]),
          password=decoded_creds.apply(lambda creds: creds[1]),
    )
    )

    # Create Lambda function
    lambda_function = aws.lambda_.Function("my-lambda-function",
        role=lambda_role.arn,
        image_uri=image.image_name,
        package_type="Image",
        timeout=400,
        memory_size=1024,
        vpc_config={
            "subnet_ids": [private_subnet_id],
            "security_group_ids": [lambda_security_group_id],
        },
        environment={
            "variables": {
                "ENV_VAR_1": "value1",
                "ENV_VAR_2": "value2",
            }
        }
    )

    # Create a CloudWatch Log Group for the Lambda function
    log_group = aws.cloudwatch.LogGroup("lambda-log-group",
        name=lambda_function.name.apply(lambda name: f"/aws/lambda/{name}"),
        retention_in_days=14
    )

    return {
        "lambda_role": lambda_role,
        "lambda_function": lambda_function,
        "ecr_repo": repo
    }