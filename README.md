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
    1. html5_functions.js [link]
    2. html5_page.html [link]
    3. html5_style.css [link]
    4. data.json [link]
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


