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



###########  Uploading static file of our Application in S3 bucket #########
def putDataInS3():
    s3=boto3.client('s3')
    s3.upload_file('./index.html', bucketName, 'index.html')
putDataInS3()



######### Launching EC2 instance #########
############ note:- wait for few minutes to run the script and restart nginx ###########

amiId="ami-062cf18d655c0b1e8"
keyPair="Yash_HV"
script='''#!/bin/bash
sudo apt update
sudo apt install -y nginx
git clone https://github.com/yashbhatt1304/boto3-automation.git
sudo cp -f ./boto3-automation/index.html /var/www/html
sudo systemctl restart nginx
'''

def lauchEC2Instance():
    ec2=boto3.client('ec2')
    response = ec2.run_instances(
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/sdh',
                'Ebs': {
                'VolumeSize': 4,
                'VolumeType': "gp3"
                },
            },
        ],
        ImageId=amiId,
        InstanceType='t2.micro',
        KeyName=keyPair,
        MaxCount=1,
        MinCount=1,
        SecurityGroupIds=[
            'sg-04b6dc832e6caa00c',
        ],
        UserData=script
    )   
    return response

instanceId = lauchEC2Instance()['Instances'][0]['InstanceId']
print(instanceId)
