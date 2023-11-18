#!/usr/bin/env python3
import aws_cdk as cdk
import yaml

from backstage_cicd_aws.infra_pipeline import InfraPipelineStack

# load yaml file and get key value for env
with open("./configs/env-config.yaml") as confFile:
    conf = yaml.full_load(confFile)
props = conf['common']

# start the naming circus
stack_name = props.get('TAG_STACK_NAME', 'backstage')

stacks = [
    f"{stack_name}-pipeline",
    stack_name
]

env = cdk.Environment(account=props.get('AWS_ACCOUNT'), region=props.get('AWS_REGION', 'us-east-1'))

app = cdk.App()

infra_pipeline = InfraPipelineStack(app, stacks[0], stacks=stacks, props=props, env=env)

app.synth()
