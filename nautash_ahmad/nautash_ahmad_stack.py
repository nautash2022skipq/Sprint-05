from aws_cdk import (
    Duration,
    aws_lambda as lambda_,
    aws_events as events_,
    aws_events_targets as targets_,
    aws_iam as iam_,
    aws_cloudwatch as cw_,
    aws_sns as sns_,
    aws_sns_subscriptions as subscriptions_,
    aws_cloudwatch_actions as cw_actions_,
    aws_dynamodb as dynamo_,
    aws_codedeploy as codedeploy_,
    Stack,
    RemovalPolicy,
)
from constructs import Construct
from resources import constants

class NautashAhmadStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        role = self.create_lambda_role()
        
        fn = self.create_lambda("WebHealthLambda", "./resources", "WebHealthAppLambda.lambda_handler", 
            role, 2
        )
        
        # Adding metrics for lambda to monitor it
        lambda_duration_metric = fn.metric_duration()
        lambda_invocation_metric = fn.metric_invocations()
        lambda_error_metric = fn.metric_errors()
        
        # Addding CloudWatch alrams for lambda function to monitor
        lambda_duration_alarm = self.create_cw_alarm(f'LambdaDurationMetricAlarm', 5, 
            cw_.ComparisonOperator.GREATER_THAN_THRESHOLD, constants.MINS, 
            lambda_duration_metric
        )
        
        lambda_invocation_alarm = self.create_cw_alarm(f'LambdaInvocationMetricAlarm', 5, 
            cw_.ComparisonOperator.GREATER_THAN_THRESHOLD, constants.MINS, 
            lambda_invocation_metric
        )
        
        lambda_error_alarm = self.create_cw_alarm(f'LambdaErrorMetricAlarm', 3, 
            cw_.ComparisonOperator.GREATER_THAN_THRESHOLD, constants.MINS, 
            lambda_error_metric
        )
        
        # Creating alias for deployment configuration. Need to make sure each cdk synthesis produces different version in is each deployment
        # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_codedeploy/LambdaDeploymentConfig.html
        version = fn.current_version
        alias = lambda_.Alias(self, "LambdaAlias",
            alias_name="WebHealthLambdaAlias",
            version=version
        )
        
        # Deployemnt configuration
        # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_codedeploy/LambdaDeploymentGroup.html
        # https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_codedeploy/LambdaDeploymentConfig.html
        deployment_group = codedeploy_.LambdaDeploymentGroup(self, "WebHealthLambdaDeploymentGroup",
            alias=alias,
            deployment_config=codedeploy_.LambdaDeploymentConfig.LINEAR_10_PERCENT_EVERY_10_MINUTES,
            alarms=[lambda_duration_alarm, lambda_invocation_alarm, lambda_error_alarm]
        )
        
        # Removal policy to automatically delete stateless and stateful resources
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk/RemovalPolicy.html#aws_cdk.RemovalPolicy
        fn.apply_removal_policy(RemovalPolicy.DESTROY)
        
        # Creating lambda for dynamo handler
        dynamo_lambda = self.create_lambda("WebHealthDynamoLambda", "./resources", "WebHealthDynamoLambda.lambda_handler", 
            role, 2
        )
        
        # Creating a rule to make our Lambda a cronjob and giving it a target
        # Schedule rule: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events/Schedule.html
        rule = events_.Rule(self, "WebHealthLambdaRule",
            schedule=events_.Schedule.rate(Duration.minutes(constants.MINS)),
            
            # Target: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events_targets/LambdaFunction.html
            targets=[targets_.LambdaFunction(handler=fn)]
        )
        
        rule.apply_removal_policy(RemovalPolicy.DESTROY)
        
        # Creating DynamoDB table
        dynamo_table = self.create_dynamodb_table('WebHealthDynamoTable', 'id', 'timestamp')
        dynamo_table.grant_full_access(dynamo_lambda)
        
        # Adding environment variable to Lambda
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html#aws_cdk.aws_lambda.Function.add_environment
        dynamo_lambda.add_environment('tableName' ,dynamo_table.table_name)
        
        # Creating SNS topic and subscription
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html
        topic = sns_.Topic(self, "WebHealthAlarmTopic")
        
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/EmailSubscription.html
        topic.add_subscription(subscriptions_.EmailSubscription('nautash.ahmad.skipq@gmail.com'))
        
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/LambdaSubscription.html
        topic.add_subscription(subscriptions_.LambdaSubscription(dynamo_lambda))
        
        '''
            Creating two metrics for a website which are availability and latency
            Alarms will be created for each of these metrics
        '''
        for url in constants.URLS:
            dimensions = {'URL': url}
            availability_metric = self.create_cw_metric(constants.NAMESPACE, constants.AVAILABILITY_METRIC, dimensions)
            availability_alarm = self.create_cw_alarm(f'{url}_availability_errors', 1, cw_.ComparisonOperator.LESS_THAN_THRESHOLD, constants.MINS, availability_metric)
            
            latency_metric = self.create_cw_metric(constants.NAMESPACE, constants.LATENCY_METRIC, dimensions)
            latency_alarm = self.create_cw_alarm(f'{url}_latency_errors', 0.3, cw_.ComparisonOperator.GREATER_THAN_THRESHOLD, constants.MINS, latency_metric)
        
            # Connecting CloudWatch alarms with SNS topic to send notifications when alaram is triggered
            # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch_actions/SnsAction.html
            availability_alarm.add_alarm_action(cw_actions_.SnsAction(topic))
            latency_alarm.add_alarm_action(cw_actions_.SnsAction(topic))
        
        
    # Create Lambda construct
    # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html
    def create_lambda(self, id, assest_path, handler, role, timeout_min):
        return lambda_.Function(self, 
            id=id,
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler=handler,
            code=lambda_.Code.from_asset(assest_path),
            role=role,
            timeout=Duration.minutes(timeout_min)
        )
        
        
    # Create IAM Role for Lambda
    # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/Role.html
    def create_lambda_role(self):
        return iam_.Role(self, "WebHealthAppLambdaRole",
            assumed_by=iam_.ServicePrincipal("lambda.amazonaws.com"),
            
            # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/ManagedPolicy.html#aws_cdk.aws_iam.ManagedPolicy.from_aws_managed_policy_name
            managed_policies=[
                iam_.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam_.ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess"),
                iam_.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess")
            ]
        )
        
        
    # Create CloudWatch alarm
    # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html
    def create_cw_alarm(self, id, threshold, comparison_operator, mins, metric):
        return cw_.Alarm(self, 
            id=id,
            threshold=threshold,
            comparison_operator=comparison_operator,
            evaluation_periods=mins,
            metric=metric
        )
        
        
    # Create CloudWatch metric
    # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Metric.html
    def create_cw_metric(self, metric_name, namespace, dimensions):
        return cw_.Metric(
            metric_name=metric_name,
            namespace=namespace,
            dimensions_map=dimensions
        )
        
        
    # Create AWS DynamoDB table
    # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
    def create_dynamodb_table(self, id, partition_key, sort_key):
        return dynamo_.Table(self, 
            id=id,
            partition_key=dynamo_.Attribute(name=partition_key, type=dynamo_.AttributeType.STRING),
            sort_key=dynamo_.Attribute(name=sort_key, type=dynamo_.AttributeType.STRING),
            billing_mode=dynamo_.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )