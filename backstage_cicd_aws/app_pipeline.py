import yaml
from aws_cdk import (
    aws_ecs as ecs,
    aws_iam as iam,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as actions,
    Stack
)
from constructs import Construct


class AppPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props: dict, stages: dict, **kwargs) -> None:
        super().__init__(scope=scope, id=construct_id, **kwargs)
        # github info for codepipeline
        github_repo = props.get("GITHUB_APP_REPO")
        github_org = props.get("GITHUB_ORG")
        github_branch = props.get("GITHUB_APP_BRANCH", "main")
        codestar_connection_arn = props.get("CODESTAR_CONN_ARN")
        github_app_arn = props.get("GITHUB_APP_ARN")
        ### build a codepipeline for building new images and re-deploying to ecs
        ### this will use the backstage app repo as source to catch canges there
        ### execute a docker build and push image to ECR
        ### then execute ECS deployment
        ### once this pipeline is built we should only need to commit changes
        ### to the backstage app repo to deploy and update

        # create the output artifact space for the pipeline
        self.source_output = codepipeline.Artifact()
        self.build_output = codepipeline.Artifact()

        # setup source to be the backstage app source
        source_action = actions.CodeStarConnectionsSourceAction(
            action_name="Github-Source",
            connection_arn=codestar_connection_arn,
            repo=github_repo,
            owner=github_org,
            branch=github_branch,
            output=self.source_output
        )

        # make codebuild action to use buildspec.yml and feed in env vars from .env
        # this will build and push new image to ECR repo

        build_project = codebuild.PipelineProject(
            self,
            "CodebuildProject",
            project_name="backstage-app-pipeline",
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
            # has to be compiled at deploy time rather than execution time.
            environment=codebuild.BuildEnvironment(build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_5,
                                                   privileged=True),
        )
        # add policy to update push to ECR
        policy = iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryPowerUser")
        build_project.role.add_managed_policy(policy)
        # add policy to access secret in build
        secrets_policy = iam.PolicyStatement(
            resources=[github_app_arn],
            actions=['secretsmanager:GetSecretValue'],
        )
        build_project.add_to_role_policy(secrets_policy)

        # code build action will use docker to build new image and push to ECR
        # the buildspec.yaml is in the backstage app repo
        repo_uri = self.image_repo.repository_uri
        # repo_uri = '952379647918.dkr.ecr.ap-southeast-1.amazonaws.com/backstage'
        base_repo_uri = f"{props.get('AWS_ACCOUNT')}.dkr.ecr.{props.get('AWS_REGION')}.amazonaws.com"

        build_action = actions.CodeBuildAction(
            action_name="Docker-Build",
            project=build_project,
            input=self.source_output,
            outputs=[self.build_output],
            environment_variables={
                "BASE_REPO_URI": codebuild.BuildEnvironmentVariable(value=base_repo_uri),
                "GITHUB_APP_ARN": codebuild.BuildEnvironmentVariable(value=github_app_arn),
                "REPOSITORY_URI": codebuild.BuildEnvironmentVariable(value=repo_uri),
                "AWS_REGION": codebuild.BuildEnvironmentVariable(value=props.get("AWS_REGION")),
                "CONTAINER_NAME": codebuild.BuildEnvironmentVariable(value=props.get("CONTAINER_NAME")),
                "DOCKERFILE": codebuild.BuildEnvironmentVariable(value=props.get("DOCKERFILE", "dockerfile")),
            },
        )

        # ECS deploy actions will take file made in build stage and update the service with new image

        self.pipeline = codepipeline.Pipeline(self, "backstagepipeline", cross_account_keys=False,
                                              pipeline_name="backstage-app-pipeline")

        self.pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        self.pipeline.add_stage(
            stage_name="Build",
            actions=[build_action]
        )

        # we add deploy stages to the pipeline based on stages dict.
        for name, stage in stages.items():
            # dont pass these into the ECS container env.
            approval = stage.pop('STAGE_APPROVAL', False)
            emails = stage.pop('APPROVAL_EMAILS', None)
            # overload the shared env vars with those for the stage specifics if required. 
            props = {
                **props,
                **stage
            }

            # add a ECS deploy stage with the stage specific service, and an approval stage if requested.
            self.pipeline.add_deploy_stage(name, self.ecs_stack.service, approval, emails)

    def add_deploy_stage(self, name: str, fargate_service: ecs.IBaseService, approval: bool = False, emails: list = []):
        dps = self.pipeline.add_stage(
            stage_name=name + "-deploy"
        )
        runorder = 1
        if approval:
            dps.add_action(
                actions.ManualApprovalAction(action_name=name + "-stage-approval", notify_emails=emails,
                                             run_order=runorder)
            )
            runorder += 1
        dps.add_action(
            actions.EcsDeployAction(
                service=fargate_service,
                action_name=name + "-deploy",
                input=self.build_output,
                run_order=runorder
            )
        )
