import pulumi
import pulumi_aws as aws
from networking import get_default_vpc_and_subnets, create_redshift_security_group
from iam import create_redshift_iam_role

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
    # 1. ネットワーク設定 (共通モジュールを利用)
    # ==============================================================================
    default_vpc, default_subnets = get_default_vpc_and_subnets()
    redshift_sg = create_redshift_security_group("redshift-sg", default_vpc.id)

    # サブネットグループの作成（Redshiftを配置するサブネット群）
    subnet_group = aws.redshift.SubnetGroup("redshift-subnet-group",
        subnet_ids=default_subnets.ids,
        description="Default subnet group for Redshift"
    )

    # ==============================================================================
    # 2. IAMロールの設定 (共通モジュールを利用)
    # ==============================================================================
    redshift_role, role_attachment = create_redshift_iam_role("redshift-role")

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

    # ==============================================================================
    # 4. 戻り値
    # ==============================================================================
    return {
        "cluster_endpoint": cluster.endpoint,
        "database_name": cluster.database_name,
        "username": cluster.master_username
    }
