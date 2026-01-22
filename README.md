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



## セットアップ & 実行方法 (AWS/GCP共通)



各ディレクトリ配下が独立した Pulumi プロジェクトとして構成されています。



### 1. ディレクトリへ移動



```bash

cd gcp  # または cd aws

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

    
