# 灵枢 3.0 自定义接口补丁（Custom Provider Patch）

给本地应用「灵枢 3.0」（XiaoJiuAI 出品的 AI 长篇小说工具）增加 **自定义 OpenAI 兼容接口** 支持：
不用改应用功能本身，通过修补打包产物，让服务商列表多出一个「自定义接口」选项，
可自由填写 **Base URL / API Key / 模型**，并支持 **从接口拉取模型列表**。

> ⚠️ 仅供个人学习研究使用。灵枢 3.0 版权归原作者所有，本仓库不包含、也不分发该应用的任何二进制或前端代码。

## 功能

- 服务商列表新增 `custom`（自定义接口），分组为「其他模型」
- 设置页出现「接口地址（Base URL）」输入框，仅自定义接口时显示；保存后回显
- 模型版本下拉支持 **拉取模型列表**（走后端代理请求 `GET {base_url}/models`，避免浏览器跨域）
- 自定义接口的模型下拉支持 **手动输入任意型号**（filterable + tag），拉取失败也能手填
- 连接测试、保存逻辑全部兼容自定义接口；不填地址保存会提示
- **设置页跟随实际配置**：打开设置自动定位到当前使用的服务商（原版每次强制回到 DeepSeek，密钥状态显示错乱）
- **托盘驻留**：点关闭隐藏到托盘、后台继续运行；托盘左键恢复窗口，右键菜单可退出（`app-src/main.cjs` + 内置 `build/icon.png`）

## 改了哪里

灵枢 3.0 的后端是 PyInstaller 打包的 Python（`resources/nova-api/nova-api.exe`），
前端是 Vite 压缩后的单文件 bundle（`resources/web/assets/index-*.js`）。本补丁：

| 目标 | 文件 | 说明 |
| --- | --- | --- |
| 后端 | `patch/providers.py` | 重写 `app/llm/providers.py`：9 个原服务商预置 + `custom` 条目，`get_provider()` 读取已存 Base URL |
| 后端 | `patch/settings.py` | 重写 `app/services/settings.py`：按服务商保存地址（`llm_bases`）、健康检查走自定义端点、`remote_models()` 拉取模型列表 |
| 后端 | `patch/routers_settings.py` | 重写 `app/routers/settings.py`：原 4 条路由 + 新增 `GET /api/settings/remote-models` |
| 打包 | `scripts/repack2.py` | 把上述模块重新编译并替换进 PyInstaller 的 PYZ 归档（无需完整源码） |
| 前端 | `scripts/inject_tpl.js` / `scripts/inject_fe2.js` | 位置切割法向压缩 bundle 注入：接口地址输入框、拉取按钮、下拉 filterable/tag、保存与回显逻辑 |

关键实现点：

- **PYZ 重打包**：PYZ 归档内条目无长度前缀、位置为绝对偏移，重打包需同时修正目录项与 CArchive cookie（见 `repack2.py`）
- **前端注入**：压缩后的 Vue render 函数用「锚点唯一性校验 + 位置切割」注入，
  模板缓存槽、`patchFlag` 动态 props 数组都要对应更新；API 请求必须复用应用自带的
  `iw()` 封装（内部走 `window.novaDesktop.apiBase`，file:// 加载时裸 `fetch("/api/...")` 是打不到后端的）

## 使用前提

- Windows + 灵枢 3.0（本补丁对应版本：`nova-api.exe` 11,952,776 字节 / `index-BZrTDTJi.js` 602,212 字节）
- Python 3.12（重编译用）、Node.js（前端注入用）
- 动手前**务必备份** `resources/nova-api/nova-api.exe` 和 `resources/web/assets/index-*.js`

## 免责声明

- 本仓库仅含补丁源码与工具脚本，不含灵枢 3.0 的任何部分
- 应用更新后文件哈希变化，锚点会失效，需要重新定位
- 使用产生的任何问题由使用者自行承担
