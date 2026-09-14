#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按教师名单批量生成统一的教学目录结构。

用法：
    1. 在下面的"教师名单"中填写教师姓名与所授课程；
    2. 在本文件所在目录运行：  python3 生成教师档案.py
    3. 生成结果：教师教学档案/<教师姓名>/<学年学期>_<课程名称>/…

模板来源：教师教学档案/_模板（一名教师·一门课程·一个学期的空白结构）。
程序会复制模板并把 {{教师姓名}}、{{课程名称}}、{{学年学期}} 替换为实际值。
已存在的目标目录不会被覆盖。
"""

import shutil
import sys
from pathlib import Path

# ── 配置区（只改这里）────────────────────────────────────────────────

学年学期 = "2025-2026学年第1学期"

教师名单 = {
    # "教师姓名": ["课程1", "课程2"],
    # 示例：
    # "张三": ["内科学", "诊断学"],
    # "李四": ["外科学"],
}

# ── 以下一般不需要修改 ───────────────────────────────────────────────

根目录 = Path(__file__).resolve().parent / "教师教学档案"
模板目录 = 根目录 / "_模板"
占位符 = ("{{教师姓名}}", "{{课程名称}}", "{{学年学期}}")
忽略文件 = shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc")


def 校验模板() -> None:
    if not 模板目录.is_dir():
        sys.exit(f"找不到模板目录：{模板目录}")
    if not (模板目录 / "README.md").is_file():
        sys.exit(f"模板目录不完整，缺少 README.md：{模板目录}")


def 替换占位符(目标: Path, 教师: str, 课程: str) -> int:
    次数 = 0
    for 文件 in 目标.rglob("*"):
        if not 文件.is_file() or 文件.suffix.lower() not in {".md", ".txt", ".csv"}:
            continue
        原文 = 文件.read_text(encoding="utf-8")
        新文 = 原文
        for 旧, 新值 in zip(占位符, (教师, 课程, 学年学期)):
            if 旧 in 新文:
                次数 += 新文.count(旧)
                新文 = 新文.replace(旧, 新值)
        if 新文 != 原文:
            文件.write_text(新文, encoding="utf-8")
    return 次数


def 生成(教师: str, 课程: str) -> None:
    目标 = 根目录 / 教师 / f"{学年学期}_{课程}"
    if 目标.exists():
        print(f"  跳过（已存在）：{目标.relative_to(根目录)}")
        return
    shutil.copytree(模板目录, 目标, ignore=忽略文件)
    次数 = 替换占位符(目标, 教师, 课程)
    print(f"  已生成：{目标.relative_to(根目录)}（替换占位符 {次数} 处）")


def main() -> None:
    校验模板()
    if not 教师名单:
        print("尚未填写『教师名单』，以下为填写示例：\n")
        print('    教师名单 = {')
        print('        "张三": ["内科学", "诊断学"],')
        print('        "李四": ["外科学"],')
        print('    }\n')
        print(f"模板已就绪，可手工复制：{模板目录.relative_to(根目录.parent)}")
        return

    print(f"学年学期：{学年学期}")
    总数 = 0
    for 教师, 课程列表 in 教师名单.items():
        print(f"{教师}：")
        for 课程 in 课程列表:
            生成(教师, 课程)
            总数 += 1
    print(f"\n完成，共 {总数} 套课程教学档案（结构与 _模板 一致）。")


if __name__ == "__main__":
    main()
