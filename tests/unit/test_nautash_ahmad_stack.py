import pytest
import aws_cdk as core
import aws_cdk.assertions as assertions

from nautash_ahmad.nautash_ahmad_stack import NautashAhmadStack

# Writing a fixture
# https://realpython.com/pytest-python-testing/#when-to-create-fixtures

@pytest.fixture
def stack_template():
    app = core.App()
    stack = NautashAhmadStack(app, "nautash-ahmad")
    template = assertions.Template.from_stack(stack)
    
    return template


# ------- Unit tests ------- #

# Template: https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.assertions/Template.html
# Assertions: https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.assertions/README.html

def test_have_two_lambdas(stack_template):
    template = stack_template
    template.resource_count_is('AWS::Lambda::Function', 2)
    
    
def test_has_lambda_s3key_prop(stack_template):
    template = stack_template
    template.has_resource_properties("AWS::Lambda::Function", props={
        'Handler': 'WebHealthAppLambda.lambda_handler',
        'Runtime': 'python3.8',
        'Timeout': 120
    })
    
    
def test_has_dynamo_resource(stack_template):
    template = stack_template
    template.find_resources('AWS::DynamoDB::Table')
    
    
def test_has_cdk_condition(stack_template):
    template = stack_template
    template.find_conditions("CDKMetadataAvailable")
    
    
def test_has_parameters(stack_template):
    template = stack_template
    template.find_parameters('BootstrapVersion')