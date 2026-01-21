import pulumi
import redshift

# Redshift DWH環境の構築
dwh_outputs = redshift.create_data_warehouse()

# スタック出力
pulumi.export("redshift_cluster_endpoint", dwh_outputs["cluster_endpoint"])
pulumi.export("redshift_database_name", dwh_outputs["database_name"])
pulumi.export("redshift_username", dwh_outputs["username"])
