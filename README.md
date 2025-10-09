# Discord Chat Viewer for OBS

Discordの特定のチャンネルのチャットを、OBSのブラウザソースにリアルタイムで可愛く表示するためのツールです。

## ✨ 特徴

-   **リアルタイム更新**: Discordのチャットが投稿されると、即座にOBS上の表示に反映されます。
-   **可愛いデザイン**: パステルカラーと手書き風フォントを使用した、吹き出し形式のチャットデザイン。
-   **メディア対応**: テキストだけでなく、画像、動画、URLの埋め込み（Embed）も表示できます。
-   **簡単セットアップ**: Windowsユーザー向けに、ダブルクリックで起動できるバッチファイルを用意しています。
-   **軽量動作**: Pythonの`discord.py`と`websockets`ライブラリを使用し、軽量に動作します。

## 🔧 必要なもの

-   [Python 3.8](https://www.python.org/downloads/) 以上
-   Discordアカウント
-   OBS Studio

## 🚀 セットアップ手順

### 1. ファイルの準備

このプロジェクトのファイルをダウンロードまたはクローンし、好きな場所に配置します。

### 2. Discord Botの準備

このツールはDiscord Botを利用してメッセージを取得します。

1.  **Botの作成**:
    -   [Discord Developer Portal](https://discord.com/developers/applications)にアクセスし、ログインします。
    -   `New Application`ボタンを押し、好きな名前（例: OBS Chat Bot）でアプリケーションを作成します。
    -   左側のメニューから `Bot` を選択し、`Add Bot` をクリックしてBotを作成します。

2.  **インテントの有効化**:
    -   Botのページで、`Privileged Gateway Intents` という項目を探します。
    -   **MESSAGE CONTENT INTENT** のトグルをオン（有効）にしてください。これがないとメッセージの内容を読み取れません。

3.  **Botトークンの取得**:
    -   Botの名前の下にある `Reset Token` (または `View Token`) をクリックして、Botのトークンをコピーします。
    -   **⚠️ このトークンは絶対に他人に教えたり、公開しないでください。**

4.  **Botをサーバーに招待**:
    -   左側のメニューから `OAuth2` -> `URL Generator` を選択します。
    -   `SCOPES` で `bot` を選択します。
    -   `BOT PERMISSIONS` で以下の権限にチェックを入れます。
        -   `View Channels` (チャンネルを見る)
        -   `Send Messages` (メッセージを送信) ※必須ではないが推奨
        -   `Read Message History` (メッセージ履歴を読む)
    -   生成されたURLをコピーし、ブラウザで開いて、Botを追加したいあなたのDiscordサーバーに招待します。

5.  **チャンネルIDの取得**:
    -   Discordの設定で「詳細設定」を開き、「開発者モード」をオンにします。
    -   OBSに表示したいチャンネルを右クリックし、「チャンネルIDをコピー」を選択します。

### 3. フォントの配置

`fonts` フォルダを作成し、その中に `HachiMaruPop-Regular.ttf` を配置してください。
（フォントは[Google Fonts](https://fonts.google.com/specimen/Hachi+Maru+Pop)などからダウンロードできます）

### 4. 設定ファイルの編集

`config.yaml` をテキストエディタで開き、あなたの情報に書き換えます。

```yaml
# Discord Botのトークン
DISCORD_BOT_TOKEN: "ここに先ほどコピーしたBotトークンを貼り付け"

# 表示したいチャンネルのID
DISCORD_CHANNEL_ID: 123456789012345678 # ここにコピーしたチャンネルIDを貼り付け
```

## 💡 使い方

### Windowsの場合 (推奨)

1.  **`start.bat` をダブルクリックして実行します。**
2.  黒いウィンドウが開き、必要なライブラリのインストールとサーバーの起動が自動的に行われます。
3.  「`Starting the Discord Bot and WebSocket server...`」というメッセージが表示されれば成功です。

サーバーを停止するには、この黒いウィンドウを選択した状態で `Ctrl + C` を押してください。

### 手動での実行方法

1.  ターミナル（コマンドプロンプトやPowerShell）でこのプロジェクトのフォルダに移動します。
2.  仮想環境を作成して有効化します。
    ```bash
    # 仮想環境の作成 (初回のみ)
    py -m venv .venv
    # 仮想環境の有効化
    .venv\Scripts\activate
    ```
3.  必要なライブラリをインストールします。
    ```bash
    pip install -r requirements.txt
    ```
4.  サーバーを起動します。
    ```bash
    python server.py
    ```

## 🖥️ OBSへの設定

1.  OBSを起動し、「ソース」パネルの `+` ボタンから「**ブラウザ**」を選択します。
2.  プロパティ画面で、以下のように設定します。
    -   **`ローカルファイル`** にチェックを入れる。
    -   **`ローカルファイル`** の参照ボタンを押し、このプロジェクトフォルダ内の `index.html` を選択する。
    -   **`幅`** と **`高さ`** を配信画面に合わせて調整します。（例: 幅 `400`, 高さ `600`）
    -   必要であれば、「カスタムCSS」で見た目を調整することも可能です。
3.  `OK` をクリックしてソースを追加します。

これで、Discordにメッセージが投稿されるとOBSの画面にリアルタイムで表示されるようになります。

## 📂 ファイル構成

```
.
├── server.py              # Discord Bot兼WebSocketサーバー
├── index.html             # OBSで表示するチャット画面
├── config.yaml            # 設定ファイル
├── requirements.txt       # Pythonの依存ライブラリリスト
├── start.bat              # Windows用簡単起動スクリプト
├── setup_venv.bat         # (オプション) 仮想環境セットアップ用スクリプト
├── README.md              # このファイル
└── fonts/
    └── ここにフォントを配置.ttf # 表示用フォント
```

## 📄 ライセンス

このプロジェクトはMITライセンスです。