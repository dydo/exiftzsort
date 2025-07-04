# 📸 exiftzsort

**exiftzsort** は、画像・動画ファイルを EXIF やメタデータのタイムスタンプに基づいて日付別のディレクトリに整理する CLI ツールです。タイムゾーン（手動指定または GPS による自動判定）に対応し、コピーまたはシンボリックリンクによる整理が可能です。ログの出力レベルは `--log-level` オプションで柔軟に設定できます。

---

## ✨ 特長

- EXIF や FFprobe によるメタデータから日時を抽出
- GPS 情報からタイムゾーンを自動判定（`--exif-timezone auto`）
- `YYYY/YYYY_MM` 形式のフォルダに整理
- 重複ファイルを内容比較で回避（比較方法を選択可能）
- コピーまたはシンボリックリンクの出力に対応
- `--log-level` によりログ出力レベルを調整可能（`DEBUG`, `INFO`, `WARN`, `ERROR`）

---

## 🎯 このツールが役立つ人
写真や動画を複数のカメラやスマホ、家族の端末から集めて管理していると、ファイル名や保存場所がバラバラになりがちです。
そんなとき、撮影された「本当の時間順」に並べ直して、一つの流れとして見たいと思ったことはありませんか？

exiftzsort は、異なる機種や人から集まった写真・動画を、実際の撮影時刻に基づいて時系列に整理してくれるツールです。
バラバラだった思い出が、きれいに並びます📅✨

---

## 🛠 オプション

| オプション             | 説明                                                             |
| ---------------------- | ---------------------------------------------------------------- |
| `source_dir`           | 入力ディレクトリ（省略時はカレントディレクトリ）                |
| `--output-dir`         | 出力先のベースディレクトリ（省略時はカレントディレクトリ）       |
| `--copy`               | シンボリックリンクではなくコピーで出力（デフォルトはシンボリックリンク） |
| `--cmp-mode`           | 重複比較方法：`filecmp`（高速）または `hash`（精密）             |
| `--exif-timezone`      | EXIF タイムスタンプのタイムゾーン指定                            |
|                        | - `"auto"`：GPS位置情報から自動判定                             |
|                        | - `"local"`：実行環境のローカルタイムゾーン（デフォルト）       |
|                        | - `Asia/Tokyo` など IANA 名で指定                               |
| `--log-level`          | 表示するログの最小レベル：`DEBUG` / `INFO` / `WARN` / `ERROR`（デフォルト：`WARN`） |
| `--enable-skip-dir`    | 指定ディレクトリ名をスキップする機能を有効化                      |
| `--skip-dirs`          | スキップ対象のディレクトリ名リスト（`--enable-skip-dir` と併用）  |
| `-h`, `--help`         | ヘルプ表示                                                       |


---

## 🧪 ログ出力レベル例

```bash
# デフォルト（WARN と ERROR のみ）
python exiftzsort.py ./media

# INFO 以上（INFO, WARN, ERROR）を表示
python exiftzsort.py ./media --log-level INFO

# DEBUG も含めてすべて表示
python exiftzsort.py ./media --log-level DEBUG

# エラーのみ表示（最も静かなモード）
python exiftzsort.py ./media --log-level ERROR
```

---

## 🔧 インストール

### 必要パッケージ

```bash
pip install pillow timezonefinder
```

※ 動画のメタデータ取得には `ffprobe`（`ffmpeg` に含まれる）が必要です。

---

## 🚀 使用例

```bash
# デフォルト設定（カレントディレクトリを処理）
python exiftzsort.py

# コピー出力 + タイムゾーン指定
python exiftzsort.py ./import --copy --exif-timezone Asia/Tokyo

# 固定な重複比較 + デバッグログ
python exiftzsort.py ./media --cmp-mode hash --log-level DEBUG

# 出力ディレクトリを指定
python exiftzsort.py ./media --output-dir ./sorted_output
```

---

## 📂 出力先ディレクトリ構造例

```
Pict_works/
└── New/
    └── 2023/
        └── 2023_07/
            ├── 20230725-102015.jpg
            ├── 20230725-102016-01.jpg
            └── raw/
                ├── 20230725-102017.dng
                └── 20230725-102018-01.cr2
```

---

## 📝 ライセンス

Apache License 2.0\
Copyright (c) 2025 dydo

---

## 😋 作者

作成者: **dydo**\
コントリビューション歓迎！

---

## ⚠️ 免責事項

本ソフトウェアは「現状のまま」提供されており、明示または黙示を問わず、  
いかなる保証も伴いません。本ツールの使用により生じた損害・データ損失・  
その他いかなる結果についても、作者は一切の責任を負いません。  
**ご使用の前に、必ず大切なファイルのバックアップをお取りください。使用は自己責任でお願いします。**

