# 言葉の贈り物 開発記録


---

## β-24

### プロジェクトテーマ
AI実行仕様書を組み込んだ結果、
AIは仕様書を忠実に守る一方で、
文章を書くという本来の目的が弱くなった。

β-24では、

「文章を書くことを目的とした対話制御」

を実装する。
---

## β-24-1

### 内容

- story_state を追加
- load_story_state() を追加
- save_story_state() を追加
- generate_response() で state を取得

### テスト

- アプリ起動　OK
- 会話　OK
---

## β-24-2

### 内容

- runtime_initial.txt を追加
- load_runtime_initial() を追加
- generate_response() で runtime_initial を読込

### テスト

- アプリ起動　OK
- 会話　OK
---

## β-24-3

### 内容

- build_messages() を状態対応へ変更
- runtime_initial を毎回送信
- story_spec は INITIAL 時のみ送信
- state を build_messages() に渡す

### テスト

- アプリ起動　OK
- 初回会話　OK
- エラーなし
---

## 今後の予定

- β-24-4  
  INTERVIEWブロックを実装

- β-24-5  
  READY判定を実装

- β-24-6  
  GENERATEブロックを実装

- β-24-7  
  動作調整・完成
  