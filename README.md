# X-Skills - Twitter/X 自动化发布工具

基于 CDP (Chrome DevTools Protocol) 的 Twitter/X 自动化发布工具，支持发布推文、线程、搜索和互动功能。

---

## 🌟 灵感来源

本项目灵感来自 **[xiaohongshu-skills](https://github.com/autoclaw-cc/xiaohongshu-skills)** - 小红书自动化发布工具。

感谢原作者的出色设计，本项目的架构和 CLI 设计参考了 xiaohongshu-skills 的模式。

---

## ✨ 功能特性

- ✅ 发布单条推文
- ✅ 发布线程（多条推文）
- ✅ 搜索推文
- ✅ 点赞/转发/评论
- ✅ 多账号管理
- ✅ 登录状态检查
- ✅ CDP 连接支持

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd X-Skills
pip3 install -r requirements.txt
playwright install chromium
```

### 2. 启动 Chrome

```bash
python scripts/chrome_launcher.py
```

### 3. 登录 Twitter

```bash
python scripts/x_publish.py login
```

### 4. 发布推文

```bash
python scripts/x_publish.py --tweet "这是推文内容"
```

---

## 📋 常用命令

### 启动浏览器

```bash
# 有窗口模式（推荐）
python scripts/chrome_launcher.py

# 无头模式
python scripts/chrome_launcher.py --headless

# 指定端口
python scripts/chrome_launcher.py --port 9223

# 重启
python scripts/chrome_launcher.py --restart

# 关闭
python scripts/chrome_launcher.py --kill
```

### 发布推文

```bash
# 直接发布
python scripts/x_publish.py --tweet "推文内容"

# 从文件读取
python scripts/x_publish.py --tweet-file tweet.txt

# 带图片
python scripts/x_publish.py --tweet "内容" --images pic1.jpg pic2.jpg

# 预览模式（不实际发布）
python scripts/x_publish.py --preview --tweet "内容"
```

### 发布线程

```bash
# 多条推文
python scripts/x_publish.py --thread "推文 1" "推文 2" "推文 3"

# 从文件读取（每行一条）
python scripts/x_publish.py --thread-file thread.txt
```

### 账号管理

```bash
# 列出所有账号
python scripts/x_publish.py list-accounts

# 添加新账号
python scripts/x_publish.py add-account work --alias "工作号"

# 切换账号
python scripts/x_publish.py switch-account --account personal
```

---

## 📁 项目结构

```
X-Skills/
├── README.md             # 本文件
├── SKILL.md              # 完整使用说明
├── requirements.txt      # Python 依赖
├── scripts/
│   ├── chrome_launcher.py  # Chrome 启动器
│   └── x_publish.py        # Twitter 发布核心
├── config/               # 配置文件
├── docs/                 # 详细文档
├── images/               # 图片资源
└── tmp/                  # 临时文件
```

---

## 🔧 技术栈

- **Python 3.9+**
- **Playwright** - 浏览器自动化
- **CDP** - Chrome DevTools Protocol
- **Twitter Web** - 网页版 Twitter

---

## ⚠️ 注意事项

1. **登录状态**：首次使用需要手动扫码登录
2. **字符限制**：单条推文不超过 280 字符
3. **线程限制**：单次最多发布 25 条推文
4. **图片限制**：单条推文最多 4 张图片
5. **速率限制**：避免短时间内大量发布

---

## 📖 详细文档

- [SKILL.md](./SKILL.md) - 完整使用说明
- [docs/](./docs/) - 详细文档目录

---

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- **[xiaohongshu-skills](https://github.com/autoclaw-cc/xiaohongshu-skills)** - 本项目灵感来源和架构参考
- **Playwright** - 优秀的浏览器自动化工具
- **Twitter** - 平台提供方

---

**创建时间**: 2026-03-09  
**版本**: 0.1.0  
**状态**: 开发中 🚧
