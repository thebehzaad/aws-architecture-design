from aws_cdk import (
    aws_iam as iam,
    aws_lambda as _lambda,
    Stack,
    core
)
from constructs import Construct

class LambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, user_pool_arn: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # IAM Role for Helper Lambda
        helper_lambda_role = iam.Role(self, "HelperLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "HelperLambdaPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["cognito-idp:AdminCreateUser", "cognito-idp:AdminSetUserPassword"],
                            resources=[user_pool_arn]
                        ),
                        iam.PolicyStatement(
                            actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                            resources=[f"arn:aws:logs:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:log-group:/aws/lambda/HelperInitCognitoFunction:*"]
                        )
                    ]
                )
            }
        )

        # Helper Lambda Function
        self.helper_lambda = _lambda.Function(self, "HelperInitCognitoFunction",
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

        # IAM Role for API Service Lambda
        api_service_iam_role = iam.Role(self, "ApiServiceIAMRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "ApiServiceIAMPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["cognito-idp:Admin*"],
                            resources=[user_pool_arn]
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
        self.api_service_lambda = _lambda.Function(self, "ApiServiceLambdaFunction",
            function_name="ApiServiceLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda.handler",
            role=api_service_iam_role,
            code=_lambda.Code.from_bucket(
                bucket_name=f"{core.Aws.STACK_NAME}-{core.Aws.ACCOUNT_ID}-{core.Aws.REGION}-lambdas",
                key="pets-api.zip"
            )
        )

        # IAM Role for Helper DynamoDB Lambda
        helper_dynamo_db_lambda_role = iam.Role(self, "HelperDynamoDbLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "HelperDynamoDbLambdaPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["dynamodb:PutItem"],
                            resources=[f"arn:aws:dynamodb:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:table/auth-policy-store"]
                        ),
                        iam.PolicyStatement(
                            actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                            resources=[f"arn:aws:logs:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:log-group:/aws/lambda/HelperDynamoDbInitFunction:*"]
                        )
                    ]
                )
            }
        )

        # Helper DynamoDB Lambda Function
        self.helper_dynamo_db_lambda = _lambda.Function(self, "HelperDynamoDbInitFunction",
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