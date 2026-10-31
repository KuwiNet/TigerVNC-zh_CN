# TigerVNC-zh_CN

TigerVNC Viewer 的**简体中文语言包**（`tigervnc.mo`）。

tag 与 TigerVNC 官方版本号保持一致（例如 `v1.16.2`），并通过 GitHub Actions
**自动检查官方新版本**，发现新版即自动生成并发布对应的中文语言包。

## 为什么只需要一个 .mo 文件

TigerVNC 的 viewer 在启动时调用：

```
bindtextdomain("tigervnc", <exe所在目录>\locale)
```

并按照系统区域从以下位置加载翻译：

```
locale\<语言>\LC_MESSAGES\tigervnc.mo
```

因此只要把编译好的 `tigervnc.mo` 放到正确位置，界面就会显示简体中文，
**无需改动 exe 本体**。

## 使用方法

1. 在 [Releases](../../releases) 下载对应版本的语言包 zip；
2. 解压后得到 `locale` 文件夹；
3. 把 `locale` 文件夹放到 `vncviewer64-*.exe` **同目录**下；
4. 运行 viewer 即可，界面显示简体中文。

> 提示：需在中文系统区域下运行；英文系统需在“区域设置→语言”中加入中文，
> 否则 gettext 会回退英文界面。

## 本仓库结构

```
.
├── locale/zh_CN/LC_MESSAGES/tigervnc.mo   # 当前简体中文语言包（产物）
├── po/
│   ├── tigervnc.pot                       # 官方翻译模板
│   └── zh_CN.po                           # 简体中文翻译源（可编辑）
├── scripts/
│   ├── build_mo.py                        # pot + po -> mo（可移植，依赖 polib）
│   └── validate_mo.py                     # 校验 mo 文件
└── .github/workflows/sync-locale.yml      # 自动检查官方版本并发布
```

## 自动更新机制

`.github/workflows/sync-locale.yml` 每周一自动（也支持手动运行）执行：

1. 查询 TigerVNC 官方最新 release 的 tag；
2. 与本仓库最新 tag 比较；
3. 若官方有新版：
   - 下载官方新版 `po/tigervnc.pot`；
   - 用 `scripts/build_mo.py` 合并旧 `zh_CN.po` 的已有翻译并生成新 `.mo`；
   - 提交变更并打与官方一致的 tag（如 `v1.16.2`）；
   - 发布 release，附件为只含 `locale` 目录的压缩包。

如需手动触发，在仓库 Actions 页选择该工作流点击 **Run workflow** 即可。

## 翻译来源

- 官方模板：<https://github.com/TigerVNC/tigervnc/blob/master/po/tigervnc.pot>
- 简体中文翻译：以 Translation Project 的 zh_CN 翻译为基础，并按新版模板补译。
