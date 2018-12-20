Python Wrapper for AquesTalk (Old License)
==========================================

旧ライセンス版AquesTalkのPythonラッパー

**32ビット版Windows**のPythonでのみ動作します。

AquesTalkのライセンス変更については[公式ブログ][blog.a-quest]を参照してください。

Installation
------------
```
pip install AquesTalk-python
```

Usage
-----
```
import aquestalk
aq = aquestalk.load('f1')
wav = aq.synthe("こんにちわ")
type(wav)
# => <class 'wave.Wave_read'>
```

Required Notices
----------------
- 本ライブラリは、株式会社アクエストの規則音声合成ライブラリ「AquesTalk」を使用しています。
- 本ライブラリに同梱のDLLファイルの著作権は同社に帰属します。
    - 詳細はAqLicense.txtをご覧ください。

[blog.a-quest]: http://blog-yama.a-quest.com/?eid=970181
