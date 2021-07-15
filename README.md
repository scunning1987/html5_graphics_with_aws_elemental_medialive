# HTML5 Graphics With AWS Elemental MediaLive
## Overview
These instructions and templates outline how to deploy a solution that utilizes AWS Elemental MediaLive's HTML5 graphics functionality to display metric data received via an API call.

1. Video is ingested into MediaLive (using MediaConnect, RTMP, RTP/FEC, HLS, CDI, etc...).
2. The MediaLive channel must be configured with HTML5 graphics enabled. Please note there is a cost associated with this feature. See AWS Elemental MediaLive pricing page for details
3. Data is received via API call, and is pushed via Lambda to a data file on Amazon S3
4. The HTML5 pages (html,js,css) are also on Amazon S3, and the Javascript code references the data file when rendering the HTML page
5. MediaLive is continually polling the HTML page and updates near real time with new information from the data file

![](images/html5-blog-part-1.png?width=60pc&classes=border,shadow)

Example data sent in API call:

```
POST aws.apigateway.com/myendpoint.net/v1/newdata

{
   "metrics":{
    "key_metric_1": "91.1",
    "key_metric_2": "2420.8813",
  },
  "ticker":{
    "message":"Hello from your friends at AWS",
    "speed":5
  },
   "expires":600
}
```

Example rendered page:

![](images/html5-render-1.png?width=60pc&classes=border,shadow)

## How to Deploy
### Prerequisites
In order to complete this deployment in your environment. Make sure you have achieved all the prerequisites first:

* You need an AWS Account, if you don’t have one, you can create an account at https://aws.amazon.com
* IAM user/role with privileged access. To deploy the services in these instructions, your user must be able to create IAM roles & policies, deploy Amazon API Gateway endpoints, create AWS Lambda functions, create Amazon S3 buckets, and create MediaLive channels.
* These instructions assume you have the video pipeline already deployed with a valid source for an existing AWS Elemental Live channel. See this [blog post](https://aws.amazon.com/blogs/media/awse-quickly-creat-live-streaming-channel-aws-elemental-medialive-workflow-wizard/) if you need help in this area 

### Services used in this blog post

* AWS IAM
* AWS Elemental MediaLive
* Amazon S3
* AWS Lambda
* Amazon API Gateway

### Deployment Instructions - Via CloudFormation
1. Login to your AWS account
2. Using the search navigation, or the services summary page, navigate to the CloudFormation console
3. From the CloudFormation dashboard home, select *Create Stack - with new resources*
4. Select *Template is ready* then *Upload a template file*
5. Browse to [this CloudFormation template](cloudformation/html5_graphics_with_aws_elemental_medialive.yaml) after you save locally
6. Select *Next*
7. Give the stack a name, a deployment name (these can be the same), and HTML Path location. The path location is just a relative url where the HTML pages will be written to, ie. `medialive/html`
8. Select *Next*
9. The stack options page has parameters that are optional for you to complete, you can skip and select *Next*
10. Scroll to the bottom of the review page, acknowledge that CloudFormation is able to create IAM roles/policies and select *Create stack*

After the stack creation is completed, you can go to the Outputs tab of the stack summary to find your APIEndpointURL and HTMLPage location

For further instructions on how to use this deployment, go to the [Testing the System](#testing-the-system) section below

### Deployment Instructions - Via the AWS Console

Please ensure you deploy **all** the below services in the same region.

#### Amazon S3

1. Login to your AWS account
2. Using the search navigation, or the services summary page, navigate to the S3 console
3. Select *Create bucket*
4. Give your bucket a name (this must be a globally unique name as it becomes part of your object retrieval URL
5. Under *Block Public Access settings for this bucket*, uncheck this box and acknowledge the security warning

| TIP: If public access to your bucket is a violation of your security policies, you could instead create public access via a CloudFront distribution, see this [blog](https://aws.amazon.com/premiumsupport/knowledge-center/cloudfront-access-to-amazon-s3/) for more instructions  |
| --- | 

6. Leave all other settings as default and select *Create bucket*
7. Select your bucket from the bucket summary, then select *Create folder*
8. Name your folder : medialive-html5 (if you name it something else, take note as it will affect our IAM policy later)
9. Inside the newly created folder, upload the HTML files:
    1. html5_functions.js [link](html_pages/html5_functions.js)
    2. html5_page.html [link](html_pages/html5_page.html)
    3. html5_style.css [link](html_pages/html5_style.css)
    4. data.json [link](html_pages/data.json)
10. Select the checkmark next to each of the newly created files, then select the *Actions* drop-down menu and select *Make public*
11. After the task completes successfully, select the *Close* button to go back to the object view
12. Now select on the hyperlink of the json file, data.json
13. Copy the *S3 URI* to be used later in the AWS Lambda function
14. Now select on the hyperlink of the html page, html5_page.html
15. Copy the *Amazon Resource Name (ARN)* to be used later in IAM
16. Copy the *Object URL* and paste into a new tab in your browser. The template page should load with sample data

| TIP: Save the HTTPS URL for this HTML page as it will be needed in your MediaLive channnel later |
| --- |

17. You can now close the S3 Console

#### AWS IAM

Before our AWS services can interact with one another, we must setup the right roles and policies for them to do so.

1. Login to your AWS account
2. Using the search navigation, or the services summary page, navigate to the IAM console
3. In the Navigation pane, select *Policies*, then *Create policy*
4. Use the Visual editor to create the policy; under Service select *S3*
5. Under Actions, select *All S3 actions*
6. Under Resources, select *bucket - Add ARN*
7. In the window that pops up, paste the ARN copied from the HTML object earlier, but replace the key name from the ARN with an asterisk (example : arn:aws:s3:::bucket1/medialive-html5/*)
8. Select *Save changes* to close this window
9. Leave *Request conditions* as default and select *Next:Tags*
10. Enter tags if required for your corporate policy, else select *Next:Review*
11. Give the policy a name, for example : AccessToS3HTML5
12. Optionally, give the policy a description to further identify the policy, for example: Custom policy to access specific MediaLive HTML Pages on S3 bucket ‘bucket1’
13. Select *Create policy*
14. In the Navigation pane, select *Role*, then *Create role*
15. Under the heading *Or select a service to view its use cases common*, select *Lambda*, then *Next:Permissions*
16. Type " LambdaBasicExecutionRole " , then select the checkmark next to the result. This policy allows our Lambda function to write to Amazon CloudWatch logs, which is useful for debugging
17. Clear the search bar and then type the name of the policy created just earlier “ AccessToS3HTML5 ”, then select the checkmark next to the result
18. Select *Next:Tags*
19. Enter tags if required for your corporate policy, else select *Next:Review*
20. Give the role a name, for example : AWSLambdaAccessToS3HTML
21. Optionally, give the role a description to further identify the role, for example: AWS Lambda role to access S3 bucket for MediaLive HTML5 Graphics Overlay workflow
22. Select *Create role*
23. You can now close the IAM Console

#### AWS Lambda

1. Login to your AWS account
2. Using the search navigation, or the services summary page, navigate to the Lambda console
3. From the navigation pane on the right, select *Functions*, then select *Create function*
4. Under Create function, select *Author from scratch*
5. Name the function : medialive_html5_api_handler
6. Under runtime, select Python 3.8
7. Under Permissions, expand *Change default execution role*
8. Under Execution role, select *Use an existing role*, select the dropdown and search for the AWS Lambda role you made earlier (AWSLambdaAccessToS3HTML)
9. Select *Create function*
10. In the Function code block, select the *Upload from* drop-down menu and browse to [this Lambda function](lambda/medialive_html5_api_handler.zip)
11. Import the zip file!
12. In the Configuration tab, select *Environment Variables*
13. Edit the environment variables for BUCKET and DATA_KEY to match your newly created bucket and key path for the data.json file you uploaded earlier. The S3 URI looks like this: s3://cunsco-bucket1/medialive-html5/data.json
   1. The BUCKET is the first part of the URI : cunsco-bucket1
   2. The DATA_KEY is the rest: medialive-html5/data.json
14. You can now close the Lambda Console

#### API Gateway

1. Login to your AWS account
2. Using the search navigation, or the services summary page, navigate to the API Gateway console
3. Select *Create API*
4. Under API Type, select *REST API - Import*
5. In the Import from Swagger or Open API3 section, select the *Select Swagger File* button and upload [this API Gateway template](api_gateway/html5_data_ingest-v1-swagger-apigateway.json)
6. Select the *Import* button
7. Under Resources, select the *Any* method, then select the *Integration Request* box
8. Select the edit pencil next to *Lambda Region*, and select your Lambda region, then select the tick box to the right of the field
9. Select the edit pencil next to *Lambda Function*, delete the text in this field and start typing the name of your Lambda function until it auto-populates, then select the tick box to the right of the field
10. Now select the 'root slash' / under the Resources pane, then select the *Actions* button, then *Deploy API*
11. In the popup box that appears, select a new deployment stage, and give it name *v1*, then select the *Deploy* button
12. Retrieve your Invoke URL by selecting the *Stages* pane, then expand your v1 stage until you see methods under the /{proxy+} Resource, select the GET method, and note the Invoke URL that appears. It will look something like:

| Invoke URL: https://12345abcde.execute-api.us-west-2.amazonaws.com/v1/{proxy+} |
|---|

13. You can now close the API Gateway console

#### AWS Elemental MediaLive
**Setting up your video pipeline**
If you need help in setting up your MediaLive video pipeline, see the below blog post that utilizes the MediaLive Workflow Wizard.
https://aws.amazon.com/blogs/media/awse-quickly-creat-live-streaming-channel-aws-elemental-medialive-workflow-wizard/ 

**Enabling HTML5 motion graphics for your channel**
In order to utilize the HTML5 graphics overlay feature on your MediaLive channel(s), you must enable it in the MediaLive channel. The below instructions detail how to do this:

1. Login to your AWS account
2. Using the search navigation, or the services summary page, navigate to the MediaLive console
3. Your channel must be in a IDLE state for editing. If it is currently in STARTED state, select the checkbox next to your channel and then select the *Stop* button
4. Select the checkbox next to your channel, then select the *Actions* dropdown menu, followed by *Edit channel*
5. Go to the Channel *General settings* and expand *Motion Graphics Configuration*
6. Toggle the switch to the ON position
7. In the Motion Graphics Insertion dropdown, select *ENABLED*
8. In the Motion Graphics Settings dropdown, select *HTML motion graphics*
9. Select *Update channel*

### Deployment Instructions - Via the AWS CLI

If you don't have the AWS CLI, there are instructions on how to get it from [here](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)

#### Amazon S3
1. Create new bucket
```
$ aws s3api create-bucket --bucket cunsco-bucket2 --region us-west-2 --create-bucket-configuration LocationConstraint=us-west-2
```

*A successful response should look like this:*
``` 
{
"Location": "http://cunsco-bucket2.s3.amazonaws.com/" (http://cunsco-bucket2.s3.amazonaws.com/)
}
```

*Take note of the URL as access to objects will be from this location*

2. Copy HTML files to S3 bucket

*First, download the files in the html_pages/ folder of this repo, then perform the S3 copy commands:*

``` 
$ aws s3 cp html5_page.html s3://cunsco-bucket2/medialive-html5/html5_page.html --acl public-read
$ aws s3 cp html5_functions.js s3://cunsco-bucket2/medialive-html5/html5_functions.js --acl public-read
$ aws s3 cp html5_style.css s3://cunsco-bucket2/medialive-html5/html5_style.css --acl public-read
$ aws s3 cp data.json s3://cunsco-bucket2/medialive-html5/data.json --acl public-read
```

*check S3 bucket to confirm files are present:*

``` 
$ aws s3 ls cunsco-bucket1/medialive-html5/
2021-06-28 20:29:18        371 data.json
2021-06-28 20:29:02       4231 html5_functions.js
2021-06-28 20:28:46        445 html5_page.html
2021-06-28 20:29:11       2412 html5_style.css
```

3. Test you can view the HTML page

*open your browser and try and access the html page (use the S3 create bucket response along with the path in your s3 copy to create the URL:*

``` 
http://cunsco-bucket2.s3.amazonaws.com/medialive-html5/html5_page.html
```

*The HTML page should load with some sample data and a ticker message.*

#### AWS IAM
1. Create policy

*Replace the resource value `"Resource": "arn:aws:s3:::cunsco-bucket2/medialive-html5/*"`  from the below example to match your bucket and path to HTML files*

``` 
$ aws iam create-policy --policy-name scott-test-cli --policy-document '{     "Version": "2012-10-17",     "Statement": [         {             "Sid": "VisualEditor0",             "Effect": "Allow",             "Action": [                 "s3:ListStorageLensConfigurations",                 "s3:ListAccessPointsForObjectLambda",                 "s3:GetAccessPoint",                 "s3:PutAccountPublicAccessBlock",                 "s3:GetAccountPublicAccessBlock",                 "s3:ListAllMyBuckets",                 "s3:ListAccessPoints",                 "s3:ListJobs",                 "s3:PutStorageLensConfiguration",                 "s3:CreateJob"             ],             "Resource": "*"         },         {             "Sid": "VisualEditor1",             "Effect": "Allow",             "Action": "s3:*",             "Resource": "arn:aws:s3:::cunsco-bucket2/medialive-html5/*"         }     ] }'
```

*Take note of the policy arn in the response:*

``` 
"Arn": "arn:aws:iam::003315040000:policy/scott-test-cli-2"
```

2. Create role

*Replace the role-name `scott-test-role` with your own role name, ie. AWSLambdaAccessToS3HTML*

``` 
$ aws iam create-role --role-name scott-test-role --description "this is the role description" --assume-role-policy-document '{   "Version": "2012-10-17",   "Statement": [     {       "Effect": "Allow",       "Principal": {         "Service": "lambda.amazonaws.com"       },       "Action": "sts:AssumeRole"     }   ] }'
```

*Take note of role arn in the response (this is required for Lambda):*

``` 
 "Arn": "arn:aws:iam::003315040000:role/scott-test-role"
```

3. Attach policy to role (using the role name you stated above)

``` 
$ aws iam attach-role-policy --role-name scott-test-role --policy-arn arn:aws:iam::003315040000:policy/scott-test-cli-2
```

#### AWS Lambda

1. Create Function

*You need to have the following data to build the command:*
* *Bucket*
* *Path to template data.json key*
* *Lambda function zip file location (on local device)*
* *IAM Role ARN for Lambda to assume*

*Replace the data in the below command with yours, ie. bucket, path, Lambda zip location, IAM role arn...*

``` 
$ aws lambda create-function --function-name medialive_html5_api_handler --runtime python3.8 --timeout 5 --handler lambda_function.lambda_handler --environment "Variables={BUCKET=cunsco-bucket2,DATA_KEY=medialive-html5/data.json}" --zip-file fileb://~/Downloads/medialive_html5_api_handler.zip --role arn:aws:iam::001122330000:role/AWSLambdaAccessToS3HTML
```

*Take note of the function Name and ARN in the response*

``` 
"FunctionName": "medialive_html5_api_handler_2",
"FunctionArn": "arn:aws:lambda:us-west-2:003315040000:function:medialive_html5_api_handler_2"
```

#### API Gateway

1. Create a new REST API gateway endpoint

``` 
$ aws apigateway create-rest-api --name "html5_data_ingest"  --endpoint-configuration "types=REGIONAL"
```

*Take note of the name and ID in the response.*

``` 
    "id": "ohirdx9q0j",
    "name": "html5_data_ingest",
```

2. Create an API resource

*Get parent ID for root resource first...*

``` 
$ aws apigateway get-resources --rest-api-id ogh3anadh7 | jq .items[0].id
```

*note the id from the first item (there should only be one item in the list anyway)*

*Create proxy+ resource using rest-api-id, and parent-id:*

``` 
$ aws apigateway create-resource --rest-api-id ohirdx9q0j --path-part "{proxy+}" --parent-id t6jm0g3bid
```

*Take note of the response:*

``` 
{
    "id": "bxsf2b",
    "parentId": "t6jm0g3bid",
    "pathPart": "{proxy+}",
    "path": "/{proxy+}"
}
```

3. Create method for resource

*Create the method for any HTTP request type:*

``` 
$ aws apigateway put-method --rest-api-id ohirdx9q0j --resource-id bxsf2b --http-method ANY --authorization-type NONE
```

4. Create AWS_Proxy (Lambda) integration

*Create integration, replace the rest-api-id, resource-id, and the Lambda ARN portion of the uri:*

``` 
$ aws apigateway put-integration --rest-api-id ohirdx9q0j --resource-id bxsf2b --http-method ANY --type AWS_PROXY --integration-http-method ANY --uri 'arn:aws:apigateway:us-west-2:lambda:path//2015-03-31/functions/arn:aws:lambda:us-west-2:003315049522:function:medialive_html5_api_handler/invocations'

response: 

{
    "type": "AWS",
    "httpMethod": "ANY",
    "uri": "arn:aws:apigateway:us-west-2:lambda:path//2015-03-31/functions/arn:aws:lambda:us-west-2:003315049522:function:medialive_html5_api_handler/invocations",
    "passthroughBehavior": "WHEN_NO_MATCH",
    "timeoutInMillis": 29000,
    "cacheNamespace": "bxsf2b",
    "cacheKeyParameters": []
}
```

*Grant API Gateway permission to invoke Lambda, replace the account number and rest-api-id from below to match yours, also make sure the function-name matches your Lambda function name*

``` 
$ aws lambda add-permission --source-arn "arn:aws:execute-api:us-west-2:003315049522:ohirdx9q0j/*/ANY/*" --principal apigateway.amazonaws.com --statement-id "1" --function-name "medialive_html5_api_handler" --action lambda:InvokeFunction
```

4. Create Deployment

*Create a deployment, that will also create a stage with it:*

``` 
$ aws apigateway create-deployment --rest-api-id ohirdx9q0j --stage-name v1

response:

{
    "id": "zz8qal",
    "createdDate": "2021-06-30T15:54:35-06:00"
}
```

5. Retrieve your API Gateway Invoke URL

*You cannot obtain your API Gateway Invoke URL via a command. The API Gateway Invoke URL is in the below format, you just need to replace the rest-api-id, region, and stage-name with your values:*

``` 
https://{rest-api-id}.execute-api.{region}.amazonaws.com/{stage-name}/
```

*An API call would look something like this (sample values):*

``` 
https://j39jdg9f23.execute-api.us-west-2.amazonaws.com/v1/newdata
```

## Testing the System
### POSTING new data through API

You can manually test the API functionality using a program such as [Postman](https://www.postman.com/). Take the invoke URL you noted down after creating the API Gateway, replace the `{proxy+}` placeholder with `newdata`

Create a new API request with method POST:


**URL**

https://12345abcde.execute-api.us-west-2.amazonaws.com/v1/newdata

**Body**
``` 
{
   "metrics":{
    "key_metric_1": "91.1",
    "key_metric_2": "2420.8813",
  },
  "ticker":{
    "message":"Hello from your friends at AWS",
    "speed":5
  },
   "expires":600
}
```

### About the JSON format...

The 3 main json keys are:

``` 
{
  "metrics":...,
  "ticker":...,
  "expires":...
}
```

They are optional. You can mix and match which ones you use when you submit your metrics and data. If you emit the “expires” key, then the default behavior is to leave the data rendered on the screen until further notice.

After you post the data, you should get a HTTP200 response and the following response payload:

``` 
{
    "status": "Successfully Created Item in Database"
}
```

The new data should be posted to the data.json html page instantly, and you should see the results rendered over your MediaLive channel shortly after. Please note that some of the latency you experience may be inherent from the streaming method you’re using. Typical HLS latency is between 15-30 seconds

Your metric data will appear in a table that is built dynamically based on the number of key-value pairs sent in the API call. The ticker message is displayed at the bottom of the pages, and supports 5 speeds (1-5)

![](images/medialive-sample.png?width=60pc&classes=border,shadow)

### Using the MediaLive Scheduling feature to trigger the overlay

Follow the instructions in [this blog post](https://aws.amazon.com/blogs/media/awse-enhance-live-stream-html5-motion-graphics/), which outlines how to use MediaLive scheduling functionality to enable/disable the motion graphics overlay

## Securing the Deployment

At AWS, security is job 1. In this section, we outline how to further secure the deployment above to ensure the greatest level of protection against external threats.

### IAM 

You can further restrict the functions that AWS Lambda is able to perform on your behalf. Right now, our setup allows the function full access to the path we’ve defined.

Useful Resources:

* AWS Policy Generator : https://awspolicygen.s3.amazonaws.com/policygen.html
* Amazon S3 sample policies : https://docs.aws.amazon.com/AmazonS3/latest/userguide/example-policies-s3.html

### Amazon CloudFront

You can deploy an Amazon CloudFront distribution to prevent the need for your S3 bucket to be accessed publicly.

Useful Resources:

* Protecting your S3 bucket : https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html
* Blog post with instructions on configuration : https://aws.amazon.com/premiumsupport/knowledge-center/cloudfront-access-to-amazon-s3/

### AWS WAF

You can apply firewall rules to your API Gateway and/or CloudFront distribution, to further restrict access to your system

Useful Resources:

* Protect your API Gateway : https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-aws-waf.html
* Protect your CloudFront distribution : https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-awswaf.html

### Amazon API Gateway

Right now, the Amazon API Gateway endpoint is publicly accessible.However, you can create private endpoints that are only accessible via your Amazon VPC network. If you have a VPN or Direct Connect to Amazon VPC, then this option is the most secure.

Useful Resources :

* Creating a private API endpoint : https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-private-apis.html