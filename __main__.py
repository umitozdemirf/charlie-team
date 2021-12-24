"""An AWS Python Pulumi program"""
import pulumi
import pulumi_aws as aws

db_pass = "root"

charlie_vpc = aws.ec2.Vpc("charlie-vpc",
                          cidr_block="10.1.0.0/16",
                          tags={
                              "Name": "Charlie-VPC"
                          }
                          )

subnet1a = aws.ec2.Subnet("subnet-1a",
                          vpc_id=charlie_vpc.id,
                          cidr_block="10.1.1.0/24",
                          tags={
                              "Name": "Charlie-Subnet"
                          },
                          availability_zone="us-west-2a"
                          )

subnet1b = aws.ec2.Subnet("subnet-1b",
                          vpc_id=charlie_vpc.id,
                          cidr_block="10.1.2.0/24",
                          tags={
                              "Name": "Charlie-Subnet2"
                          },
                          availability_zone="us-west-2b"
                          )

subnet1c = aws.ec2.Subnet("subnet-1c",
                          vpc_id=charlie_vpc.id,
                          cidr_block="10.1.3.0/24",
                          tags={
                              "Name": "Charlie-Subnet3"
                          },
                          availability_zone="us-west-2c"
                          )

subnet_group = aws.rds.SubnetGroup("subnet-group",
                                   subnet_ids=[subnet1a.id,
                                               subnet1b.id],
                                   tags={"Name": "db-subnet-group"})

db_neptune = aws.neptune.Cluster("db-neptune",
                                 apply_immediately=True,
                                 backup_retention_period=5,
                                 cluster_identifier="charlie-neptune",
                                 engine="neptune",
                                 iam_database_authentication_enabled=True,
                                 preferred_backup_window="07:00-09:00",
                                 skip_final_snapshot=True,
                                 neptune_subnet_group_name=subnet_group.name)

db_mysql = aws.rds.Cluster("db-mysql",
                           availability_zones=[
                               "us-west-2a",
                               "us-west-2b",
                           ],
                           backup_retention_period=5,
                           cluster_identifier="aurora-cluster-demo",
                           database_name="charlie-mysql",
                           engine="aurora-mysql",
                           engine_version="5.7.mysql_aurora.2.03.2",
                           master_password="charlie1",
                           master_username="charlie",
                           preferred_backup_window="07:00-09:00",
                           db_subnet_group_name=subnet_group.name)

role = aws.iam.Role("charlie-iam-role",
                    assume_role_policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
""")

eks_policy = aws.iam.RolePolicyAttachment("Charlie-AmazonEKSClusterPolicy",
                                          policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
                                          role=role.name)
eks_policy_controller = aws.iam.RolePolicyAttachment("Charlie-AmazonEKSVPCResourceController",
                                                     policy_arn="arn:aws:iam::aws:policy/AmazonEKSVPCResourceController",
                                                     role=role.name)

charlie_eks = aws.eks.Cluster("charlie-eks",
                              role_arn=role.arn,
                              vpc_config=aws.eks.ClusterVpcConfigArgs(
                                  subnet_ids=[
                                      subnet1a.id,
                                      subnet1b.id,
                                      subnet1c.id
                                  ],
                              ),
                              opts=pulumi.ResourceOptions(depends_on=[
                                  eks_policy,
                                  eks_policy_controller,
                              ]))
