'''
Copyright (c) 2021 Scott Cunningham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Summary: This script is designed to parse and modify an MPEG DASH manifest.

Original Author: Scott Cunningham
'''

import json
import boto3
import logging
import os
import re
import datetime

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

bucket = os.environ['BUCKET']
data_file_key = os.environ['DATA_KEY']

def lambda_handler(event, context):
    
    # API template response to API Gateway, for 200 or 500 responses
    def api_response(status_code,message):
        response_body = {
            "statusCode":status_code,
            "headers":{
                "Content-Type":"application/json"
                },
            "body":json.dumps({"status":message})
            }
        return response_body
    
    
    # TODO implement
    LOGGER.info("API Call received: %s " % (event))
    
    # Get body from event
    event_body = json.loads(event['body'])
    
    ## Initialize S3 boto3 client
    s3 = boto3.client('s3')

    # Get existing file from S3 and pull into dict object
    try:
        current_data_json_file = s3.get_object(Bucket=bucket, Key=data_file_key)
    except Exception as e:
        LOGGER.error("Error getting data file from S3 : %s " % (e))
        api_response(500,"Error getting data file from S3 : %s " % (e))
        raise Exception("Error getting data file from S3 : %s " % (e))
    
    # Read S3 object response into Variable
    current_data_json = json.loads(current_data_json_file['Body'].read())
    new_data_json = current_data_json

    # Initialize dictionary for each main key type. After the data.json file is retrieved from S3, we will replace only the keys that were sent in the API call
    new_metrics = dict()
    new_ticker = dict()
    expires = 0
    got_new_data = False
    
    # first, check if the old data.json is expired, if so - delete the contents before proceeding
    if int(current_data_json['expires']) < int(datetime.datetime.utcnow().strftime('%s')) and int(current_data_json['expires']) > 0:
        # delete 'metrics' and 'ticker' data, and reset 'expires' to 0
        current_data_json['metrics'] = {}
        current_data_json['ticker'] = {}
        current_data_json['expires'] = 0
        
    if "metrics" in event_body.keys():
        # Received Metrics
        LOGGER.info("Received metrics in API call : %s " % (event_body['metrics']))
        
        html5_metrics_data = dict()
        def dict_path(path,my_dict):
            for k,v in my_dict.items():
                if isinstance(v,dict):
                    dict_path(path+".."+k,v)
                else:
                    html5_metrics_data.update({path+".."+k:v})
            return html5_metrics_data
        new_metrics = dict_path("",event_body['metrics'])
        
        new_data_json['metrics'] = new_metrics
        got_new_data = True
    else:
        new_data_json['metrics'] = current_data_json['metrics']
    
    if "ticker" in event_body.keys():
        LOGGER.info("Received ticker data in API call : %s " % (event_body['ticker']))
        # Ticker needs 2 keys: message / speed (optional)
        if "message" in event_body['ticker'].keys():
            # Message is present
            new_ticker['message'] = event_body['ticker']['message']
        else:
            new_ticker['message'] = current_data_json['ticker']['message']
        
        if "speed" in event_body['ticker'].keys():
            # speed value is present
            # check value to make sure it's valid
            if bool(re.search("^[1-5]{1}", str(event_body['ticker']['speed']))):
                new_ticker['speed'] = int(event_body['ticker']['speed'])
            else:
                LOGGER.warning("Received ticker speed value but it was not valid. Expected 1-5, got : %s" % (str(event_body['ticker']['speed'])))
                new_ticker['speed'] = 1 # default to 1 if incorrect speed value is sent
        else:
            new_ticker['speed'] = current_data_json['ticker']['speed']
            
        new_data_json['ticker'] = new_ticker
        got_new_data = True
            
    if "expires" in event_body.keys():
        LOGGER.info("Received expiry value in API call : %s " % (event_body['expires']))
        if bool(re.search("^[0-9]*$",str(event_body['expires']))):
            expires = int(event_body['expires'])
            if int(expires) == 0:
                expires = 0
            else:
                expires = int(datetime.datetime.utcnow().strftime('%s')) + int(event_body['expires'])
        else:
            LOGGER.warning("The expires value sent doesn't seem to be an integer. Received this value: %s " % (event_body['expires']))
            expires = 0 # defaulting to indefinite display / no expiry
        
        # overwriting existing data.json
        new_data_json['expires'] = expires
        got_new_data = True
    
    if got_new_data:
        # If we received a key of 'metric' 'ticker' or 'expires' in the API call, along with valid values, then we update the data.json file in S3
        
        # Put new data file to S3, overwriting the existing only where necessary
        try:
            s3_response = s3.put_object(Body=json.dumps(new_data_json), Bucket=bucket, Key=data_file_key, ContentType='application/json', ACL='public-read', CacheControl='no-cache')
            LOGGER.debug("PUT new stat file to S3, got response : %s " % (s3_response) )
            LOGGER.info("New Stat file : %s " % (new_data_json))
            return api_response(200,"Completed upload of new data to S3")
        except Exception as e:
            LOGGER.error("Unable to put new data.json file to S3, got exception: %s" % (e))
            return api_response(500,"Error uploading new data to S3 : %s " % (e))
    else:
        LOGGER.warning("Received an API call, but it doesn't contain any useful data, not doing anything. This is what we received : %s " % (event_body))
        return api_response(500,"Received an API call, but it doesn't contain any useful data, not doing anything. This is what we received : %s " % (event_body))