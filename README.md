# SpeakerDeck Downloader

SpeakerDeckのプレゼンテーション資料をPDFファイルとしてダウンロードするPythonツールです。

## 機能

- SpeakerDeckのURLを指定してプレゼンテーションをダウンロード
- すべてのスライドを1つのPDFファイルに結合
- オリジナルの画質を維持

## 必要環境

- Python 3.7以上

## インストール

1. このリポジトリをクローンまたはダウンロード

2. 依存パッケージをインストール:
```bash
pip install -r requirements.txt
```

## 使い方

### 基本的な使用方法

```bash
python speakerdeck_downloader.py <SpeakerDeck URL>
```

### 例

```bash
python speakerdeck_downloader.py https://speakerdeck.com/nrinetcom/awstoan-hao-ji-shu
```

### 出力先を指定

```bash
python speakerdeck_downloader.py https://speakerdeck.com/nrinetcom/awstoan-hao-ji-shu -o downloads
```

### ヘルプ

```bash
python speakerdeck_downloader.py --help
```

## オプション

- `url`: ダウンロードするSpeakerDeckのURL（必須）
- `-o, --output`: 出力ディレクトリ（デフォルト: カレントディレクトリ）

## URLの形式

以下の形式のURLに対応しています:
```
https://speakerdeck.com/ユーザー名/プレゼンテーション名
```

例:
- `https://speakerdeck.com/nrinetcom/awstoan-hao-ji-shu`

## 出力

ダウンロードされたPDFファイルは、プレゼンテーションのタイトルを基にしたファイル名で保存されます。

## 注意事項

- このツールは教育目的で作成されています
- ダウンロードした資料の利用については、各プレゼンテーションのライセンスに従ってください
- 過度なリクエストはサーバーに負荷をかける可能性があるため、適切な間隔を空けて使用してください

## トラブルシューティング

### スライドが見つからない場合

SpeakerDeckのHTML構造が変更された可能性があります。その場合は、スクリプトの更新が必要です。

### ダウンロードエラー

- インターネット接続を確認してください
- URLが正しいか確認してください
- SpeakerDeckのサイトがアクセス可能か確認してください

## ライセンス

MIT License
