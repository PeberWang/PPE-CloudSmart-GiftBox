#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# 切换到项目目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 读取技术方案文档
try:
    with open("docs/plan/PPE云端智能大礼包技术方案 v4.0.md", "r", encoding="utf-8") as f:
        content = f.read()
        print("=== PPE云端智能大礼包技术方案 v4.0 ===")
        print(content)
except FileNotFoundError:
    print("文件不存在，尝试读取v3.0...")
    try:
        with open("docs/plan/PPE云端智能大礼包技术方案 v3.0.md", "r", encoding="utf-8") as f:
            content = f.read()
            print("=== PPE云端智能大礼包技术方案 v3.0 ===")
            print(content)
    except FileNotFoundError as e:
        print(f"文件未找到: {e}")
except Exception as e:
    print(f"读取文件出错: {e}")