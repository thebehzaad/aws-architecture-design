from aws_cdk import (
    aws_cognito as cognito,
    Stack,
    core
)
from constructs import Construct

class CognitoUserPoolStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Cognito User Pool
        self.user_pool = cognito.UserPool(self, "CognitoUserPool",
            user_pool_name="CognitoPool"
        )

        # Cognito User Pool Client
        self.user_pool_client = cognito.UserPoolClient(self, "CognitoUserPoolClient",
            user_pool=self.user_pool,
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
        self.user_pool_domain = cognito.UserPoolDomain(self, "CognitoUserPoolDomain",
            user_pool=self.user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"dns-name-{self.user_pool_client.user_pool_client_id}"
            )
        )

        # Cognito User Pool Group
        self.user_pool_group = cognito.CfnUserPoolGroup(self, "CognitoUserPoolGroup",
            group_name="pet-veterinarian",
            user_pool_id=self.user_pool.user_pool_id
        )