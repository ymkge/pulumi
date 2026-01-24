import json
import pulumi
import pulumi_aws as aws

def create_data_warehouse():
    """
    AWS Redshiftクラスターと、それに必要なIAMロール、セキュリティグループなどを構築します。
    """

    # ==============================================================================
    # 設定値 (Configuration)
    # ==============================================================================
    config = pulumi.Config()
    
    CLUSTER_IDENTIFIER = "my-redshift-cluster"
    DB_NAME = "analytics_db"
    USERNAME = "admin_user"
    PASSWORD = config.require_secret("dbPassword")
    NODE_TYPE = "dc2.large"           # 開発用には安価な dc2.large を推奨
    CLUSTER_TYPE = "single-node"      # 本番は multi-node 推奨

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
                description="Redshift Ingress from Config"
            )
        )

    # Redshift用のセキュリティグループ作成
    redshift_sg = aws.ec2.SecurityGroup("redshift-sg",
        description="Allow Redshift access",
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

    # サブネットグループの作成（Redshiftを配置するサブネット群）
    subnet_group = aws.redshift.SubnetGroup("redshift-subnet-group",
        subnet_ids=default_subnets.ids,
        description="Default subnet group for Redshift"
    )

    # ==============================================================================
    # 2. IAMロールの設定
    # ==============================================================================
    # Redshiftが他のAWSサービス（S3など）にアクセスするためのロール
    redshift_role = aws.iam.Role("redshift-role",
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

    # 例: S3読み取り権限を付与（S3からCOPYコマンドでロードする場合などに必要）
    role_attachment = aws.iam.RolePolicyAttachment("redshift-s3-read-only",
        role=redshift_role.name,
        policy_arn="arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
    )

    # ==============================================================================
    # 3. Redshift クラスターの作成
    # ==============================================================================
    cluster = aws.redshift.Cluster("my-cluster",
        cluster_identifier=CLUSTER_IDENTIFIER,
        database_name=DB_NAME,
        master_username=USERNAME,
        master_password=PASSWORD,
        node_type=NODE_TYPE,
        cluster_type=CLUSTER_TYPE,
        
        # ネットワーク設定
        cluster_subnet_group_name=subnet_group.name,
        vpc_security_group_ids=[redshift_sg.id],
        
        # IAM設定
        iam_roles=[redshift_role.arn],
        
        # 可用性・公開設定
        publicly_accessible=True, # 外部からアクセス可能にする（開発用）
        skip_final_snapshot=True, # 削除時にスナップショットを取らない（開発用）
        
        opts=pulumi.ResourceOptions(depends_on=[role_attachment])
    )

    # ==============================================================================
    # 4. 戻り値
    # ==============================================================================
    return {
        "cluster_endpoint": cluster.endpoint,
        "database_name": cluster.database_name,
        "username": cluster.master_username
    }
