from aws_cdk import (
    aws_apigateway,
    aws_lambda,
    Stack,
    core
)
from constructs import Construct

class CognitoProtectedApiGatewayStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, api_service_lambda: aws_lambda.IFunction, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # API Gateway Rest API
        self.api_gateway_rest_api = aws_apigateway.RestApi(self, "ApiGatewayRestApi",
            rest_api_name="MyApiGateway"
        )

        # API Gateway Resource
        self.api_gateway_resource = self.api_gateway_rest_api.root.add_resource("{api+}")

        # API Gateway Method
        self.api_gateway_method = self.api_gateway_resource.add_method("ANY",
            aws_apigateway.LambdaIntegration(api_service_lambda),
            authorization_type=aws_apigateway.AuthorizationType.CUSTOM,
            authorizer=aws_apigateway.RequestAuthorizer(self, "ApiGatewayAuthorizer",
                handler=aws_lambda.Function.from_function_arn(self, "CustomAuthLambdaFunction", function_arn="arn:aws:lambda:region:account-id:function:CustomAuthLambdaFunction"),
                identity_sources=[aws_apigateway.IdentitySource.header("Authorization")]
            )
        )

        # API Gateway Deployment
        self.api_gateway_deployment = aws_apigateway.Deployment(self, "ApiGatewayDeploymentProtected",
            api=self.api_gateway_rest_api,
            description="protected api",
            stage_name="dev"
        )


