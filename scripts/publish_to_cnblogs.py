# -*- coding: utf-8 -*-
"""
博客园自动化发布/更新脚本
- 支持首次发布自动注入 post_id
- 后续修改自动更新已有文章
- 完整保留 Front Matter 结构
"""

import sys
import os
import re
import yaml
import requests
from datetime import datetime, timezone
from pathlib import Path

# ==============================
# 🔑 认证信息（从环境变量读取，安全！）
# ==============================
COOKIE = os.getenv("CNBLOGS_COOKIE")
XSRF_TOKEN = os.getenv("CNBLOGS_XSRF_TOKEN")

if not COOKIE or not XSRF_TOKEN:
    print("❌ 错误：请设置环境变量 CNBLOGS_COOKIE 和 CNBLOGS_XSRF_TOKEN", file=sys.stderr)
    print("提示：从浏览器开发者工具中复制 .Cnblogs.AspNetCore.Cookies 和 XSRF-TOKEN 的值", file=sys.stderr)
    sys.exit(1)


# ==============================
# 📄 解析 Front Matter
# ==============================
def parse_front_matter(content: str):
    lines = content.splitlines()
    if len(lines) < 3 or lines[0] != "---":
        return {}, content

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx == -1:
        return {}, content

    fm_yaml = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1:]).lstrip()

    try:
        meta = yaml.safe_load(fm_yaml) or {}
    except yaml.YAMLError:
        return {}, content

    # 标准化 draft
    if "draft" in meta:
        val = meta["draft"]
        if isinstance(val, str):
            meta["draft"] = val.lower() in ("true", "1", "yes", "on")
        else:
            meta["draft"] = bool(val)
    else:
        meta["draft"] = False

    # 标准化 tags
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    elif not isinstance(tags, list):
        tags = []
    meta["tags"] = [str(t).strip() for t in tags if t]

    return meta, body


# ==============================
# 💾 注入 post_id 到 .md 文件
# ==============================
def inject_post_id_to_file(file_path: Path, post_id: int):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    if not lines or lines[0] != "---":
        content = "\n".join(lines)
        new_fm = f"""---
post_id: {post_id}
---

{content}"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_fm)
        print(f"💾 已创建 Front Matter 并写入 post_id: {post_id}")
        return

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        print("⚠️ Front Matter 格式不完整，跳过注入 post_id", file=sys.stderr)
        return

    has_post_id = any(re.match(r"^\s*post_id\s*:", line) for line in lines[1:end_idx])
    if has_post_id:
        print("ℹ️ post_id 已存在，无需注入")
        return

    lines.insert(end_idx, f"post_id: {post_id}")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"✅ 成功注入 post_id: {post_id} 到 {file_path.name}")


# ==============================
# 🔍 获取已有文章详情
# ==============================
def get_post(post_id: int):
    url = f"https://i.cnblogs.com/api/posts/{post_id}"
    headers = {
        "Cookie": COOKIE,
        "X-XSRF-TOKEN": XSRF_TOKEN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"⚠️ 获取原文失败 (ID={post_id})，状态码: {resp.status_code}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"⚠️ 获取原文异常: {e}", file=sys.stderr)
        return None


# ==============================
# 📡 发送请求（统一 POST /api/posts）
# ==============================
def _send_request(url: str, payload: dict, method: str = "POST"):
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://i.cnblogs.com",
        "Referer": "https://i.cnblogs.com/posts/edit",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": COOKIE,
        "X-XSRF-TOKEN": XSRF_TOKEN,
    }

    resp = requests.request(method, url, headers=headers, json=payload, timeout=30)
    if resp.status_code in (200, 201):
        data = resp.json()
        action = "更新" if "id" in payload and payload["id"] else "发布"
        print(f"✅ {action}成功！ID: {data['id']}")
        print(f"🔗 链接: {data['url']}")
        return data
    else:
        print(f"❌ 请求失败！状态码: {resp.status_code}", file=sys.stderr)
        print(f"响应: {resp.text}", file=sys.stderr)
        resp.raise_for_status()


# ==============================
# 🚀 统一发布/更新函数
# ==============================
def publish_or_update(title: str, content: str, tags: list, is_draft: bool, post_id: int = None):
    url = "https://i.cnblogs.com/api/posts"
    payload = {
        "title": title,
        "postBody": content,
        "isMarkdown": True,
        "isDraft": is_draft,
        "isPublished": not is_draft,
        "postType": 1,
        "accessPermission": 268435456,
        "includeInMainSyndication": True,
        "displayOnHomePage": True,
        "isAllowComments": True,
        "tags": tags,
        "usingEditorId": 5,
    }

    if post_id:
        original = get_post(post_id)
        if not original:
            raise RuntimeError(f"无法获取原文信息，ID: {post_id}")

        payload["id"] = post_id
        # 直接使用原始 datePublished（格式为 "2025-11-22T13:15:00.000Z"）
        if original.get("datePublished"):
            payload["datePublished"] = original["datePublished"]
        # 补充其他字段（非必需，但更贴近浏览器行为）
        for key in ["author", "blogId", "url"]:
            if key in original:
                payload[key] = original[key]

    return _send_request(url, payload, method="POST")


# ==============================
# ▶️ 主程序
# ==============================
def main():
    if len(sys.argv) != 2:
        print("用法: python publish_to_cnblogs.py <笔记文件.md>", file=sys.stderr)
        sys.exit(1)

    md_file = Path(sys.argv[1])
    if not md_file.is_file():
        print(f"❌ 文件不存在: {md_file}", file=sys.stderr)
        sys.exit(1)

    print(f"📖 正在读取: {md_file}")
    with open(md_file, "r", encoding="utf-8") as f:
        raw = f.read()

    meta, body = parse_front_matter(raw)

    title = meta.get("title") or md_file.stem.replace("-", " ").title()
    tags = meta.get("tags", [])
    is_draft = meta.get("draft", False)
    post_id = meta.get("post_id")

    if post_id:
        try:
            post_id = int(post_id)
        except (TypeError, ValueError):
            print(f"⚠️ post_id 格式无效: {post_id}，将作为新文章发布", file=sys.stderr)
            post_id = None

    print(f"📝 标题: {title}")
    print(f"🏷️  标签: {tags}")
    print(f"✏️  草稿模式: {'是' if is_draft else '否'}")

    if post_id:
        print(f"🔄 操作: 更新已有文章 (ID: {post_id})")
        result = publish_or_update(
            title=title, content=body, tags=tags, is_draft=is_draft, post_id=post_id
        )
    else:
        print("🆕 操作: 发布新文章")
        result = publish_or_update(
            title=title, content=body, tags=tags, is_draft=is_draft
        )
        inject_post_id_to_file(md_file, result["id"])


if __name__ == "__main__":
    main()