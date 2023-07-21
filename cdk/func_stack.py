from constructs import Construct
from os import environ
from aws_cdk import (
    Stack,
    aws_lambda,
    aws_logs as logs,
    Duration,
    aws_iam as iam,
    aws_s3 as s3,
    aws_cloudfront as cf,
    aws_events as events,
    aws_events_targets as targets
)


class FuncStack(Stack):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            bucket: s3.Bucket,
            distribution: cf.Distribution,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        print(environ['PROJECT_NAME'])

        function_id: str = f"{environ['PROJECT_NAME']}-lambda"
        rule_id: str = f"{environ['PROJECT_NAME']}-lambda-trigger-rule"

        self.lambda_function = aws_lambda.DockerImageFunction(
            scope=self,
            id=function_id,
            code=aws_lambda.DockerImageCode.from_image_asset("calendar_sync"),
            function_name=function_id,
            log_retention=logs.RetentionDays.ONE_MONTH,
            timeout=Duration.seconds(10),
            initial_policy=[
                iam.PolicyStatement(
                    actions=[
                        "s3:PutObject",
                        "s3:GetObject",
                        "s3:ListBucket",
                        "s3:DeleteObject",
                        "cloudfront:GetInvalidation",
                        "cloudfront:UpdateDistribution",
                        "cloudfront:CreateInvalidation",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f"arn:aws:s3:::{bucket.bucket_name}",
                        f"arn:aws:s3:::{bucket.bucket_name}/*",
                        f"arn:aws:cloudfront::{kwargs.get('env').account}:distribution/{distribution.distribution_id}"
                    ]
                )
            ],
            environment={
                "CALENDAR_LINK": environ["CALENDAR_LINK"],
                "DISTRIBUTION_ID": distribution.distribution_id,
                "BUCKET_NAME": bucket.bucket_name,
                "EVENTS_PER_PAGE": environ["EVENTS_PER_PAGE"],
                "TZ": environ["TZ"]
            }
        )

        self.rule = events.Rule(
            scope=self,
            id=rule_id,
            rule_name=rule_id,
            schedule=events.Schedule.cron(
                hour="0",
                minute="0"
            ),
            targets=[targets.LambdaFunction(handler=self.lambda_function)]
        )
