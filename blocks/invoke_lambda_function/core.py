import json
import boto3
import boto3.session
from botocore.client import Config

def main(event, function_name, region_name, aws_access_key_id,
         aws_secret_access_key, timeout=270):
    """
    @Block
    :desc: Invoke a lambda function with a custom event

    :param event: A dictionary that will be passed to the lambda function
    :type event: dict
    :example event: {"list_of_jobs": [{"path_to_zip":"tax-deeds-scraper.zip"}]}

    :param function_name: Name of the AWS lambda function
    :type function_name: string
    :example function_name: "SeleniumLambda"

    :param region_name: AWS region name
    :type region_name: string
    :example region_name: "us-east-1"

    :param aws_access_key_id: AWS access key
    :type aws_access_key_id: string
    :example aws_access_key_id: "

    :param aws_secret_access_key: AWS secret key
    :type aws_secret_access_key: string
    :example aws_secret_access_key:

    :returns: Response from AWS lambda
    :type: dict
    :example: {u'Payload': <botocore.response.StreamingBody object at 0x1012f0fd0>, 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': 'ddcd3243-5797-11e7-ab88-3ff4c6e62606', 'HTTPHeaders': {'x-amzn-requestid': 'ddcd3243-5797-11e7-ab88-3ff4c6e62606', 'content-length': '16', 'x-amzn-trace-id': 'root=1-594c40c7-04ace324ffe2777d268d283b;sampled=0', 'x-amzn-remapped-content-length': '0', 'connection': 'keep-alive', 'date': 'Thu, 22 Jun 2017 22:12:22 GMT', 'content-type': 'application/json'}}, u'StatusCode': 200}
    """

    config = Config(connect_timeout=60, read_timeout=270)
    session = boto3.session.Session()
    client = session.client('lambda',
                          region_name=region_name,
                          aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key,
                          config=config)
    res = client.invoke(FunctionName=function_name,
                        InvocationType='RequestResponse',
                        Payload=json.dumps(event))

    return res
