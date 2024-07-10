# network.py

import pulumi
import pulumi_aws as aws

def create_network_infrastructure():
    # Create VPC
    vpc = aws.ec2.Vpc("my-vpc",
                      cidr_block="10.0.0.0/16",
                      tags={"Name": "my-vpc"})

    # Create Internet Gateway
    igw = aws.ec2.InternetGateway("my-vpc-igw",
                                  vpc_id=vpc.id,
                                  opts=pulumi.ResourceOptions(depends_on=[vpc]),
                                  tags={"Name": "my-vpc-igw"})

    # Create Route Table for Public
    public_route_table = aws.ec2.RouteTable("my-vpc-public-rt",
                                            vpc_id=vpc.id,
                                            routes=[{
                                                "cidr_block": "0.0.0.0/0",
                                                "gateway_id": igw.id,
                                            }],
                                            opts=pulumi.ResourceOptions(depends_on=[igw]),
                                            tags={"Name": "my-vpc-public-rt"})

    # Create Public Subnet
    public_subnet = aws.ec2.Subnet("public-subnet",
                                   vpc_id=vpc.id,
                                   cidr_block="10.0.1.0/24",
                                   availability_zone="us-east-1a",
                                   map_public_ip_on_launch=True,
                                   opts=pulumi.ResourceOptions(depends_on=[vpc]),
                                   tags={"Name": "public-subnet"})

    # Associate Route Table with Public Subnet
    public_route_table_association = aws.ec2.RouteTableAssociation("public-subnet-association",
                                                                   subnet_id=public_subnet.id,
                                                                   route_table_id=public_route_table.id,
                                                                   opts=pulumi.ResourceOptions(depends_on=[public_subnet, public_route_table]))

    # Create Private Subnet
    private_subnet = aws.ec2.Subnet("private-subnet",
                                    vpc_id=vpc.id,
                                    cidr_block="10.0.2.0/24",
                                    availability_zone="us-east-1b",
                                    map_public_ip_on_launch=False,
                                    opts=pulumi.ResourceOptions(depends_on=[vpc]),
                                    tags={"Name": "private-subnet"})

    # Create NAT Gateway
    eip = aws.ec2.Eip("my-eip")
    nat_gateway = aws.ec2.NatGateway("my-nat-gateway",
                                     subnet_id=public_subnet.id,
                                     allocation_id=eip.id,
                                     opts=pulumi.ResourceOptions(depends_on=[public_subnet, eip]),
                                     tags={"Name": "my-nat-gateway"})

    # Create Route Table for Private Subnet
    private_route_table = aws.ec2.RouteTable("my-vpc-private-rt",
                                             vpc_id=vpc.id,
                                             routes=[{
                                                 "cidr_block": "0.0.0.0/0",
                                                 "gateway_id": nat_gateway.id,
                                             }],
                                             opts=pulumi.ResourceOptions(depends_on=[nat_gateway]),
                                             tags={"Name": "my-vpc-private-rt"})

    # Associate Route Table with Private Subnet
    private_route_table_association = aws.ec2.RouteTableAssociation("private-subnet-association",
                                                                    subnet_id=private_subnet.id,
                                                                    route_table_id=private_route_table.id,
                                                                    opts=pulumi.ResourceOptions(depends_on=[private_subnet, private_route_table]))

    return {
        "vpc": vpc,
        "public_subnet": public_subnet,
        "private_subnet": private_subnet,
        "public_route_table": public_route_table,
        "private_route_table": private_route_table
    }