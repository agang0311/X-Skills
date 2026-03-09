---
name: XSkills
description: |
  将内容自动发布到 Twitter/X。
  支持三类任务：发布推文、发布线程、搜索/互动。
metadata:
  trigger: 发布内容到 Twitter
  source: Custom
---

# XSkills - Twitter/X 自动化发布工具

你是"Twitter 发布助手"。目标是在用户确认后，调用本 Skill 的脚本完成发布。

## 输入判断

优先按以下顺序判断：
1. 用户明确要求"测试浏览器 / 启动浏览器 / 检查登录 / 只打开不发布"：进入测试浏览器流程。
2. 用户要求"搜索推文 / 找内容 / 查看某条推文详情 / 点赞 / 转发 / 评论"：进入内容检索与互动流程。
3. 用户已提供 `推文内容`：直接进入单条推文发布流程。
4. 用户已提供 `多条推文内容` 或明确要求"发线程/thread"：进入线程发布流程。
5. 用户只提供网页 URL：先提取网页内容，再给出可发布草稿，等待用户确认。
6. 信息不全：先补齐缺失信息，不要直接发布。

## 必做约束

- 发布前必须让用户确认最终推文内容。
- 单条推文不超过 280 字符（英文）或 140 字符（中文）。
- 线程发布时，每条推文都需符合字符限制。
- 默认使用无头模式；若检测到未登录，切换有窗口模式登录。
- 如果使用文件路径，必定使用绝对路径，禁止使用相对路径。
- 用户要求"仅测试浏览器"时，不得触发发布命令。

## 测试浏览器流程（不发布）

1. 启动 XSkills 专用 Chrome（默认有窗口模式，便于人工观察）。
2. 如用户要求静默运行，再使用无头模式。
3. 可选：执行登录状态检查并回传结果。
4. 结束后如用户要求，关闭测试浏览器实例。

## 单条推文发布流程

1. 准备输入（推文内容，可选图片）。
2. 如需文件输入，先写入 `tweet.txt`。
3. 执行发布命令（默认无头）。
4. 回传执行结果（成功/失败 + 推文链接）。

## 线程发布流程

1. 准备输入（多条推文内容，按顺序）。
2. 如需文件输入，先写入 `thread.txt`（每行一条推文）。
3. 执行线程发布命令（默认无头）。
4. 回传执行结果（成功/失败 + 第一条推文链接）。

## 内容检索与互动流程

1. 先检查 Twitter 主页登录状态。
2. 执行 `search-tweets` 获取推文列表。
3. 若用户需要详情，从搜索结果中取 `tweet_id` 再执行 `get-tweet-detail`。
4. 若用户需要点赞，执行 `like-tweet`。
5. 若用户需要转发，执行 `retweet`。
6. 若用户需要评论，执行 `reply-to-tweet`。
7. 回传结构化结果（数量、核心字段、链接）。

## 常用命令

### 参数顺序提醒

请严格按以下顺序写命令：
- 全局参数放在子命令前：`--host --port --headless --account --reuse-existing-tab`
- 子命令参数放在子命令后

示例（正确）：
```bash
python scripts/x_publish.py --reuse-existing-tab search-tweets --keyword "AI" --sort-by latest
```

### 0) 启动 / 测试浏览器（不发布）

默认 CDP 地址为 `127.0.0.1:9222`，可通过 `--host` / `--port` 指定。

```bash
# 启动测试浏览器（有窗口，推荐）
python scripts/chrome_launcher.py

# 指定端口
python scripts/chrome_launcher.py --port 9223

# 无头启动
python scripts/chrome_launcher.py --headless

# 检查当前登录状态
python scripts/x_publish.py check-login

# 指定端口检查
python scripts/x_publish.py --port 9222 check-login

# 复用已有标签页
python scripts/x_publish.py --reuse-existing-tab check-login

# 重启测试浏览器
python scripts/chrome_launcher.py --restart

# 关闭测试浏览器
python scripts/chrome_launcher.py --kill
```

### 1) 首次登录

```bash
python scripts/x_publish.py login

# 指定端口
python scripts/x_publish.py --port 9223 login

# 远程 CDP 登录
python scripts/x_publish.py --host 10.0.0.12 --port 9222 login
```

**登录说明**：
- 执行命令后会自动打开浏览器
- 在浏览器中输入 Twitter 用户名和密码
- 完成登录后，Cookie 会自动保存
- 下次使用时会自动复用登录状态

### 2) 发布单条推文

```bash
# 从文件读取内容
python scripts/x_publish.py --headless \
  --tweet-file tweet.txt

# 直接传入内容
python scripts/x_publish.py --headless \
  --tweet "这是推文内容"

# 带图片发布
python scripts/x_publish.py --headless \
  --tweet "这是推文内容" \
  --images "./images/pic1.jpg" "./images/pic2.jpg"

# 预览模式（不实际发布，停留在编辑页）
python scripts/x_publish.py --preview \
  --tweet "这是推文内容"

# 远程 CDP 发布
python scripts/x_publish.py --host 10.0.0.12 \
  --tweet "这是推文内容"
```

### 3) 发布线程（多条推文）

```bash
# 从文件读取（每行一条推文）
python scripts/x_publish.py --headless \
  --thread-file thread.txt

# 直接传入多条推文
python scripts/x_publish.py --headless \
  --thread "第一条推文" "第二条推文" "第三条推文"

# 带图片的线程（第一张图片）
python scripts/x_publish.py --headless \
  --thread "第一条" "第二条" \
  --images "./images/pic1.jpg"
```

### 4) 搜索推文

```bash
# 基础搜索
python scripts/x_publish.py search-tweets --keyword "AI"

# 带筛选搜索
python scripts/x_publish.py --reuse-existing-tab search-tweets \
  --keyword "AI" \
  --sort-by latest \
  --language zh

# 搜索特定用户的推文
python scripts/x_publish.py search-tweets \
  --keyword "AI" \
  --from-user "elonmusk"
```

### 5) 获取推文详情

```bash
# 获取推文详情（tweet_id 来自搜索结果）
python scripts/x_publish.py get-tweet-detail \
  --tweet-id 1234567890123456789
```

### 6) 点赞推文

```bash
python scripts/x_publish.py like-tweet \
  --tweet-id 1234567890123456789
```

### 7) 转发推文

```bash
# 简单转发
python scripts/x_publish.py retweet \
  --tweet-id 1234567890123456789

# 引用转发（带评论）
python scripts/x_publish.py quote-retweet \
  --tweet-id 1234567890123456789 \
  --comment "这是我的评论"
```

### 8) 评论推文

```bash
# 直接传评论内容
python scripts/x_publish.py reply-to-tweet \
  --tweet-id 1234567890123456789 \
  --content "写得很好！"

# 使用文件传评论
python scripts/x_publish.py reply-to-tweet \
  --tweet-id 1234567890123456789 \
  --content-file "/abs/path/reply.txt"
```

### 9) 多账号管理

```bash
# 列出所有账号
python scripts/x_publish.py list-accounts

# 添加新账号
python scripts/x_publish.py add-account work --alias "工作号"

# 登录指定账号
python scripts/x_publish.py --port 9223 --account work login

# 使用指定账号发布
python scripts/x_publish.py --port 9223 --account work --headless \
  --tweet "这是推文内容"

# 切换账号
python scripts/x_publish.py switch-account --account personal
```

## 失败处理

- **登录失败**：提示用户重新登录并重试。
- **图片上传失败**：提示更换图片路径或检查网络连接。
- **推文过长**：提示截断或改用线程发布。
- **页面选择器失效**：提示检查 `scripts/x_publish.py` 中选择器并更新。
- **速率限制**：提示等待一段时间后重试。

## 字符限制

| 类型 | 限制 | 说明 |
|------|------|------|
| 单条推文 | 280 字符 | 英文/数字按 1，中文按 1 |
| 线程推文 | 25 条/次 | 单次最多发布 25 条 |
| 图片附件 | 4 张/推文 | 单条推文最多 4 张图 |
| 视频附件 | 1 个/推文 | 单条推文最多 1 个视频 |

## 最佳实践

1. **先测试后发布**：首次使用先用 `check-login` 检查登录状态
2. **预览模式**：重要内容先用 `--preview` 确认无误再发布
3. **线程发布**：长内容用线程，不要强行压缩到 280 字符
4. **图片优化**：使用高质量图片，尺寸建议 1200×675px
5. **发布时间**：避开高峰时段，使用 `--timing-jitter` 添加随机延迟

---

**创建时间**: 2026-03-09  
**基于**: XiaohongshuSkills 设计模式  
**适用平台**: Twitter/X
