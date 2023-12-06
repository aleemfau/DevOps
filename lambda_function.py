import json
import boto3
import logging
import signal
import datetime
import json
import urllib3
import base64
import boto3

# Initialize SNS client
client = boto3.client('sns')

def saveLogs(orgs_endpoint, status, method):
    # Timestream configuration
    region_name = "us-east-1"
    database_name = "sampleDB"
    table_name = "requests"

    # AWS credentials for Timestream
    aws_access_key = "AKIA6KJUA44RCYBXDN74"
    aws_secret_key = "S8nWVwke0gDJUZNczmT/YufarvMa4pFccnKm25sh"
    aws_session_token = ""  # Not using Session tokens

    # Configure AWS credentials
    aws_credentials = {
        "aws_access_key_id": aws_access_key,
        "aws_secret_access_key": aws_secret_key,
        "aws_session_token": aws_session_token
    }

    # Create Timestream client
    timestream_client = boto3.client('timestream-write', region_name=region_name, **aws_credentials)
    timestamp = int(datetime.datetime.utcnow().timestamp() * 1000)

    # Example: Timestream table has columns 'timestamp', 'url', 'method', 'status_code'
    records = [
        {
            'Dimensions': [
                {'Name': 'url', 'Value': orgs_endpoint},
                {'Name': 'method', 'Value': method},
                # Add more dimensions as needed
            ],
            'MeasureName': 'status_code',
            'MeasureValue': str(status),
            'Time': str(timestamp)
        }
    ]

    # Write the records to Timestream
    try:
        timestream_client.write_records(DatabaseName=database_name, TableName=table_name, Records=records)
        print("Request logged successfully.")
    except Exception as e:
        print(f"Error logging request: {e}")

def adduser(grafana_api_url, email):
    # Grafana API endpoint to add a user
    orgs_endpoint = f"{grafana_api_url}/api/admin/users"
    api_keys = "eyJrIjoid3g1dTZ4ZDE4WDlxdVc4N1lPbGpwRFRaeVpIOXBWUlciLCJuIjoiaGkiLCJpZCI6MX0="
    password = "admin"
    username = "admin"
    
    # User data to be added
    org_data = json.dumps({
        "name": "user",
        "password": "userpassword",
        "email": email
    })
    
    # Basic authentication credentials
    credentials = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')
    headers = {"Authorization": f"Basic {credentials}", 'Accept': 'application/json', 'Content-Type': 'application/json'}
    
    # HTTP request to add user
    http = urllib3.PoolManager()
    r = http.request('POST', orgs_endpoint, headers=headers, body=org_data)
    
    # Log the request details to Timestream
    saveLogs(orgs_endpoint, r.status, "POST")
    return r

def handler():
    # SNS handler function to publish an error message
    response = client.publish(TopicArn='arn:aws:sns:us-east-1:984193492770:ERR_TOPIC',
                              Message="Error code:408\n error message:timedout}")

def lambda_handler(event, context):
    try:
        grafana_api_url = "http://54.198.25.107:3000"
        org_name_to_check = "Main rg."
        r = check_organization_exists(grafana_api_url, org_name_to_check)

       
       
       
       
        # Uncomment the following lines to check user existence and add if not found
        # email = "alleeem@gmail.co"
        # r = checkuser(grafana_api_url, email)





        timeout_duration = 3
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout_duration)
        
        # If status code is not 200, publish error message to SNS
        if r.status != 200:
            response = client.publish(TopicArn='arn:aws:sns:us-east-1:984193492770:ERR_TOPIC',
                                      Message=f"Error code:{r.status}\n error message:{r.data.decode('utf-8')}")
        return {'statusCode': r.status, 'body': r.data.decode('utf-8')}
    except TimeoutError as e:
        print(f"Timeout: {e}")
    finally:
        signal.alarm(0)

def checkuser(grafana_api_url, email):
    # Grafana API endpoint to check user existence
    orgs_endpoint = f"{grafana_api_url}/api/users/lookup?loginOrEmail={email}"
    api_keys = "eyJrIjoid3g1dTZ4ZDE4WDlxdVc4N1lPbGpwRFRaeVpIOXBWUlciLCJuIjoiaGkiLCJpZCI6MX0="
    username = "admin"
    password = "admin"
    
    # Basic authentication credentials
    credentials = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')
    headers = {"Authorization": f"Basic {credentials}", 'Accept': 'application/json'}
    
    # HTTP request to check user
    http = urllib3.PoolManager()
    r = http.request('GET', orgs_endpoint, headers=headers)
    
    # Log the request details to Timestream
    saveLogs(orgs_endpoint, r.status, "GET")
    
    # If user not found (status code 404), add the user
    if r.status == 404:
        adduser(grafana_api_url, email)
    return r

def check_organization_exists(grafana_api_url, org_check):
    # Grafana API endpoint to check organization existence
    orgs_endpoint = f"{grafana_api_url}/api/orgs/name/{org_check}"
    api_keys = "eyJrIjoid3g1dTZ4ZDE4WDlxdVc4N1lPbGpwRFRaeVpIOXBWUlciLCJuIjoiaGkiLCJpZCI6MX0="
    username = "admin"
    password = "admin"
    
    # Basic authentication credentials
    credentials = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')
    headers = {"Authorization": f"Basic {credentials}", 'Accept': 'application/json'}
    
    # HTTP request to check organization
    http = urllib3.PoolManager()
    r = http.request('GET', orgs_endpoint, headers=headers)
    
    # Log the request details to Timestream
    saveLogs(orgs_endpoint, r.status, "GET")
    return r
