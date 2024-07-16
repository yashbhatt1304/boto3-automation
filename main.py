import boto3

bucketName="yashbucket101"

########## creating S3 storage for storing static files ##########
def creates3storage():
    s3=boto3.client('s3')
    response = s3.create_bucket(
        Bucket=bucketName,
        CreateBucketConfiguration={'LocationConstraint': 'ap-northeast-2',},
    )
    return response["Location"]
s3BucketUrl=creates3storage()


###########  Uploading static file f=of our Application in S3 bucket #########
def putDataInS3():
    s3=boto3.client('s3')
    s3.upload_file('./index.html', bucketName, 'index.html')

putDataInS3()
