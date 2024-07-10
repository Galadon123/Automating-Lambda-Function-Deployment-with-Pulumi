import pulumi
import pulumi_aws as aws
import json
import base64
import pulumi_docker as docker
from pulumi_docker import Image, DockerBuild, ImageRegistry
import subprocess
import time


class LambdaUpdater(pulumi.dynamic.ResourceProvider):
    def create(self, props):
        cmd = f"aws lambda update-function-code --function-name {props['function_name']} --image-uri {props['image_uri']} --region {props['region']}"
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        
        # Generate a unique ID for this update
        new_id = f"{props['function_name']}_{props['timestamp']}"
        
        return pulumi.dynamic.CreateResult(id_=new_id, outs=props)

    def update(self, id, props, olds):
        cmd = f"aws lambda update-function-code --function-name {props['function_name']} --image-uri {props['image_uri']} --region {props['region']}"
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        
        # Use the existing ID
        props['id'] = id
        
        return pulumi.dynamic.UpdateResult(outs=props)

class LambdaUpdate(pulumi.dynamic.Resource):
    def __init__(self, name, props, opts = None):
        super().__init__(LambdaUpdater(), name, props, opts)
        self.function_name = props['function_name']
        self.image_uri = props['image_uri']
        self.region = props['region']
        self.timestamp = props['timestamp']

def get_exports_from_s3(bucket_name, object_key):
    # Use the get_object function to retrieve the S3 object
    s3_object = aws.s3.get_object(bucket=bucket_name, key=object_key)
    
    # Check if s3_object.body is a string or an Output
    if isinstance(s3_object.body, str):
        # If it's a string, parse it and wrap it in a Pulumi Outputs
        return pulumi.Output.from_input(json.loads(s3_object.body))
    else:
        # If it's an Output, apply json.loads to it
        return s3_object.body.apply(lambda body: json.loads(body))

# Usage
exports = get_exports_from_s3('lambda-function-bucket-poridhi-1234', 'pulumi-exports.json')

# Get ECR repository details from exports
repository_url = exports.apply(lambda exp: exp['repository_url'])
ecr_registry_id = exports.apply(lambda exp: exp['ecr_registry_id'])

# Get repository credentials
creds = aws.ecr.get_credentials_output(registry_id=ecr_registry_id)

decoded_creds = creds.authorization_token.apply(
    lambda token: base64.b64decode(token).decode('utf-8').split(':')
)

registry_server = creds.proxy_endpoint

# Define the ECR image name
ecr_image_name = repository_url.apply(lambda url: f"{url}:latest")

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


lambda_function_name = exports.apply(lambda exp: exp['lambda_function_name'])
lambda_role_arn = exports.apply(lambda exp: exp['lambda_role_arn'])
lambda_function_arn = exports.apply(lambda exp: exp['lambda_function_arn'])

# Update the Lambda function using AWS CLI
update_lambda = LambdaUpdate('update-lambda-function',
    {
        'function_name': lambda_function_name,
        'image_uri': image.image_name,
        'region': aws.config.region,
        'timestamp': str(time.time())  # Add this line
    },
    opts=pulumi.ResourceOptions(depends_on=[image])
)

api = aws.apigateway.RestApi("myApi",
    description="API Gateway for Lambda function",
)
default_resource = aws.apigateway.Resource("defaultResource",
    parent_id=api.root_resource_id,
    path_part="default",
    rest_api=api.id,
)
# Create a resource
lambda_resource = aws.apigateway.Resource("lambdaResource",
    parent_id=default_resource.id,
    path_part="my-lambda-function",
    rest_api=api.id,
)
test1_resource = aws.apigateway.Resource("test1Resource",
    parent_id=lambda_resource.id,
    path_part="test1",
    rest_api=api.id,
)
test2_resource = aws.apigateway.Resource("test2Resource",
    parent_id=lambda_resource.id,
    path_part="test2",
    rest_api=api.id,
)
test1_method = aws.apigateway.Method("test1_Method",
    http_method="GET",
    authorization="NONE",
    resource_id=test1_resource.id,
    rest_api=api.id,
)

test2_method = aws.apigateway.Method("test2_Method",
    http_method="GET",
    authorization="NONE",
    resource_id=test2_resource.id,
    rest_api=api.id,
)

# Create a method for the GET request
method = aws.apigateway.Method("myMethod",
    http_method="GET",
    authorization="NONE",
    resource_id=lambda_resource.id,
    rest_api=api.id,
)

integration = aws.apigateway.Integration("myIntegration",
    http_method=method.http_method,
    integration_http_method="POST",
    type="AWS_PROXY",
    uri=lambda_function_arn.apply(lambda arn: f"arn:aws:apigateway:{aws.config.region}:lambda:path/2015-03-31/functions/{arn}/invocations"),
    resource_id=lambda_resource.id,
    rest_api=api.id,
)
test1_integration = aws.apigateway.Integration("test1Integration",
    http_method=test1_method.http_method,
    integration_http_method="POST",
    type="AWS_PROXY",
    uri=lambda_function_arn.apply(lambda arn: f"arn:aws:apigateway:{aws.config.region}:lambda:path/2015-03-31/functions/{arn}/invocations"),
    resource_id=test1_resource.id,
    rest_api=api.id,
)
test2_integration = aws.apigateway.Integration("test2Integration",
    http_method=test2_method.http_method,
    integration_http_method="POST",
    type="AWS_PROXY",
    uri=lambda_function_arn.apply(lambda arn: f"arn:aws:apigateway:{aws.config.region}:lambda:path/2015-03-31/functions/{arn}/invocations"),
    resource_id=test2_resource.id,
    rest_api=api.id,
)

# Grant API Gateway permission to invoke the Lambda function
permission = aws.lambda_.Permission("lambda_Permission",
    action="lambda:InvokeFunction",
    function=lambda_function_arn,
    principal="apigateway.amazonaws.com",
    source_arn=api.execution_arn.apply(lambda arn: f"{arn}/*/*"),
)

# Deploy the API
deployment = aws.apigateway.Deployment("myDeployment",
    rest_api=api.id,
    # Ensure deployment triggers on changes to the integration
    triggers={
        "integration": integration.id,
        "test1_integration": test1_integration.id,
        "test2_integration": test2_integration.id,

    },
    opts=pulumi.ResourceOptions(depends_on=[integration]),
)

# Create a stage
stage = aws.apigateway.Stage("myStage",
    deployment=deployment.id,
    rest_api=api.id,
    stage_name="prod",
)
# Export the image details
pulumi.export('image_url', image.image_name)



