# HTML5 Graphics With AWSS Elemental MediaLive
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