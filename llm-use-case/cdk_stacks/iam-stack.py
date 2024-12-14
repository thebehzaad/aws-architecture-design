from aws_cdk import (
    aws_iam as iam,
    Stack,
    core
)
from constructs import Construct

class IamStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, user_pool_arn: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # IAM Role for Helper Lambda
        self.helper_lambda_role = iam.Role(self, "HelperLambdaRole",
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

        # IAM Role for API Service Lambda
        self.api_service_iam_role = iam.Role(self, "ApiServiceIAMRole",
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

        # IAM Role for Helper DynamoDB Lambda
        self.helper_dynamo_db_lambda_role = iam.Role(self, "HelperDynamoDbLambdaRole",
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