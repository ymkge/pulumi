# Pulumi Infrastructure Samples

このリポジトリは、Pulumi と Python を使用した IaC (Infrastructure as Code) のサンプルコード集です。
主要なクラウドプロバイダー (GCP, AWS, Azure) ごとのディレクトリ構成で、実践的なインフラ構築パターンを管理していく予定です。

## ディレクトリ構成

*   `gcp/`: Google Cloud Platform 用のサンプル (現在は BigQuery DWH 構築など)
*   `aws/`: Amazon Web Services 用のサンプル (今後追加予定)
*   `azure/`: Microsoft Azure 用のサンプル (今後追加予定)

## 前提条件

*   [Pulumi CLI](https://www.pulumi.com/docs/install/)
*   Python 3.9 以上
*   各クラウドプロバイダーの CLI ツールと認証設定
    *   Google Cloud SDK (`gcloud auth login`, `gcloud auth application-default login`)
    *   AWS CLI (`aws configure`)
    *   Azure CLI (`az login`)

## セットアップ & 実行方法 (GCPの例)

各ディレクトリ配下が独立した Pulumi プロジェクトとして構成されています。

### 1. ディレクトリへ移動

```bash
cd gcp
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

### 5. デプロイの実行 (プレビュー & 適用)

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