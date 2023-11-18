from aws_cdk import Stack, SecretValue
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as actions
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_iam as iam
from constructs import Construct


class InfraPipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, stacks: list, props: dict, **kwargs) -> None:
        super().__init__(scope=scope, id=id, **kwargs)
         # github info for codepipeline
        github_repo = props.get("GITHUB_INFRA_REPO")
        github_org = props.get("GITHUB_ORG")
        github_branch = props.get("GITHUB_INFRA_BRANCH", "main")
        codestar_connection_arn = props.get("CODESTAR_CONN_ARN")

        # create the output artifact space for the pipeline
        source_output = codepipeline.Artifact()
        synth_output = codepipeline.Artifact()
        # Create a GitHub source action
        # setup source to be the backstage app source
        source_action = actions.CodeStarConnectionsSourceAction(
            action_name="Github-Source",
            connection_arn=codestar_connection_arn,
            repo=github_repo,
            owner=github_org,
            branch=github_branch,
            output=source_output
        )
        # Create a CodePipeline pipeline
        pipeline = codepipeline.Pipeline(self, "infra-pipeline", pipeline_name=id)

        # Add the source action to the pipeline
        pipeline.add_stage(
            stage_name='Source',
            actions=[source_action]
        )

        synth_project = codebuild.PipelineProject(
            self,
            "CodebuildProject",
            project_name=id,
            build_spec=codebuild.BuildSpec.from_source_filename('./infra-buildspec.yml'),
            environment=codebuild.BuildEnvironment(build_image=codebuild.LinuxBuildImage.STANDARD_7_0)
        )
        # lookups needed by backstage stack have to have permissions added in order to synth
        codebuild_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=["*"],
            actions=["*"],
        )

        synth_project.add_to_role_policy(codebuild_policy)

        synth_action = actions.CodeBuildAction(
            action_name="Synth",
            project=synth_project,
            input=source_output,
            outputs=[synth_output],
        )
        pipeline.add_stage(
            stage_name="Build",
            actions=[synth_action]
        )

        for stack in stacks:
            change_set_name = f"{stack}-changeset"
            pipeline.add_stage(
                stage_name=f"Deploy-{stack}",
                actions=[
                    actions.CloudFormationCreateReplaceChangeSetAction(
                        action_name=f"Create-{stack}-ChangeSet",
                        stack_name=stack,
                        template_path=synth_output.at_path(f"{stack}.template.json"),
                        admin_permissions=True,
                        change_set_name=change_set_name,
                        run_order=1
                    ),
                    actions.CloudFormationExecuteChangeSetAction(
                        action_name=f"Exec-{stack}-ChangeSet",
                        stack_name=stack,
                        change_set_name=change_set_name,
                        run_order=2
                    )
                ]
            )
