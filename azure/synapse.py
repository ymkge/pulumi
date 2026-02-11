import pulumi
from pulumi_azure_native import resources, storage, synapse
import pulumi_random as random

def create_storage_infrastructure(resource_group: resources.ResourceGroup):
    """Data Lake Storage Gen2 とファイルシステムの作成"""
    
    # Synapse Workspace には HNS (Hierarchical Namespace) が有効なストレージが必要
    storage_account = storage.StorageAccount("datalake",
        resource_group_name=resource_group.name,
        sku=storage.SkuArgs(
            name=storage.SkuName.STANDARD_LRS,
        ),
        kind=storage.Kind.STORAGE_V2,
        is_hns_enabled=True,
        allow_blob_public_access=False
    )

    # Synapse Workspace のデフォルトファイルシステムとして使用
    filesystem = storage.BlobContainer("filesystem",
        resource_group_name=resource_group.name,
        account_name=storage_account.name,
        container_name="users"
    )
    
    return storage_account, filesystem

def create_synapse_workspace(
    resource_group: resources.ResourceGroup,
    storage_account: storage.StorageAccount,
    filesystem: storage.BlobContainer,
    admin_login: str,
    admin_password: pulumi.Output[str]
):
    """Synapse Workspace の作成"""
    
    workspace = synapse.Workspace("synapseWorkspace",
        resource_group_name=resource_group.name,
        default_data_lake_storage=synapse.DataLakeStorageAccountDetailsArgs(
            account_url=storage_account.primary_endpoints.dfs,
            filesystem=filesystem.name,
        ),
        sql_administrator_login=admin_login,
        sql_administrator_login_password=admin_password,
        identity=synapse.ManagedIdentityArgs(
            type="SystemAssigned",
        ),
        managed_resource_group_name=resource_group.name.apply(lambda name: f"{name}-synapse-managed"),
        location=resource_group.location
    )
    
    return workspace

def setup_firewall(
    resource_group: resources.ResourceGroup,
    workspace: synapse.Workspace,
    ip_start: str,
    ip_end: str
):
    """Firewall ルールの設定"""
    
    return synapse.IpFirewallRule("allowSpecificRange",
        resource_group_name=resource_group.name,
        workspace_name=workspace.name,
        start_ip_address=ip_start,
        end_ip_address=ip_end
    )

def create_sql_pool(resource_group: resources.ResourceGroup, workspace: synapse.Workspace):
    """専用 SQL プールの作成"""
    
    return synapse.SqlPool("sqlPool",
        resource_group_name=resource_group.name,
        workspace_name=workspace.name,
        sku=synapse.SkuArgs(
            name="DW100c", # 最小構成
            tier="DataWarehouse"
        ),
        location=resource_group.location
    )

def create_spark_pool(resource_group: resources.ResourceGroup, workspace: synapse.Workspace):
    """Apache Spark プールの作成"""
    
    return synapse.BigDataPool("sparkPool",
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

def deploy_synapse():
    """Synapse DWH 環境全体のデプロイ"""
    
    # 1. 基本リソースの準備
    resource_group = resources.ResourceGroup("synapse-rg")
    
    # パスワード生成
    sql_admin_password = random.RandomPassword("sqlAdminPassword",
        length=16,
        special=True,
        min_upper=1,
        min_lower=1,
        min_numeric=1
    )

    # Config 取得
    config = pulumi.Config()
    sql_admin_login = config.get("sqlAdmin") or "sqladminuser"
    allowed_ip_start = config.get("allowedIpStart")
    allowed_ip_end = config.get("allowedIpEnd")

    # 2. ストレージ基盤の作成
    storage_account, filesystem = create_storage_infrastructure(resource_group)

    # 3. Synapse Workspace の作成
    workspace = create_synapse_workspace(
        resource_group, 
        storage_account, 
        filesystem, 
        sql_admin_login, 
        sql_admin_password.result
    )

    # 4. ネットワークセキュリティ設定
    if allowed_ip_start and allowed_ip_end:
        setup_firewall(resource_group, workspace, allowed_ip_start, allowed_ip_end)

    # 5. 分析エンジンの作成 (SQL Pool & Spark Pool)
    sql_pool = create_sql_pool(resource_group, workspace)
    spark_pool = create_spark_pool(resource_group, workspace)

    # 6. スタック出力 (Exports)
    pulumi.export("resource_group_name", resource_group.name)
    pulumi.export("storage_account_name", storage_account.name)
    pulumi.export("synapse_workspace_name", workspace.name)
    pulumi.export("synapse_workspace_url", workspace.connectivity_endpoints)
    pulumi.export("sql_admin_user", sql_admin_login)
    pulumi.export("sql_admin_password", sql_admin_password.result)
    pulumi.export("sql_pool_name", sql_pool.name)
    pulumi.export("spark_pool_name", spark_pool.name)