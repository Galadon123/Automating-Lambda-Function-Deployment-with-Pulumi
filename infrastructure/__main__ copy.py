# __main__.py

import pulumi
from network import create_network_infrastructure
from security import create_security_groups
from lambda_function import create_lambda_function
from storage import create_storage_and_outputs

# Create network infrastru
network = create_network_infrastructure()

# Create security groups
security_groups = create_security_groups(network["vpc"].id)

# Create Lambda function and related 
lambda_resources = create_lambda_function(
    network["vpc"].id,
    network["private_subnet"].id,
    security_groups["lambda_security_group"].id
)

# Create S3 bucket and prepare for output storage
bucket, upload_exports_to_s3 = create_storage_and_outputs(network["vpc"].id)

# Collect all outputsfas
all_outputs = {
    "vpc_id": network["vpc"].id,
    "public_subnet_id": network["public_subnet"].id,
    "private_subnet_id": network["private_subnet"].id,
    "public_route_table_id": network["public_route_table"].id,
    "private_route_table_id": network["private_route_table"].id,
    "lambda_security_group_id": security_groups["lambda_security_group"].id,
    "lambda_role_arn": lambda_resources["lambda_role"].arn,
    "repository_url": lambda_resources["ecr_repo"].repository_url,
    "ecr_registry_id": lambda_resources["ecr_repo"].registry_id,
    "lambda_function_name": lambda_resources["lambda_function"].name,
    "lambda_function_arn": lambda_resources["lambda_function"].arn,
    "bucket_name": bucket.id,
}

# Upload outputs to S3
pulumi.Output.all(**all_outputs).apply(lambda resolved: upload_exports_to_s3(resolved))

# Export some values for easy access
pulumi.export('vpc_id', network["vpc"].id)
pulumi.export('lambda_function_name', lambda_resources["lambda_function"].name)
pulumi.export('bucket_name', bucket.id)