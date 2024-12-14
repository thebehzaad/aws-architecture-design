from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct

class LlmUseCaseStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "LlmUseCaseQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )





from aws_cdk import (
  aws_cognito as cognito,
  aws_iam as iam,
  aws_lambda as _lambda,
  aws_apigateway as apigateway,
  aws_dynamodb as dynamodb,
  core
)

class CognitoApiGatewayStack(core.Stack):

  def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    # Cognito User Pool
    user_pool = cognito.UserPool(self, "CognitoUserPool",
      user_pool_name="CognitoPool"
    )

    # Cognito User Pool Client
    user_pool_client = cognito.UserPoolClient(self, "CognitoUserPoolClient",
      user_pool=user_pool,
      allowed_oauth_flows=["implicit"],
      allowed_oauth_flows_user_pool_client=True,
      allowed_oauth_scopes=["email", "openid"],
      callback_urls=["http://localhost"],
      generate_secret=False,
      explicit_auth_flows=[
        cognito.ExplicitAuthFlows.ALLOW_USER_PASSWORD_AUTH,
        cognito.ExplicitAuthFlows.ALLOW_USER_SRP_AUTH,
        cognito.ExplicitAuthFlows.ALLOW_REFRESH_TOKEN_AUTH
      ],
      supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO]
    )

    # Cognito User Pool Domain
    user_pool_domain = cognito.UserPoolDomain(self, "CognitoUserPoolDomain",
      user_pool=user_pool,
      cognito_domain=cognito.CognitoDomainOptions(
        domain_prefix=f"dns-name-{user_pool_client.user_pool_client_id}"
      )
    )

    # Cognito User Pool Group
    user_pool_group = cognito.CfnUserPoolGroup(self, "CognitoUserPoolGroup",
      group_name="pet-veterinarian",
      user_pool_id=user_pool.user_pool_id
    )

    # IAM Role for Helper Lambda
    helper_lambda_role = iam.Role(self, "HelperCognitoLambdaRole",
      assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
      inline_policies={
        "helperCognitoLambdaRole": iam.PolicyDocument(
          statements=[
            iam.PolicyStatement(
              actions=["cognito-idp:Admin*"],
              resources=[user_pool.user_pool_arn]
            ),
            iam.PolicyStatement(
              actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
              resources=[f"arn:aws:logs:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:log-group:/aws/lambda/{core.Aws.STACK_NAME}-HelperInitCognitoFunction-*:*"]
            )
          ]
        )
      }
    )

    # Helper Lambda Function
    helper_lambda = _lambda.Function(self, "HelperInitCognitoFunction",
      code=_lambda.InlineCode("""
        const AWS = require("aws-sdk");
        const response = require("cfn-response");
        const cognitoidentityserviceprovider = new AWS.CognitoIdentityServiceProvider({apiVersion: '2016-04-18'});

        exports.handler = function (event, context, callback) {
          var userPoolId = event.ResourceProperties.UserPoolId;
          var username = event.ResourceProperties.CognitoUserName;
          var pass = event.ResourceProperties.CognitoUserPassword;

          console.log("username: " + username);

          var params = {
            UserPoolId: userPoolId,
            Username: username,
            TemporaryPassword: pass
          };

          cognitoidentityserviceprovider.adminCreateUser(params, function (err, data) {
            if (err) {
              console.log(err, err.stack);
            } else {
              console.log(data);
            }

            const params = {
              UserPoolId: userPoolId,
              Username: username,
              Password: pass,
              Permanent: true
            };
            cognitoidentityserviceprovider.adminSetUserPassword(params, function (err, data) {
              if (err) {
                response.send(event, context, "FAILED", {});
              } else {
                response.send(event, context, "SUCCESS", {});
              }
            });
          });
        };
      """),
      handler="index.handler",
      runtime=_lambda.Runtime.NODEJS_16_X,
      role=helper_lambda_role,
      timeout=core.Duration.seconds(30)
    )

    # Custom Resource to Initialize Cognito User
    helper_initialize_cognito_user = core.CustomResource(self, "HelperInitializeCognitoUser",
      service_token=helper_lambda.function_arn,
      properties={
        "UserPoolId": user_pool.user_pool_id,
        "CognitoUserName": core.CfnParameter(self, "CognitoUserName", type="String", default="cognitouser").value_as_string,
        "CognitoUserPassword": core.CfnParameter(self, "CognitoUserPassword", type="String", allowed_pattern='^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[\^$*.\[\]{}\(\)?\-“!@#%&/,><\’:;|_~`])\S{6,99}$').value_as_string
      }
    )

    # Cognito User Pool User to Group Attachment
    cognito_user_pool_user_to_group_attachment = cognito.CfnUserPoolUserToGroupAttachment(self, "CognitoUserPoolUserToGroupAttachment",
      group_name=user_pool_group.group_name,
      username=core.CfnParameter(self, "CognitoUserName").value_as_string,
      user_pool_id=user_pool.user_pool_id
    )

    # IAM Role for API Service Lambda
    api_service_iam_role = iam.Role(self, "ApiServiceIAMRole",
      assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
      inline_policies={
        "ApiServiceIAMPolicy": iam.PolicyDocument(
          statements=[
            iam.PolicyStatement(
              actions=["cognito-idp:Admin*"],
              resources=[user_pool.user_pool_arn]
            ),
            iam.PolicyStatement(
              actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
              resources=[f"arn:aws:logs:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:log-group:/aws/lambda/ApiServiceLambdaFunction:*"]
            )
          ]
        )
      }
    )

    # API Service Lambda Function
    api_service_lambda = _lambda.Function(self, "ApiServiceLambdaFunction",
      function_name="ApiServiceLambdaFunction",
      runtime=_lambda.Runtime.PYTHON_3_9,
      handler="lambda.handler",
      role=api_service_iam_role,
      code=_lambda.Code.from_bucket(
        bucket_name=f"{core.Aws.STACK_NAME}-{core.Aws.ACCOUNT_ID}-{core.Aws.REGION}-lambdas",
        key="pets-api.zip"
      )
    )

    # API Gateway Rest API
    api_gateway_rest_api = apigateway.RestApi(self, "ApiGatewayRestApi",
      rest_api_name="MyApiGateway"
    )

    # API Gateway Resource
    api_gateway_resource = api_gateway_rest_api.root.add_resource("{api+}")

    # API Gateway Method
    api_gateway_method = api_gateway_resource.add_method("ANY",
      apigateway.LambdaIntegration(api_service_lambda),
      authorization_type=apigateway.AuthorizationType.CUSTOM,
      authorizer=apigateway.RequestAuthorizer(self, "ApiGatewayAuthorizer",
        handler=_lambda.Function.from_function_arn(self, "CustomAuthLambdaFunction", function_arn="arn:aws:lambda:region:account-id:function:CustomAuthLambdaFunction"),
        identity_sources=[apigateway.IdentitySource.header("Authorization")]
      )
    )

    # API Gateway Deployment
    api_gateway_deployment = apigateway.Deployment(self, "ApiGatewayDeploymentProtected",
      api=api_gateway_rest_api,
      description="protected api",
      stage_name="dev"
    )

    # DynamoDB Table
    dynamo_db_table = dynamodb.Table(self, "DynamoDBTable",
      table_name="auth-policy-store",
      partition_key=dynamodb.Attribute(name="group", type=dynamodb.AttributeType.STRING),
      provisioned_throughput=dynamodb.ProvisionedThroughput(read_capacity_units=5, write_capacity_units=5)
    )

    # IAM Role for Helper DynamoDB Lambda
    helper_dynamo_db_lambda_role = iam.Role(self, "HelperDynamoDbLambdaRole",
      assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
      inline_policies={
        "dynamodbAccessRole": iam.PolicyDocument(
          statements=[
            iam.PolicyStatement(
              actions=["dynamodb:PutItem"],
              resources=[dynamo_db_table.table_arn]
            ),
            iam.PolicyStatement(
              actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
              resources=[f"arn:aws:logs:{core.Aws.REGION}::log-group:/aws/lambda/{core.Aws.STACK_NAME}-*:*"]
            )
          ]
        )
      }
    )

    # Helper DynamoDB Lambda Function
    helper_dynamo_db_lambda = _lambda.Function(self, "HelperDynamoDbInitFunction",
      code=_lambda.InlineCode("""
        const AWS = require("aws-sdk");
        const response = require("cfn-response");
        const docClient = new AWS.DynamoDB.DocumentClient();
        exports.handler = function(event, context) {
          console.log(JSON.stringify(event,null,2));
          var params = {
            TableName: event.ResourceProperties.DynamoTableName,
            Item:{
               "group": "pet-veterinarian",
               "policy": {
                 "Statement": [
                 {
                   "Action": "execute-api:Invoke",
                   "Effect": "Allow",
                   "Resource": [
                   "arn:aws:execute-api:*:*:*/*/*/petstore/v1/*",
                   "arn:aws:execute-api:*:*:*/*/GET/petstore/v2/status"
                   ],
                   "Sid": "PetStore-API"
                 }
                 ],
                 "Version": "2012-10-17"
               }
               }
          };
        docClient.put(params, function(err, data) { if (err) {
          response.send(event, context, "FAILED", {});
        } else {
          response.send(event, context, "SUCCESS", {});
        }
        });
        };
      """),
      handler="index.handler",
      runtime=_lambda.Runtime.NODEJS_16_X,
      role=helper_dynamo_db_lambda_role,
      timeout=core.Duration.seconds(30)
    )

    # Custom Resource to Initialize DynamoDB
    helper_initialize_dynamo_db = core.CustomResource(self, "HelperDynamoDbInitializeDynamoDB",
      service_token=helper_dynamo_db_lambda.function_arn,
      properties={
        "DynamoTableName": dynamo_db_table.table_name
      }
    )

    # Outputs
    core.CfnOutput(self, "CognitoUserPoolClientId",
      value=user_pool_client.user_pool_client_id
    )

    core.CfnOutput(self, "CognitoHostedUiUrl",
      value=f"https://{user_pool_domain.domain_name}.auth.{core.Aws.REGION}.amazoncognito.com/login?client_id={user_pool_client.user_pool_client_id}&response_type=token&scope=email+openid&redirect_uri=http://localhost"
    )

    core.CfnOutput(self, "ApiGatewayDeploymentUrlApiEndpoint",
      value=f"https://{api_gateway_rest_api.rest_api_id}.execute-api.{core.Aws.REGION}.amazonaws.com/dev/petstore/v1/pets"
    )

    core.CfnOutput(self, "ApiGatewayDeploymentUrlApiEndpointV2",
      value=f"https://{api_gateway_rest_api.rest_api_id}.execute-api.{core.Aws.REGION}.amazonaws.com/dev/petstore/v2/pets"
    )

app = core.App()
CognitoApiGatewayStack(app, "CognitoApiGatewayStack")
app.synth()
