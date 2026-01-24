import pulumi
from pulumi_azure_native import resources, storage, synapse
import pulumi_random as random

def deploy_synapse():
    # リソースグループの作成
    resource_group = resources.ResourceGroup("synapse-rg")

    # Data Lake Storage Gen2 用のストレージアカウント作成
    # Synapse Workspace には HNS (Hierarchical Namespace) が有効なストレージが必要
    storage_account = storage.StorageAccount("datalake",
        resource_group_name=resource_group.name,
        sku=storage.SkuArgs(
            name=storage.SkuName.STANDARD_LRS,
        ),
        kind=storage.Kind.STORAGE_V2,
        is_hns_enabled=True, # Hierarchical Namespace を有効化
        allow_blob_public_access=False
    )

    # ファイルシステム (Container) の作成
    # Synapse Workspace のデフォルトファイルシステムとして使用
    filesystem = storage.BlobContainer("filesystem",
        resource_group_name=resource_group.name,
        account_name=storage_account.name,
        container_name="users"
    )

    # SQL管理者パスワードの生成
    sql_admin_password = random.RandomPassword("sqlAdminPassword",
        length=16,
        special=True,
        min_upper=1,
        min_lower=1,
        min_numeric=1
    )

    # Configの取得
    config = pulumi.Config()
    sql_admin_login = config.get("sqlAdmin") or "sqladminuser"

    # Synapse Workspace の作成
    workspace = synapse.Workspace("synapseWorkspace",
        resource_group_name=resource_group.name,
        default_data_lake_storage=synapse.DataLakeStorageAccountDetailsArgs(
            account_url=storage_account.primary_endpoints.dfs,
            filesystem="users",
        ),
        sql_administrator_login=sql_admin_login,
        sql_administrator_login_password=sql_admin_password.result,
        identity=synapse.ManagedIdentityArgs(
            type="SystemAssigned",
        ),
        managed_resource_group_name=resource_group.name.apply(lambda name: f"{name}-synapse-managed"),
        location=resource_group.location
    )

    # 開発用のFirewallルール (Configで指定された範囲のみ許可)
    # 設定がない場合はルールを作成しない（アクセス不可）
    allowed_ip_start = config.get("allowedIpStart")
    allowed_ip_end = config.get("allowedIpEnd")

    if allowed_ip_start and allowed_ip_end:
        firewall_rule = synapse.IpFirewallRule("allowSpecificRange",
            resource_group_name=resource_group.name,
            workspace_name=workspace.name,
            start_ip_address=allowed_ip_start,
            end_ip_address=allowed_ip_end
        )

    # 専用SQLプール (Dedicated SQL Pool) の作成 (オプション)
    sql_pool = synapse.SqlPool("sqlPool",
        resource_group_name=resource_group.name,
        workspace_name=workspace.name,
        sku=synapse.SkuArgs(
            name="DW100c", # 最小構成
            tier="DataWarehouse"
        ),
        location=resource_group.location
    )

    # Sparkプール (Apache Spark Pool) の作成 (オプション)
    spark_pool = synapse.BigDataPool("sparkPool",
        resource_group_name=resource_group.name,
        workspace_name=workspace.name,
        node_size="Small",
        node_count=3,
        node_size_family="MemoryOptimized",
        auto_scale=synapse.AutoScalePropertiesArgs(
            enabled=True,
            min_node_count=3,
            max_node_count=3
        ),
        auto_pause=synapse.AutoPausePropertiesArgs(
            enabled=True,
            delay_in_minutes=15
        ),
        spark_version="3.4",
        location=resource_group.location
    )

    # 出力
    pulumi.export("resource_group_name", resource_group.name)
    pulumi.export("storage_account_name", storage_account.name)
    pulumi.export("synapse_workspace_name", workspace.name)
    pulumi.export("synapse_workspace_url", workspace.connectivity_endpoints)
    pulumi.export("sql_admin_user", "sqladminuser")
    pulumi.export("sql_admin_password", sql_admin_password.result)
    pulumi.export("sql_pool_name", sql_pool.name)
    pulumi.export("spark_pool_name", spark_pool.name)
