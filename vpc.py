from troposphere import Base64, FindInMap, GetAtt
from troposphere import Parameter, Output, Ref, Template
import troposphere.ec2 as ec2
from troposphere.ec2 import Tag

def tag_resource(resource):
    resource.Tags = [
    project_tag
    ]

# The template
t = Template()
t.description = "Neptune test template"
t.add_version()

project_tag = Tag(Key="Project", Value="Neptune")

# NeptuneVpc
vpc = ec2.VPC("NeptuneVpc")
vpc.CidrBlock = "10.0.0.0/16"
tag_resource(vpc)
t.add_resource(vpc)    

# InternetGateway
igw = ec2.InternetGateway("InternetGateway")
tag_resource(igw)
t.add_resource(igw)

# InternetGatewayAttachment
igwa = ec2.VPCGatewayAttachment("InternetGatewayAttachment")
igwa.VpcId = vpc.ref()
igwa.InternetGatewayId = igw.ref()
t.add_resource(igwa)

# PrivateSubnet
private_subnet = ec2.Subnet("PrivateSubnet")
private_subnet.CidrBlock = "10.0.1.0/24"
private_subnet.MapPublicIpOnLaunch = False
private_subnet.VpcId = vpc.ref()
tag_resource(private_subnet)
t.add_resource(private_subnet)

# PublicSubnet
public_subnet = ec2.Subnet("PublicSubnet")
public_subnet.CidrBlock = "10.0.11.0/24"
public_subnet.MapPublicIpOnLaunch = True
public_subnet.VpcId = vpc.ref()
tag_resource(public_subnet)
t.add_resource(public_subnet)

# PublicRouteTable
rt = ec2.RouteTable("PublicRouteTable")
rt.VpcId = vpc.ref()
tag_resource(rt)
t.add_resource(rt)

# Associate route table to public subnet.
psrta = ec2.SubnetRouteTableAssociation("PublicSubnetRouteTableAssociation")
psrta.RouteTableId = rt.ref()
psrta.SubnetId = public_subnet.ref()
t.add_resource(psrta)

# DefaultToIgwRoute
route = ec2.Route("DefaultToIgwRoute")
route.RouteTableId = rt.ref()
route.DestinationCidrBlock = "0.0.0.0/0"
route.GatewayId = igwa.ref()
t.add_resource(route)

#   SSHSecurityGroup:
sshsg = ec2.SecurityGroup("SSHSecurityGroup")
sshsg.GroupDescription = "SSH trafic from anywhere"
sshsg.SecurityGroupIngress = [
    ec2.SecurityGroupIngress(
        "SSHProtocol", 
        CidrIp = "0.0.0.0/0", 
        IpProtocol = "tcp",
        FromPort = "22",
        ToPort = "22",)
    ]
sshsg.VpcId = vpc.ref()
tag_resource(sshsg)
t.add_resource(sshsg)

#   HTTPSecurityGroup:
httpsg = ec2.SecurityGroup("HttpSecurityGroup")
httpsg.GroupDescription = "SSH trafic from anywhere"
httpsg.SecurityGroupIngress = [
    ec2.SecurityGroupIngress(
        "HTTPProtocol", 
        CidrIp = "0.0.0.0/0", 
        IpProtocol = "tcp",
        FromPort = "80",
        ToPort = "80",)
    ]
httpsg.VpcId = vpc.ref()
tag_resource(httpsg)
t.add_resource(httpsg)

# BastionHost
instance = ec2.Instance("myinstance")
instance.ImageId = "ami-951945d0"
instance.InstanceType = "t1.micro"
instance.SubnetId = public_subnet.ref()
instance.SecurityGroupIds = [
    sshsg.ref(),
]
instance.KeyName = "pezaPublicKey"
instance.UserData = Base64("""#!/bin/bash -ex
usermod -G docker ec2-user
yum update -y
yum upgrade -y
yum install httpd php docker -y
systemctl enable httpd
echo 'CBS OCIO Demo!!!' > /var/www/html/index.html
systemctl start httpd
systemctl enable docker
systemclt start docker
""")
tag_resource(instance)
t.add_resource(instance)

print(t.to_yaml())    