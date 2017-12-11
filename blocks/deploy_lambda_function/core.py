import json
import logging
import os
import sys
import time
from imp import load_source
from shutil import copy
from shutil import copyfile
from tempfile import mkdtemp

import boto3
import botocore
import pip
import yaml



from data_utils import archive
from data_utils import mkdir
from data_utils import read
from data_utils import timestamp




def get_role_name(account_id, role):
    #Shortcut to insert the `account_id` and `role` into the iam string.
    return 'arn:aws:iam::{0}:role/{1}'.format(account_id, role)


def get_account_id(aws_access_key_id, aws_secret_access_key):
    #Query STS for a users' account_id
    client = get_client('sts', aws_access_key_id, aws_secret_access_key)
    return client.get_caller_identity().get('Account')


def get_client(client, aws_access_key_id, aws_secret_access_key, region=None):
    #Shortcut for getting an initialized instance of the boto3 client.

    return boto3.client(
        client,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region
    )


def main(src, path_to_zip_file):
    """
    @Block
    :desc: Register and upload a function to AWS Lambda.

    :param src: path to lambda function 
    :type src: string
    :example src: my_lambda_function

    :param path_to_zip_file: path to the zip file to deploy
    :type path_to_zip_file: string 
    :example path_to_zip_file: my_lambda_function/dist/myzip.zip 

    """

    print('Creating your new Lambda function')


    path_to_config_file = os.path.join(src, 'config.yaml')
    cfg = read(path_to_config_file, loader=yaml.load)


    if function_exists(cfg, cfg.get('function_name')):
        update_function(cfg, path_to_zip_file)
    else:
        

        byte_stream = read(path_to_zip_file)
        aws_access_key_id = cfg.get('aws_access_key_id')
        aws_secret_access_key = cfg.get('aws_secret_access_key')

        account_id = get_account_id(aws_access_key_id, aws_secret_access_key)
        role = get_role_name(account_id, cfg.get('role', 'lambda_basic_execution'))

        client = get_client('lambda', aws_access_key_id, aws_secret_access_key,
                            cfg.get('region'))

        # Do we prefer development variable over config?
        func_name = (
            os.environ.get('LAMBDA_FUNCTION_NAME') or cfg.get('function_name')
        )
        print('Creating lambda function with name: {}'.format(func_name))
        kwargs = {
            'FunctionName': func_name,
            'Runtime': cfg.get('runtime', 'python2.7'),
            'Role': role,
            'Handler': cfg.get('handler'),
            'Code': {'ZipFile': byte_stream},
            'Description': cfg.get('description'),
            'Timeout': cfg.get('timeout', 15),
            'MemorySize': cfg.get('memory_size', 512),
            'Publish': True
        }

        if 'environment_variables' in cfg:
            kwargs.update(
                Environment={
                    'Variables': {
                        key: value
                        for key, value
                        in cfg.get('environment_variables').items()
                    }
                }
            )

        client.create_function(**kwargs)


def update_function(cfg, path_to_zip_file):
    #Updates the code of an existing Lambda function

    print('Updating your Lambda function')
    byte_stream = read(path_to_zip_file)
    aws_access_key_id = cfg.get('aws_access_key_id')
    aws_secret_access_key = cfg.get('aws_secret_access_key')

    account_id = get_account_id(aws_access_key_id, aws_secret_access_key)
    role = get_role_name(account_id, cfg.get('role', 'lambda_basic_execution'))

    client = get_client('lambda', aws_access_key_id, aws_secret_access_key,
                        cfg.get('region'))

    client.update_function_code(
        FunctionName=cfg.get('function_name'),
        ZipFile=byte_stream,
        Publish=True
    )

    kwargs = {
        'FunctionName': cfg.get('function_name'),
        'Role': role,
        'Handler': cfg.get('handler'),
        'Description': cfg.get('description'),
        'Timeout': cfg.get('timeout', 15),
        'MemorySize': cfg.get('memory_size', 512),
        'VpcConfig': {
            'SubnetIds': cfg.get('subnet_ids', []),
            'SecurityGroupIds': cfg.get('security_group_ids', [])
        }
    }

    if 'environment_variables' in cfg:
        kwargs.update(
            Environment={
                'Variables': {
                    key: value
                    for key, value
                    in cfg.get('environment_variables').items()
                }
            }
        )

    client.update_function_configuration(**kwargs)


def function_exists(cfg, function_name):
    #Check whether a function exists or not

    aws_access_key_id = cfg.get('aws_access_key_id')
    aws_secret_access_key = cfg.get('aws_secret_access_key')
    client = get_client('lambda', aws_access_key_id, aws_secret_access_key,
                        cfg.get('region'))
    functions = client.list_functions().get('Functions', [])
    for fn in functions:
        if fn.get('FunctionName') == function_name:
            return True
    return False
