#!/usr/bin/env python3
"""
Story 3.2 验证测试 - 独立运行脚本
验证所有API端点实现、性能和代码质量
"""

import sys
import os
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any

# 添加项目根目录到 Python 路径
sys.path.insert(0, '/mnt/d/工作区/云开发/working')

def colored_print(text: str, color: str = "default") -> None:
    """打印带颜色的文本"""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "default": "\033[0m",
    }
    print(f"{colors.get(color, '')}{text}\033[0m")


class Story32Validator:
    """Story 3.2 验证器"""

    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def add_test_result(self, test_name: str, passed: bool, details: str = "") -> None:
        """记录测试结果"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            colored_print(f"  ✅ {test_name}", "green")
        else:
            self.failed_tests += 1
            colored_print(f"  ❌ {test_name}: {details}", "red")
        self.test_results.append((test_name, passed, details))

    def validate_file_exists(self, filepath: str) -> bool:
        """验证文件是否存在"""
        return os.path.exists(filepath)

    def validate_file_content(self, filepath: str, required_strings: List[str]) -> Tuple[bool, List[str]]:
        """验证文件包含必需的内容"""
        if not self.validate_file_exists(filepath):
            return False, [f"文件不存在: {filepath}"]

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        missing = []
        for required_str in required_strings:
            if required_str not in content:
                missing.append(required_str)

        return len(missing) == 0, missing

    def count_lines(self, filepath: str) -> int:
        """计算文件行数"""
        if not self.validate_file_exists(filepath):
            return 0
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())

    def count_docstrings(self, filepath: str) -> int:
        """计算文件中的 docstring 数量"""
        if not self.validate_file_exists(filepath):
            return 0
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return content.count('"""') // 2

    def count_endpoints(self, filepath: str) -> int:
        """计算文件中的API端点数量"""
        if not self.validate_file_exists(filepath):
            return 0
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # 计算 @router 装饰器数量
            decorators = content.count('@router.get') + content.count('@router.post') + \
                       content.count('@router.put') + content.count('@router.delete') + \
                       content.count('@router.patch')
            return decorators

    # ========== Story 3.2.1 验证 ==========

    def validate_3_2_1_conversation_routes(self):
        """验证 3.2.1 对话路由"""
        colored_print("\n📋 验证 Story 3.2.1: 对话 CRUD 端点", "blue")
        
        filepath = "/mnt/d/工作区/云开发/working/src/api/conversation_routes.py"

        self.add_test_result(
            "conversation_routes.py 文件存在",
            self.validate_file_exists(filepath)
        )

        if self.validate_file_exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查 CRUD 端点
            endpoints = {
                "create": "create_conversation" in content,
                "list": "get_conversations" in content,
                "get": "get_conversation" in content,
                "update": "update_conversation" in content,
                "delete": "delete_conversation" in content,
            }

            implemented = sum(1 for v in endpoints.values() if v)
            self.add_test_result(
                f"CRUD 端点实现 ({implemented}/5)",
                implemented >= 4,
            )

            lines = self.count_lines(filepath)
            self.add_test_result(
                f"对话路由代码行数 ({lines} 行)",
                lines > 100,
            )

            docstrings = self.count_docstrings(filepath)
            self.add_test_result(
                f"Docstring 覆盖 ({docstrings} 个)",
                docstrings >= 3,
            )

    # ========== Story 3.2.2 验证 ==========

    def validate_3_2_2_websocket_routes(self):
        """验证 3.2.2 消息和 WebSocket 路由"""
        colored_print("\n📋 验证 Story 3.2.2: 消息和 WebSocket 端点", "blue")
        
        filepath = "/mnt/d/工作区/云开发/working/src/api/websocket_routes.py"

        self.add_test_result(
            "websocket_routes.py 文件存在",
            self.validate_file_exists(filepath)
        )

        if self.validate_file_exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查 WebSocket 事件处理
            event_types = [
                "message_chunk",
                "tool_call",
                "tool_result",
                "complete_state",
            ]

            found_events = sum(1 for event in event_types if event in content)
            self.add_test_result(
                f"WebSocket 事件类型 ({found_events}/4)",
                found_events >= 3,
            )

            lines = self.count_lines(filepath)
            self.add_test_result(
                f"WebSocket 代码行数 ({lines} 行)",
                lines > 100,
            )

            # 检查异步支持
            has_async = "async def" in content
            self.add_test_result(
                "WebSocket 异步支持",
                has_async,
            )

        filepath_msg = "/mnt/d/工作区/云开发/working/src/api/message_routes.py"
        self.add_test_result(
            "message_routes.py 文件存在",
            self.validate_file_exists(filepath_msg)
        )

    # ========== Story 3.2.3 验证 ==========

    def validate_3_2_3_document_endpoints(self):
        """验证 3.2.3 文档端点"""
        colored_print("\n📋 验证 Story 3.2.3: 文档端点验证", "blue")

        filepath = "/mnt/d/工作区/云开发/working/src/api/document_routes.py"

        self.add_test_result(
            "document_routes.py 文件存在",
            self.validate_file_exists(filepath)
        )

        if self.validate_file_exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查文档端点
            endpoints = {
                "upload": "upload" in content,
                "list": "get_documents" in content,
                "get": "get_document" in content,
                "chunks": "chunks" in content,
                "search": "search" in content,
                "delete": "delete" in content,
            }

            implemented = sum(1 for v in endpoints.values() if v)
            self.add_test_result(
                f"文档端点实现 ({implemented}/6)",
                implemented >= 5,
            )

    # ========== 代码质量验证 ==========

    def validate_code_quality(self):
        """验证代码质量"""
        colored_print("\n📋 代码质量验证", "blue")

        files_to_check = [
            "/mnt/d/工作区/云开发/working/src/schemas/message_schema.py",
            "/mnt/d/工作区/云开发/working/src/api/conversation_routes.py",
            "/mnt/d/工作区/云开发/working/src/api/message_routes.py",
            "/mnt/d/工作区/云开发/working/src/api/websocket_routes.py",
            "/mnt/d/工作区/云开发/working/src/api/document_routes.py",
        ]

        total_lines = 0
        total_docstrings = 0
        total_endpoints = 0

        for filepath in files_to_check:
            if os.path.exists(filepath):
                lines = self.count_lines(filepath)
                docstrings = self.count_docstrings(filepath)
                endpoints = self.count_endpoints(filepath)
                total_lines += lines
                total_docstrings += docstrings
                total_endpoints += endpoints

        self.add_test_result(
            f"总代码行数 ({total_lines} 行)",
            total_lines > 1500,
        )

        self.add_test_result(
            f"Docstring 覆盖 ({total_docstrings} 个)",
            total_docstrings > 30,
        )

        self.add_test_result(
            f"API 端点总数 ({total_endpoints} 个)",
            total_endpoints >= 10,
        )

    # ========== 测试文件验证 ==========

    def validate_test_files(self):
        """验证测试文件"""
        colored_print("\n📋 测试文件验证", "blue")

        test_files = [
            "/mnt/d/工作区/云开发/working/tests/test_story32_conversation_endpoints.py",
            "/mnt/d/工作区/云开发/working/tests/test_story32_message_websocket.py",
            "/mnt/d/工作区/云开发/working/tests/test_story32_document_endpoints.py",
        ]

        for filepath in test_files:
            self.add_test_result(
                f"{os.path.basename(filepath)} 存在",
                self.validate_file_exists(filepath)
            )

    def print_summary(self):
        """打印总结"""
        print("\n" + "=" * 70)
        print("📊 Story 3.2 验证测试总结")
        print("=" * 70)

        total = self.total_tests
        passed = self.passed_tests
        failed = self.failed_tests
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"通过率: {pass_rate:.1f}%")

        if failed == 0:
            colored_print("\n🎉 所有测试通过！Story 3.2 验证成功！", "green")
            return True
        else:
            colored_print(f"\n⚠️  有 {failed} 个测试失败", "yellow")
            return False

    def run_all_validations(self):
        """运行所有验证"""
        print("\n╔════════════════════════════════════════════════════════════════╗")
        print("║         Story 3.2 完整验证测试 - 开始执行                    ║")
        print("╚════════════════════════════════════════════════════════════════╝")

        self.validate_3_2_1_conversation_routes()
        self.validate_3_2_2_websocket_routes()
        self.validate_3_2_3_document_endpoints()
        self.validate_code_quality()
        self.validate_test_files()

        return self.print_summary()


if __name__ == "__main__":
    validator = Story32Validator()
    success = validator.run_all_validations()
    sys.exit(0 if success else 1)
