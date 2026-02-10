import pulumi
import pulumi_aws as aws
from networking import get_default_vpc_and_subnets, create_redshift_security_group
from iam import create_redshift_iam_role

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
    # 1. ネットワーク設定 (共通モジュールを利用)
    # ==============================================================================
    default_vpc, default_subnets = get_default_vpc_and_subnets()
    serverless_sg = create_redshift_security_group("redshift-serverless-sg", default_vpc.id)

    # ==============================================================================
    # 2. IAMロールの設定 (共通モジュールを利用)
    # ==============================================================================
    redshift_role, role_attachment = create_redshift_iam_role("redshift-serverless-role")

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
        opts=pulumi.ResourceOptions(depends_on=[namespace, role_attachment])
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

    # ==============================================================================
    # 4. 戻り値
    # ==============================================================================
    return {
        "workgroup_endpoint": workgroup.endpoint,
        "namespace_name": namespace.namespace_name,
        "database_name": namespace.db_name,
        "username": ADMIN_USERNAME
    }
