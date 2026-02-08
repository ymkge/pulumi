# Cloud DWH Comparison

このドキュメントでは、本リポジトリで実装されている AWS (Redshift), Azure (Synapse Analytics), GCP (BigQuery) の3つのデータウェアハウス環境について、アーキテクチャ、機能、およびコストの観点から比較します。

## 1. リソース構成一覧

各クラウドプロバイダーで構築される主要リソースの対応表です。

| Feature | AWS (Redshift) | Azure (Synapse) | GCP (BigQuery) |
| :--- | :--- | :--- | :--- |
| **Compute Engine** | Redshift Cluster (`dc2.large`) | Dedicated SQL Pool (`DW100c`) <br> Spark Pool (`Small`) | BigQuery Serverless Compute |
| **Storage** | Cluster Local Storage (160GB) | Data Lake Storage Gen2 (ADLS) | BigQuery Managed Storage |
| **Network Security** | VPC Security Group (Port 5439) | Synapse Firewall Rules | IAM (No Network Boundary in Sample) |
| **Authentication** | Database Password + IAM Role | SQL Admin Password + Entra ID | Google Cloud IAM |
| **Provisioning Time** | 数分 (Cluster起動) | 数分〜10分 (Workspace作成) | 即時 (Dataset作成) |

## 2. 各プロバイダーの実装詳細

### AWS: Amazon Redshift (`/aws`)
**構成**:
- **Cluster**: `single-node` 構成の `dc2.large` インスタンス。開発・検証用に適した最小構成です。
- **Network**: デフォルトVPC内に配置。`pulumi config` で指定された IP (CIDR) からのアクセスのみを許可するセキュリティグループを設定。
- **Secrets**: データベースのマスターパスワードは `pulumi config set --secret` で暗号化して管理することを前提としています。

**特徴**:
- 従来のRDBに近い感覚で管理できます（PostgreSQL互換）。
- インスタンスタイプによってストレージ容量とパフォーマンスが決まります。

### Azure: Synapse Analytics (`/azure`)
**構成**:
- **Workspace**: 統合分析環境。
- **SQL Pool**: 専用のデータウェアハウスプール (`DW100c`)。
- **Spark Pool**: ビッグデータ処理用の Spark クラスター（自動停止機能付き）。
- **Data Lake**: HNS (Hierarchical Namespace) が有効化された Storage Account。
- **Identity**: `pulumi_random` を使用して管理者パスワードをデプロイごとに動的生成し、安全性を高めています。

**特徴**:
- DWH (SQL) と Big Data (Spark) が同一ワークスペースでシームレスに連携できます。
- リソースグループ単位でライフサイクルを管理しやすい構成です。

### GCP: BigQuery (`/gcp`)
**構成**:
- **Dataset**: `asia-northeast1` リージョンに作成。
- **Table**: JSONスキーマ定義に基づくテーブル作成。
- **Optimization**: `event_timestamp` による**パーティショニング**と、`event_name`, `user_id` による**クラスタリング**が設定済み。これによりクエリ料金とパフォーマンスが最適化されています。

**特徴**:
- 完全なサーバーレス。インフラのプロビジョニングやサイズ管理が不要です。
- スキーマ定義やIAM設定がコード内で完結しており、シンプルです。

## 3. コスト概算 (Cost Estimation)

※ 以下の価格は目安であり、リージョンや契約形態により変動します。

| Provider | Configuration | Estimated Cost (Running 24/7) | Note |
| :--- | :--- | :--- | :--- |
| **AWS** | `dc2.large` (1 node) | ~$180 / month | 一時停止 (Pause) 機能で課金を停止可能。 |
| **Azure** | `DW100c` + `Spark Pool` | **~$1,100+ / month** <br> (SQL: ~$1.5/h, Spark: ~$0.5/h) | **注意**: 非常に高額です。検証後は必ず `pulumi destroy` してください。SQL Poolの一時停止とSparkの自動停止を活用推奨。 |
| **GCP** | On-demand Analysis | ~$0 (Small scale) | ストレージ ($0.02/GB) とクエリ量 ($5/TB) 課金。小規模な検証であれば無料枠内で収まることが多いです。 |

## 4. 選択ガイド

*   **GCP (BigQuery)** を選ぶべき場合:
    *   **手軽に始めたい**: インフラ管理をしたくない、サーバーレスで運用したい。
    *   **コストを抑えたい**: データ量が少なく、常時稼働させる必要がない。
    *   **アドホック分析**: 必要な時に必要なだけクエリを投げたい。

*   **AWS (Redshift)** を選ぶべき場合:
    *   **既存のAWS環境がある**: S3上のデータや他のAWSサービスと密接に連携したい。
    *   **予測可能なパフォーマンス**: 専有インスタンスで安定した性能が必要。
    *   **移行**: 既存のPostgreSQLベースのシステムからの移行。

*   **Azure (Synapse)** を選ぶべき場合:
    *   **統合分析環境**: SQL DWHだけでなく、Sparkやパイプライン処理も一元管理したい。
    *   **Microsoftエコシステム**: Power BI や Azure Active Directory (Entra ID) との強力な連携が必要。
