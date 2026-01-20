import json
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
    # 実際の運用ではConfigなどから取得することもありますが、今回は定数として定義します
    DATASET_ID = "app_analytics_dwh"
    LOCATION = "asia-northeast1"
    SA_EMAIL = "my-batch-job@my-project.iam.gserviceaccount.com" # ※実際のSAへ書き換えてください

    # ==============================================================================
    # 1. BigQuery データセットの作成
    # ==============================================================================
    dataset = gcp.bigquery.Dataset("analytics_dataset",
        dataset_id=DATASET_ID,
        friendly_name="App Analytics DWH",
        description="アプリのログデータを蓄積・分析するためのデータセット",
        location=LOCATION,
        default_table_expiration_ms=None,      # テーブルのデフォルト有効期限（None=無期限）
        
        # 削除時の保護設定（開発用ならFalse、本番ならTrue推奨）
        delete_contents_on_destroy=False 
    )

    # ==============================================================================
    # 2. テーブルスキーマの定義
    # ==============================================================================
    # ユーザー行動ログを想定したスキーマ
    schema_def = [
        {
            "name": "event_timestamp",
            "type": "TIMESTAMP",
            "mode": "REQUIRED",
            "description": "イベント発生日時"
        },
        {
            "name": "user_id",
            "type": "STRING",
            "mode": "NULLABLE",
            "description": "ユーザーID"
        },
        {
            "name": "event_name",
            "type": "STRING",
            "mode": "REQUIRED",
            "description": "イベント名（例: login, purchase）"
        },
        {
            "name": "event_params",
            "type": "JSON",
            "mode": "NULLABLE",
            "description": "詳細パラメータ（JSON型）"
        }
    ]

    # ==============================================================================
    # 3. テーブルの作成（パーティション・クラスタリング設定付き）
    # ==============================================================================
    table = gcp.bigquery.Table("events_table",
        dataset_id=dataset.dataset_id,
        table_id="user_events",
        description="ユーザーの行動ログテーブル",
        deletion_protection=False,  # `pulumi destroy` で削除できるように設定

        # スキーマの設定（JSON文字列に変換して渡す）
        schema=json.dumps(schema_def),

        # 【重要】パーティション設定
        # 日付（event_timestamp）ごとにデータを分割保存し、クエリ料金を削減
        time_partitioning=gcp.bigquery.TableTimePartitioningArgs(
            type="DAY",
            field="event_timestamp",
        ),

        # 【重要】クラスタリング設定
        # よくフィルタリングに使われる列を指定して検索を高速化
        clustering=["event_name", "user_id"]
    )

    # ==============================================================================
    # 4. アクセス権限（IAM）の設定
    # ==============================================================================
    # 例: 特定のサービスアカウントに「データ編集者」権限を付与
    dataset_access = gcp.bigquery.DatasetIamMember("dataset_editor_access",
        dataset_id=dataset.dataset_id,
        role="roles/bigquery.dataEditor", # データの読み書き権限
        member=f"serviceAccount:{SA_EMAIL}",
        opts=pulumi.ResourceOptions(depends_on=[dataset]) # データセット作成後に実行
    )

    # ==============================================================================
    # 5. 戻り値 (Return Values)
    # ==============================================================================
    # __main__.py で利用・出力できるように辞書で返す
    return {
        "dataset_id": dataset.dataset_id,
        "table_id": table.table_id,
        "table_full_path": pulumi.Output.concat(dataset.project, ".", dataset.dataset_id, ".", table.table_id)
    }
