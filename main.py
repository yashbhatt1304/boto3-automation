import boto3
import time

bucketName="yashbucket101"

########## creating S3 storage for storing static files ##########
def creates3storage():
    s3=boto3.client('s3')
    response = s3.create_bucket(
        Bucket=bucketName,
        CreateBucketConfiguration={'LocationConstraint': 'ap-northeast-2',},
    )
    return response["Location"]
#s3BucketUrl=creates3storage()



###########  Uploading static file of our Application in S3 bucket #########
def putDataInS3():
    s3=boto3.client('s3')
    s3.upload_file('./index.html', bucketName, 'index.html')
#putDataInS3()



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
        # IamInstanceProfile={
        #     'Arn': 'arn:aws:iam::975050024946:policy/Yash-EC2-fullAccess'
        # },
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
    time.sleep(5) 
    return response

# EC2details = lauchEC2Instance()
# instanceId = EC2details['Instances'][0]['InstanceId']
# VpcId = EC2details['Instances'][0]['VpcId']
# SubnetId = EC2details['Instances'][0]['SubnetId']
# # print(EC2details)
# print("Instance Id: "+instanceId)
# print("VPC Id: "+VpcId)



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
# tg_arn = createTargetGroup()['TargetGroups'][0]['TargetGroupArn']
# print("Target ARN: "+tg_arn)



############ Getting available subnets for VPC ############
def getSubnet():
    ec2=boto3.client('ec2')
    response = ec2.describe_subnets(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': ['vpc-0f22c13329dc40837']
                # 'Values': [VpcId]
            }
        ]
    )
    return response
subnets=[i['SubnetId'] for i in getSubnet()['Subnets']]
print("Subnets: "+str(subnets))



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
# LB_arn = createLB()['LoadBalancers'][0]['LoadBalancerArn']
# print("Load Balancer ARN: "+LB_arn)


tg_arn='arn:aws:elasticloadbalancing:ap-northeast-2:975050024946:targetgroup/Yash-tg/312c117469895dde'
instanceId='i-03466e82e7e7051ea'
LB_arn='arn:aws:elasticloadbalancing:ap-northeast-2:975050024946:loadbalancer/app/yash-LB/8ca993cbcf7f3bb8'

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
    return response

# listner =registerTGandListner()['Listeners'][0]['ListenerArn']
# print("Adding Listner to Target Group: "+listner)



########## Getting details of EC2 running Instance ##########
def getAMI():
    ec2=boto3.client('ec2')
    response = ec2.describe_instances(
        InstanceIds=[
            'i-04e63a58248406f03',
        ],
    )
    return response
res = getAMI()
# print("Describing Instance:\n"+str(res))
amiId = res['Reservations'][0]['Instances'][0]['ImageId']
vpcIdentifier = res['Reservations'][0]['Instances'][0]['VpcId']
print("AMI Id: "+amiId)
print("VPC Identifier: "+vpcIdentifier)



########### Creating configuration template for ASG ###########
ASG_template = 'yash-launch-config'
def createLaunchConfigASG():
    asg = boto3.client('autoscaling')
    response = asg.create_launch_configuration(
        ImageId=amiId,
        KeyName='Yash_HV',
        SecurityGroups=['sg-04b6dc832e6caa00c',],
        InstanceType='t2.micro',
        LaunchConfigurationName=ASG_template,
    )
    print("Launch Configuration:\n"+str(response))
# createLaunchConfigASG()



########### Creating ASG ###########
ASG_name = 'yash-auto-scaling-group'
def createAsg():
    asg = boto3.client('autoscaling')
    response = asg.create_auto_scaling_group(
        AutoScalingGroupName=ASG_name,
        DefaultInstanceWarmup=120,
        LaunchConfigurationName='yash-launch-config',
        MaxSize=4,
        MinSize=1,
        VPCZoneIdentifier=','.join(i for i in subnets),
    )
    print("Creating ASG:\n"+str(response))
createAsg()



######## Scale Out Policy #########
def createScalingOutPolicy():
    asg = boto3.client('autoscaling')
    resScaleOut = asg.put_scaling_policy(
        AutoScalingGroupName=ASG_name,
        PolicyName='ScaleOutPolicy',
        PolicyType='SimpleScaling',
        AdjustmentType='ChangeInCapacity',
        ScalingAdjustment=1,  # Increase the number of instances by 1
        Cooldown=300
    )
    return resScaleOut
ScaleOutARN=createScalingOutPolicy()['PolicyARN']
print("Scale Out Policy ARN: "+ScaleOutARN)



######## Scale In Policy #########
def createScalingInPolicy():
    asg = boto3.client('autoscaling')
    resScaleIn = asg.put_scaling_policy(
        AutoScalingGroupName=ASG_name,
        PolicyName='ScaleInPolicy',
        PolicyType='SimpleScaling',
        AdjustmentType='ChangeInCapacity',
        ScalingAdjustment=-1,  # Decrease the number of instances by 1
        Cooldown=300  
    )
    return resScaleIn
ScaleInARN=createScalingInPolicy()['PolicyARN']
print("Scale In Policy ARN: "+ScaleInARN)



########## Linking Cloudwatch with Scale Out policy ##########
def linkCloudwatchForScaleOut():
    cw = boto3.client('cloudwatch')
    resCloudwatch = cw.put_metric_alarm(
        AlarmName='AlarmScaleOut',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName='CPUUtilization',
        Namespace='AWS/EC2',
        Period=60,
        Statistic='Average',
        Threshold=75.0,
        ActionsEnabled=True,
        AlarmActions=[ScaleOutARN],
        Dimensions=[
            {
                'Name': 'AutoScalingGroupName',
                'Value': ASG_name
            },
        ],
        Unit='Percent'
    )
    return resCloudwatch
res = linkCloudwatchForScaleOut()
print("Linking Scale Out policy with Cloudwatch!\n")



########## Link Cloudwatch with Scale In Policy ##########
def linkCloudwatchForScaleIn():
    cw = boto3.client('cloudwatch')
    resCloudwatch = cw.put_metric_alarm(
        AlarmName='AlarmScaleIn',
        ComparisonOperator='LessThanThreshold',
        EvaluationPeriods=2,
        MetricName='CPUUtilization',
        Namespace='AWS/EC2',
        Period=60,
        Statistic='Average',
        Threshold=20.0,
        ActionsEnabled=True,
        AlarmActions=[ScaleInARN],
        Dimensions=[
            {
                'Name': 'AutoScalingGroupName',
                'Value': ASG_name
            },
        ],
        Unit='Percent'
    )
    return resCloudwatch
res = linkCloudwatchForScaleIn()
print("Linking Scale In policy with Cloudwatch!\n")