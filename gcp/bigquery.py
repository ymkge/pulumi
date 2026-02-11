import json
import os
import pulumi
import pulumi_gcp as gcp

def create_dwh():
    """
    BigQueryのデータセット、テーブル、IAM権限を作成し、
    主要なリソースIDを辞書として返します。
    """

    # ==============================================================================
    # 設定値 (Configuration)
    # ==============================================================================
    config = pulumi.Config()
    
    # pulumi config から取得（未設定の場合はデフォルト値を使用）
    DATASET_ID = config.get("dataset_id") or "app_analytics_dwh"
    LOCATION = config.get("location") or "asia-northeast1"
    # SA_EMAIL は必須設定とし、未設定の場合は実行時にエラーを出す（または None を許容する場合はデフォルト値を設定）
    SA_EMAIL = config.get("sa_email") or "my-batch-job@my-project.iam.gserviceaccount.com"

    # ==============================================================================
    # 1. BigQuery データセットの作成
    # ==============================================================================
    dataset = gcp.bigquery.Dataset("analytics_dataset",
        dataset_id=DATASET_ID,
        friendly_name="App Analytics DWH",
        description="アプリのログデータを蓄積・分析するためのデータセット",
        location=LOCATION,
        default_table_expiration_ms=None,
        delete_contents_on_destroy=False 
    )

    # ==============================================================================
    # 2. テーブルスキーマの読み込み
    # ==============================================================================
    # 外部 JSON ファイルからスキーマを読み込む
    schema_path = os.path.join(os.path.dirname(__file__), "schemas", "user_events.json")
    with open(schema_path, "r") as f:
        schema_def = json.load(f)

    # ==============================================================================
    # 3. テーブルの作成（パーティション・クラスタリング設定付き）
    # ==============================================================================
    table = gcp.bigquery.Table("events_table",
        dataset_id=dataset.dataset_id,
        table_id="user_events",
        description="ユーザーの行動ログテーブル",
        deletion_protection=False,

        # スキーマの設定
        schema=json.dumps(schema_def),

        # パーティション設定
        time_partitioning=gcp.bigquery.TableTimePartitioningArgs(
            type="DAY",
            field="event_timestamp",
        ),

        # クラスタリング設定
        clustering=["event_name", "user_id"]
    )

    # ==============================================================================
    # 4. アクセス権限（IAM）の設定
    # ==============================================================================
    dataset_access = gcp.bigquery.DatasetIamMember("dataset_editor_access",
        dataset_id=dataset.dataset_id,
        role="roles/bigquery.dataEditor",
        member=f"serviceAccount:{SA_EMAIL}",
        opts=pulumi.ResourceOptions(depends_on=[dataset])
    )

    # ==============================================================================
    # 5. 戻り値 (Return Values)
    # ==============================================================================
    return {
        "dataset_id": dataset.dataset_id,
        "table_id": table.table_id,
        "table_full_path": pulumi.Output.concat(dataset.project, ".", dataset.dataset_id, ".", table.table_id)
    }