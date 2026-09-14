#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把模板里的 说明.md 单向同步到各目录（模板为唯一来源）。

用法（在 0目录结构/ 下运行）：
    python3 同步说明.py --check         只报告差异，不改任何文件
    python3 同步说明.py                 同步：写入缺失的、更新未被手工改动的
    python3 同步说明.py --force         连手工改动过的也一并覆盖
    python3 同步说明.py --diff 目录     先看某个目录的差异再决定

四态判断（依据 0目录结构/.说明同步记录.json 中上次写入内容的哈希）：
    缺失       本地没有 说明.md                    → 同步时写入
    一致       本地 = 模板当前内容                  → 不动
    待更新     本地 = 上次同步写入的内容（未动过）  → 同步时覆盖
    手工改过   本地既不是模板内容、也不是上次写入   → **跳过并报告**，除非 --force

来源（模板）：0目录结构/教师教学档案/_模板/<目录>/说明.md
去向（本地）：<上层目录>/<目录>/说明.md
写入本地时会去掉指向 00_材料总清点表.md 的半句链接（本地目录没有该文件）。
"""

import argparse
import difflib
import hashlib
import json
import sys
from pathlib import Path

项目 = Path(__file__).resolve().parent
模板 = 项目 / "教师教学档案" / "_模板"
上层 = 项目.parent
记录文件 = 项目 / ".说明同步记录.json"
例外目录 = {"0目录结构", "9_仅临床课程"}


def 本地版(正文: str) -> str:
    return 正文.replace("；学期末自查用 [00_材料总清点表.md](../00_材料总清点表.md)", "")


def 摘要(正文: str) -> str:
    return hashlib.sha256(正文.encode("utf-8")).hexdigest()[:16]


def 读记录() -> dict:
    if 记录文件.is_file():
        try:
            return json.loads(记录文件.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"提示：{记录文件.name} 无法解析，按空记录处理")
    return {}


def 写记录(记录: dict) -> None:
    记录文件.write_text(json.dumps(记录, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")


def 目录列表() -> list[str]:
    if not 模板.is_dir():
        sys.exit(f"找不到模板目录：{模板}")
    return sorted(d.name for d in 模板.iterdir()
                  if d.is_dir() and d.name not in 例外目录 and (d / "说明.md").is_file())


def 模板正文(名称: str) -> str:
    return 本地版((模板 / 名称 / "说明.md").read_text(encoding="utf-8"))


def 判断(名称: str, 记录: dict) -> str:
    目标 = 上层 / 名称 / "说明.md"
    if not 目标.exists():
        return "缺失"
    现在 = 目标.read_text(encoding="utf-8")
    期望 = 模板正文(名称)
    if 现在 == 期望:
        return "一致"
    上次 = 记录.get(名称, {}).get("本地哈希")
    if 上次 and 摘要(现在) == 上次:
        return "待更新"
    return "手工改过"


def 写入(名称: str, 记录: dict) -> None:
    正文 = 模板正文(名称)
    目标 = 上层 / 名称 / "说明.md"
    目标.parent.mkdir(parents=True, exist_ok=True)
    目标.write_text(正文, encoding="utf-8")
    记录[名称] = {"本地哈希": 摘要(正文), "模板哈希": 摘要((模板 / 名称 / "说明.md").read_text(encoding="utf-8"))}


def main() -> None:
    p = argparse.ArgumentParser(description="把模板 说明.md 单向同步到各目录")
    p.add_argument("--check", action="store_true", help="只检查并报告，不改文件")
    p.add_argument("--force", action="store_true", help="手工改过的也覆盖")
    p.add_argument("--diff", metavar="目录", help="显示指定目录的差异后退出")
    参数 = p.parse_args()

    记录 = 读记录()
    目录们 = 目录列表()
    if not 目录们:
        sys.exit("模板里没有可同步的目录")

    if 参数.diff:
        if 参数.diff not in 目录们:
            sys.exit(f"模板中没有 {参数.diff}")
        目标 = 上层 / 参数.diff / "说明.md"
        现在 = 目标.read_text(encoding="utf-8") if 目标.exists() else ""
        差异 = list(difflib.unified_diff(现在.splitlines(), 模板正文(参数.diff).splitlines(),
                                        f"本地 {参数.diff}/说明.md（现状）", "同步后", lineterm="", n=1))
        print("\n".join(差异) if 差异 else "两者内容一致，无需同步")
        return

    print(f"模板：{模板.relative_to(上层)}")
    print(f"本地：{上层.name}/（{len(目录们)} 个目录）\n")

    分类: dict[str, list[str]] = {"一致": [], "缺失": [], "待更新": [], "手工改过": []}
    for 名 in 目录们:
        分类[判断(名, 记录)].append(名)

    for 状态 in ("一致", "缺失", "待更新", "手工改过"):
        print(f"  {状态:<8}{len(分类[状态]):>3}   {', '.join(分类[状态]) or '—'}")

    if 参数.check:
        print(f"\n（--check 模式，未改动任何文件；记录文件：{记录文件.name}）")
        return

    写入数 = 0
    for 名 in 分类["缺失"] + 分类["待更新"]:
        写入(名, 记录); 写入数 += 1
    for 名 in 分类["一致"]:            # 一致也登记，便于下次判断
        记录.setdefault(名, {})
        记录[名]["本地哈希"] = 摘要((上层 / 名 / "说明.md").read_text(encoding="utf-8"))
        记录[名]["模板哈希"] = 摘要((模板 / 名 / "说明.md").read_text(encoding="utf-8"))
    if 参数.force:
        for 名 in 分类["手工改过"]:
            写入(名, 记录); 写入数 += 1
    写记录(记录)

    print(f"\n已写入 {写入数} 份 说明.md，记录已更新（{记录文件.name}）")
    if 分类["手工改过"] and not 参数.force:
        print(f"跳过 {len(分类['手工改过'])} 份手工改动过的：{', '.join(分类['手工改过'])}")
        print("  看差异：python3 同步说明.py --diff <目录>   强制覆盖：--force")


if __name__ == "__main__":
    main()
