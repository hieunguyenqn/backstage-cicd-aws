# from dotenv import dotenv_values
from aws_cdk import (
    Stack
)
from constructs import Construct

# from collections import OrderedDict
from .common_resources import CommonResourceStack


class BackstageStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, props: dict, stages: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        crs = CommonResourceStack(self, "infra-common-resources", props)
