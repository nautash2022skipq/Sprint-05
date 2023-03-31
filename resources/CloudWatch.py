import boto3

class AWSCloudWatch:
    def __init__(self):
        self.cw_client = boto3.client('cloudwatch')
        
    def cw_put_metric_data(self, namespace, metric_name, dimensions, value):
        
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.put_metric_data
        response = self.cw_client.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Dimensions': dimensions,
                    'Value': value,
                },
            ]
        )