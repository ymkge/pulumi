import pulumi
import bigquery # bigquery.py を読み込む

# 関数を呼び出してリソースを作成
dwh_outputs = bigquery.create_dwh()

# メインファイルで結果を出力（何が出力されるか一覧性が良くなる）
pulumi.export("main_dataset_id", dwh_outputs["dataset_id"])