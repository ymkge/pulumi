import json
import pulumi_aws as aws

def create_redshift_iam_role(name: str):
    """
    Redshiftサービス用のIAMロールを作成し、S3読み取り権限を付与します。
    """
    role = aws.iam.Role(name,
        assume_role_policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "sts:AssumeRole",
                "Effect": "Allow",
                "Principal": {
                    "Service": "redshift.amazonaws.com"
                }
            }]
        })
    )

    policy_attachment = aws.iam.RolePolicyAttachment(f"{name}-s3-read",
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
    )

    return role, policy_attachment
