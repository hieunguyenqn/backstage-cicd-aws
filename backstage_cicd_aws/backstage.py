# from dotenv import dotenv_values
from aws_cdk import (
    Stack
)
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_rds as rds
from constructs import Construct


# from collections import OrderedDict


class BackstageStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, props: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # CommonResourceStack
        # Create a VPC
        db_port = int(props.get("POSTGRES_PORT", 5432))
        container_name = props.get("CONTAINER_NAME", 'backstage')
        ecr_repo_name = props.get("ECR_REPO_NAME", "aws-cdk/assets")

        self.vpc = ec2.Vpc(
            self,
            "ECS-VPC",
            max_azs=2,
        )
        # Define SGs so Fargate and no-one else can talk to aurora securly
        self.fargate_sg = ec2.SecurityGroup(
            self, "fargate-sec-group",
            security_group_name="FargateSecGroup",
            description="Security group for Fargate Task",
            vpc=self.vpc
        )

        self.aurora_sg = ec2.SecurityGroup(
            self, "aurora-sec-group",
            security_group_name="AuroraSecGroup",
            description='Security group for Aurora Db',
            vpc=self.vpc
        )
        # default egress rules are for any, so we just need an ingress rule
        # to allow fargate to reach the aurora cluster and protect its access from elsewhere
        self.aurora_sg.add_ingress_rule(peer=self.fargate_sg, connection=ec2.Port.tcp(db_port))

        self.aurora_instance = rds.InstanceProps(
                instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.SMALL),
                vpc=self.vpc,
                security_groups=[self.aurora_sg]
        )

        # We either create or pull in an ECR repo for the app pipeline and ECS to use.
        # on inital deploy of ECS no image will be found, but the app pipeline should build and push a new image
        if ecr_repo_name is None:
            self.image_repo = ecr.Repository(self, "repo", repository_name=container_name, image_scan_on_push=True)
        else:
            self.image_repo = ecr.Repository.from_repository_name(self, "repo", ecr_repo_name)

        # Now make the ECS cluster, Task def, and Service
        self.ecs_cluster = ecs.Cluster(self, "BackstageCluster", vpc=self.vpc)

        # lets create a named role so its easy to find and modify policies for
        # This is the role which enables the container access to AWS services.
        self.task_role = iam.Role(
            self,
            "fargate-task-role",
            role_name='Backstage-Fargate-Task-Role',
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )
