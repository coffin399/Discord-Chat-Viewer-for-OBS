# Discord Chat Viewer for OBS - ドキュメント

このディレクトリには、Discord Chat Viewer for OBSのドキュメントサイトが含まれています。

## ファイル構成

- `index.html` - メインのドキュメントページ
- `styles.css` - スタイルシート
- `README.md` - このファイル

## GitHub Pages でのデプロイ

このドキュメントサイトはGitHub Pagesで自動デプロイされます。

### セットアップ手順

1. リポジトリの設定でGitHub Pagesを有効化
2. ソースを「GitHub Actions」に設定
3. `.github/workflows/deploy.yml`が自動的にデプロイを実行

### ローカルでの確認

```bash
# ローカルサーバーで確認
cd docs
python -m http.server 8000
# ブラウザで http://localhost:8000 にアクセス
```

## カスタマイズ

- `index.html` - コンテンツの編集
- `styles.css` - デザインの変更
- `.github/workflows/deploy.yml` - デプロイ設定の変更

## ライセンス

MIT License
