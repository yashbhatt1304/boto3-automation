import boto3

bucketName="yashbucket101"
def creates3storage():
    s3=boto3.client('s3')
    response = s3.create_bucket(
        Bucket=bucketName,
        CreateBucketConfiguration={'LocationConstraint': 'ap-northeast-2',},
    )
    return response["Location"]

s3BucketUrl=creates3storage()


