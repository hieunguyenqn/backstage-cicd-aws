import aws_cdk as core
import aws_cdk.assertions as assertions

from backstage_cicd_aws.backstage_cicd_aws_stack import BackstageCicdAwsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in backstage_cicd_aws/backstage_cicd_aws_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = BackstageCicdAwsStack(app, "backstage-cicd-aws")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
