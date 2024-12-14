from aws_cdk import (
    aws_dynamodb as dynamodb,
    Stack,
    core
)
from constructs import Construct

class DynamoDbStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Table
        self.dynamo_db_table = dynamodb.Table(self, "DynamoDBTable",
            table_name="auth-policy-store",
            partition_key=dynamodb.Attribute(name="group", type=dynamodb.AttributeType.STRING),
            provisioned_throughput=dynamodb.ProvisionedThroughput(read_capacity_units=5, write_capacity_units=5)
        )