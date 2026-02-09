import pulumi
import redshift
import redshift_serverless

# --- Redshift DWH環境の構築 ---

# A. プロビジョニング版 (既存)
# dwh_outputs = redshift.create_data_warehouse()
# pulumi.export("redshift_type", "Provisioned")
# pulumi.export("redshift_cluster_endpoint", dwh_outputs["cluster_endpoint"])

# B. サーバーレス版 (新規)
dwh_outputs = redshift_serverless.create_redshift_serverless()
pulumi.export("redshift_type", "Serverless")
pulumi.export("redshift_endpoint", dwh_outputs["workgroup_endpoint"])

# --- 共通のスタック出力 ---
pulumi.export("redshift_database_name", dwh_outputs["database_name"])
pulumi.export("redshift_username", dwh_outputs["username"])
