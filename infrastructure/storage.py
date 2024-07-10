import pulumi
import pulumi_aws as aws
import json

def create_storage_and_outputs(vpc_id):
    # Create S3 bucket
    bucket = aws.s3.Bucket("lambda-function-bucket-poridhi",
        bucket="lambda-function-bucket-poridhi-1213",
        acl="private",
        tags={"Name": "Lambda Function Bucket"}
    )

    def upload_exports_to_s3(outputs):
        # Convert outputs to JSON
        outputs_json = json.dumps(outputs, indent=2)
        
        # Create an S3 object with the JSON content
        aws.s3.BucketObject("pulumi-exports",
            bucket=bucket.id,
            key="pulumi-exports.json",
            content=outputs_json,
            content_type="application/json"
        )

    return bucket, upload_exports_to_s3