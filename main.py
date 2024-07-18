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
securityGroup="sg-04b6dc832e6caa00c"
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
            securityGroup,
        ],
        UserData=script
    )   
    return response

EC2details = lauchEC2Instance()
instanceId = EC2details['Instances'][0]['InstanceId']
VpcId = EC2details['Instances'][0]['VpcId']
SubnetId = EC2details['Instances'][0]['SubnetId']
# print(EC2details)
print(instanceId)
print(VpcId)



############ Creating Target Group ###########
def createTargetGroup():
    lb=boto3.client('elbv2')
    response = lb.create_target_group(
        Name='Yash-tg',
        Protocol='HTTP',
        Port=80,
        VpcId=VpcId,
        HealthCheckProtocol='HTTP',
        HealthCheckPort='80',
        HealthCheckEnabled=True,
        HealthCheckPath='/',
        Matcher={
            'HttpCode': '200'
        },
        TargetType='instance',
    )
    return response
tg_arn = createTargetGroup()['TargetGroups'][0]['TargetGroupArn']
print(tg_arn)



############ Getting available subnets for VPC ############
def getSubnet():
    ec2=boto3.client('ec2')
    response = ec2.describe_subnets(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': ['vpc-0f22c13329dc40837']
            }
        ]
    )
    return response
subnets=[i['SubnetId'] for i in getSubnet()['Subnets']]
print(subnets)



############ Creating Application Load Balancer ############
def createLB():
    lb=boto3.client('elbv2')
    response = lb.create_load_balancer(
        Name='yash-LB',
        SecurityGroups=[securityGroup],
        Scheme='internet-facing',
        Subnets=subnets,
        Type='application'
    )

    return response
LB_arn = createLB()['LoadBalancers'][0]['LoadBalancerArn']
print(LB_arn)



########### Registering Target Group and Adding Listner ###########
def registerTGandListner():
    lb=boto3.client('elbv2')
    lb.register_targets(
        TargetGroupArn=tg_arn,
        Targets=[{'Id': instanceId}]
    )
    response = lb.create_listener(
        LoadBalancerArn=LB_arn,
        Protocol='HTTP',
        Port=80,
        DefaultActions=[
            {
                'Type': 'forward',
                'TargetGroupArn': tg_arn
            }
        ]
    )

listner =registerTGandListner()['Listeners'][0]['ListenerArn']
print(listner)