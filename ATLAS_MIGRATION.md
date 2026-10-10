# Atlas教材を別PCで使う

この移行ブランチの教材入口は [portable-atlas/README.md](portable-atlas/README.md) です。既存Portal/Coreの構成はそのまま残し、移行用readerを独立したdirectoryに置いています。

```sh
cd portable-atlas
node scripts/verify-delivery.mjs
npm test
node scripts/local-learning-preview.mjs
```

保存readerにはNode.js 22.13以上を使います。依存install、隣接repo、認証、Dockerは不要です。表示されたlocalhost URLを自分で開き、終了時はCtrl+Cを押します。

正式142・候補追加6・その他未統合43を別一覧で保ちます。新しい実測・中央統合・分野完成を主張するブランチではありません。mainへの統合は別工程です。

[非秘密の入力と再生成手順](portable-atlas/docs/REGENERATION.md) と [復元手順](portable-atlas/docs/RESTORE.md) を参照してください。過去の画像・全文実測原票・個人情報を含む資料はここへ追加していません。これらを再生成データで過去の証拠として置き換えず、必要性を判断するまで別の非公開保全物として保持します。
