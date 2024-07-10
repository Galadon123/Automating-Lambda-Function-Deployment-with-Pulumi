# security.py

import pulumi
import pulumi_aws as aws

def create_security_groups(vpc_id):
    # Create Security Group for Lambda function
    lambda_security_group = aws.ec2.SecurityGroup(
        "lambda-security-group",
        vpc_id=vpc_id,
        description="Allow all traffic",
        ingress=[{
            "protocol": "-1",  # All protocols
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }],
        egress=[{
            "protocol": "-1",  # All protocols
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }],
        tags={"Name": "lambda-security-group"}
    )

    return {
        "lambda_security_group": lambda_security_group
    }