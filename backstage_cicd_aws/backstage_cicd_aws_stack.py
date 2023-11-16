
from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct

class BackstageCicdAwsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # github info for codepipeline
        github_repo = props.get("GITHUB_APP_REPO")
        github_org = props.get("GITHUB_ORG")
        github_branch = props.get("GITHUB_APP_BRANCH", "main")
        codestar_connection_arn = props.get("CODESTAR_CONN_ARN")
        github_app_arn = props.get("GITHUB_APP_ARN")
