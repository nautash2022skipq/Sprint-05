import os, json, urllib3, datetime
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
    
    # Getting environment variable passed from the stack to lambda construct
    api_gw_url = os.environ['apiGatewayUrl']
    print(api_gw_url)
    
    urls = getUrlsFromDynamo(api_gw_url)
    print(urls)
    
    if not urls:
        print('Reading constant URLS')
        urls = URLS
    
    for url in urls:
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


def getUrlsFromDynamo(url):
    http = urllib3.PoolManager()
    res = http.request("GET", url)
    
    urls = []
    if res.status == 200:
        data = res.data
        
        # https://stackoverflow.com/questions/40059654/convert-a-bytes-array-into-json-format
        data = data.decode('utf8').replace("'", '"')
        data = json.loads(data)
        
        for record in data:
            for k, v in record.items():
                if k == 'url':
                    urls.append(v)
                    
    return urls