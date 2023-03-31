import urllib3, datetime
from CloudWatch import AWSCloudWatch
from constants import (
    URLS,
    NAMESPACE,
    AVAILABILITY_METRIC,
    LATENCY_METRIC
)

def lambda_handler(event, context):
    metrics = dict()
    
    # Creating AWS CloudWatch object
    cw_obj = AWSCloudWatch()
    
    for url in URLS:
        availability = getAvailability(url)
        latency = getLactency(url)
                
        metrics.update({
            url: f'availability: {availability} ---- latency: {latency}'
        })
        
        # Sending metric data to CloudWatch
        dimensions = [{'Name': 'URL', 'Value': url}]
        cw_obj.cw_put_metric_data(NAMESPACE, AVAILABILITY_METRIC, dimensions, availability)
        cw_obj.cw_put_metric_data(NAMESPACE, LATENCY_METRIC, dimensions, latency)
    
    return metrics


def getAvailability(url):
    http = urllib3.PoolManager()
    res = http.request("GET", url)
    
    if res.status == 200:
        return 1
    return 0


def getLactency(url):
    http = urllib3.PoolManager()
    
    start = datetime.datetime.now()
    res = http.request("GET", url)
    end = datetime.datetime.now()
    
    diff = end - start
    latency = round(diff.microseconds * .000001, 6)
    
    return latency