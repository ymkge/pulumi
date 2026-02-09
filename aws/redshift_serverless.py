import json
import pulumi
import pulumi_aws as aws

def create_redshift_serverless():
    """
    AWS Redshift Serverless (Namespace & Workgroup) を構築します。
    """

    # ==============================================================================
    # 設定値 (Configuration)
    # ==============================================================================
    config = pulumi.Config()
    
    NAMESPACE_NAME = "my-redshift-namespace"
    WORKGROUP_NAME = "my-redshift-workgroup"
    DB_NAME = "analytics_db"
    ADMIN_USERNAME = "admin_user"
    ADMIN_PASSWORD = config.require_secret("dbPassword")
    BASE_CAPACITY = 32  # RPU (Redshift Processing Units): 8-512の範囲で指定可能

    # ==============================================================================
    # 1. ネットワーク設定 (Default VPCを利用)
    # ==============================================================================
    # デフォルトVPCとサブネットを取得
    default_vpc = aws.ec2.get_vpc(default=True)
    default_subnets = aws.ec2.get_subnets(filters=[
        aws.ec2.GetSubnetsFilterArgs(name="vpc-id", values=[default_vpc.id])
    ])

    # Ingressルールの作成（ConfigでCIDRが指定されている場合のみ許可）
    ingress_rules = []
    allowed_cidr = config.get("allowedCidr")
    if allowed_cidr:
        ingress_rules.append(
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=5439,
                to_port=5439,
                cidr_blocks=[allowed_cidr],
                description="Redshift Serverless Ingress"
            )
        )

    # Redshift Serverless用のセキュリティグループ作成
    serverless_sg = aws.ec2.SecurityGroup("redshift-serverless-sg",
        description="Allow Redshift Serverless access",
        vpc_id=default_vpc.id,
        ingress=ingress_rules,
        egress=[
            # アウトバウンドは全許可
            aws.ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"]
            )
        ]
    )

    # ==============================================================================
    # 2. IAMロールの設定
    # ==============================================================================
    # Redshiftが他のAWSサービス（S3など）にアクセスするためのロール
    redshift_role = aws.iam.Role("redshift-serverless-role",
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

    # S3読み取り権限を付与
    aws.iam.RolePolicyAttachment("redshift-serverless-s3-read",
        role=redshift_role.name,
        policy_arn="arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
    )

    # ==============================================================================
    # 3. Redshift Serverless の作成
    # ==============================================================================
    
    # Namespace: データベース本体、ユーザー、認証情報の管理
    namespace = aws.redshiftserverless.Namespace("my-namespace",
        namespace_name=NAMESPACE_NAME,
        db_name=DB_NAME,
        admin_username=ADMIN_USERNAME,
        admin_user_password=ADMIN_PASSWORD,
        iam_roles=[redshift_role.arn]
    )

    # Workgroup: 計算リソース (RPU)、ネットワーク、エンドポイントの管理
    workgroup = aws.redshiftserverless.Workgroup("my-workgroup",
        workgroup_name=WORKGROUP_NAME,
        namespace_name=namespace.namespace_name,
        base_capacity=BASE_CAPACITY,
        security_group_ids=[serverless_sg.id],
        subnet_ids=default_subnets.ids,
        publicly_accessible=True, # 外部からアクセス可能にする（開発用）
        opts=pulumi.ResourceOptions(depends_on=[namespace])
    )

    # ==============================================================================
    # 4. 戻り値
    # ==============================================================================
    return {
        "workgroup_endpoint": workgroup.endpoint,
        "namespace_name": namespace.namespace_name,
        "database_name": namespace.db_name,
        "username": ADMIN_USERNAME
    }
