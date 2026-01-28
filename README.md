# Pulumi Infrastructure Samples

このリポジトリは、Pulumi と Python を使用した IaC (Infrastructure as Code) のサンプルコード集です。
主要なクラウドプロバイダー (GCP, AWS, Azure) ごとのディレクトリ構成で、実践的なインフラ構築パターンを管理していく予定です。

## ディレクトリ構成

*   `gcp/`: Google Cloud Platform 用のサンプル (BigQuery DWH 構築)
*   `aws/`: Amazon Web Services 用のサンプル (Redshift DWH 構築)
*   `azure/`: Microsoft Azure 用のサンプル (Synapse Analytics DWH 構築)

## 前提条件

*   [Pulumi CLI](https://www.pulumi.com/docs/install/)
*   Python 3.9 以上
*   各クラウドプロバイダーの CLI ツールと認証設定
    *   Google Cloud SDK (`gcloud auth login`, `gcloud auth application-default login`)
    *   AWS CLI (`aws configure`)
    *   Azure CLI (`az login`)

## セットアップ & 実行方法 (共通)

各ディレクトリ配下が独立した Pulumi プロジェクトとして構成されています。

### 1. ディレクトリへ移動

```bash
cd gcp  # または cd aws, cd azure
```

### 2. Python 仮想環境の作成と有効化

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. Pulumi スタックの初期化と選択

まだスタックがない場合は初期化します。

```bash
pulumi stack init dev
```

### 5. 設定 (Configuration)

各プロバイダー固有の設定を行います。詳細は後述の [Configuration](#configuration) セクションを参照してください。

### 6. デプロイの実行 (プレビュー & 適用)

```bash
pulumi up
```

リソースを削除する場合は以下のコマンドを実行します。

```bash
pulumi destroy
```

## 実装済みサンプル詳細

### GCP (`/gcp`)

*   **BigQuery DWH**:
    *   データセットの作成
    *   テーブル作成（日付パーティショニング、クラスタリング設定済み）
    *   IAM 権限設定（サービスアカウントへの権限付与）

### AWS (`/aws`)

*   **Redshift DWH**:
    *   Redshift クラスターの構築 (Single-node, dc2.large)
    *   IAM ロールの作成 (S3 読み取り権限の付与)
    *   VPC セキュリティグループの設定 (5439 ポートの開放)
    *   デフォルト VPC への自動デプロイ設定

### Azure (`/azure`)

*   **Synapse Analytics DWH**:
    *   **Resource Group**: リソース管理用のグループ作成。
    *   **Data Lake Storage Gen2**: Synapse必須のストレージ基盤 (HNS有効)。
    *   **Synapse Workspace**: 分析エンジンの統合環境。
    *   **Dedicated SQL Pool**: データウェアハウス機能 (最小構成: DW100c)。
    *   **Apache Spark Pool**: ビッグデータ処理機能 (自動停止・オートスケール設定済み)。
    *   **Security**: 管理者パスワードの自動生成と、開発用ファイアウォールルールの設定。

## Configuration

プロジェクトごとの設定項目です。

### AWS (`/aws`)

Redshift プロジェクトでは、セキュリティのためパスワードの設定が必須です。許可IPは任意です。

```bash
cd aws

# DBパスワードの設定 (必須)
pulumi config set --secret dbPassword "YourStrongPassword!"

# 許可IPアドレスの設定 (任意: 設定しない場合は外部アクセス不可)
pulumi config set allowedCidr "203.0.113.1/32"
```

### Azure (`/azure`)

Synapse Analytics プロジェクトでは、必要に応じて管理者ユーザー名と許可IP範囲を設定できます。

```bash
cd azure

# 管理者ユーザー名の設定 (任意: デフォルトは sqladminuser)
pulumi config set sqlAdmin "myadmin"

# 許可IP範囲の設定 (任意: 設定しない場合は外部アクセス不可)
# 1つのIPのみ許可する場合は start と end に同じ値を設定します
pulumi config set allowedIpStart "203.0.113.1"
pulumi config set allowedIpEnd "203.0.113.1"
```

### GCP (`/gcp`)

BigQuery プロジェクトでは、現在 Pulumi Config を使用していません。
設定を変更する場合は `gcp/bigquery.py` 内の定数定義を直接編集してください。

*   `DATASET_ID`: データセットID
*   `LOCATION`: ロケーション (例: `asia-northeast1`)
*   `SA_EMAIL`: 権限を付与するサービスアカウントのメールアドレス

## Security & Production Readiness (Next Steps)

現在の構成は**開発・検証用 (Development Sandbox)** を想定しており、利便性を優先しています。
本番環境 (Production) で運用する場合、セキュリティ基準を満たすために以下の改善を推奨します。

### 1. ネットワークセキュリティの強化
*   **Public Access の無効化**: 現在の `publicly_accessible=True` (AWS) やファイアウォール全開放設定を無効化し、VPCエンドポイント (PrivateLink) や閉域網経由でのみアクセス可能にする。
*   **IP制限の厳格化**: Config で許可IPを設定するか、踏み台サーバー (Bastion Host) 経由でのアクセスに限定する。

### 2. 認証・機密情報の管理
*   **Secrets Manager 連携**: パスワードを Pulumi Config で渡すのではなく、AWS Secrets Manager / Azure Key Vault 等で動的に生成・管理し、アプリケーションから参照させる。
*   **IAM / RBAC の最小権限**: 現在の広範な権限を見直し、必要最小限の権限セット (Least Privilege) を定義する。

### 3. 暗号化と監査
*   **CMK (Customer Managed Key)**: デフォルトの暗号化キーではなく、自社管理の鍵 (KMS) を使用してデータを暗号化する。
*   **Audit Logging**: 誰がいつアクセスしたかを追跡するため、監査ログを有効化し、セキュアなストレージへ転送・保管する。