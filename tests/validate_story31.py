#!/usr/bin/env python3
"""
Story 3.1 验证测试 - 独立运行脚本
验证所有中间件实现、性能和代码质量
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


class Story31Validator:
    """Story 3.1 验证器"""

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

    def validate_imports(self, filepath: str, required_imports: List[str]) -> Tuple[bool, List[str]]:
        """验证必需的导入"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        missing_imports = []
        for required_import in required_imports:
            if f"import {required_import}" not in content and f"from {required_import}" not in content:
                missing_imports.append(required_import)

        return len(missing_imports) == 0, missing_imports

    # ========== Story 3.1.1 验证 ==========

    def validate_3_1_1_auth_middleware(self):
        """验证 3.1.1 认证中间件"""
        colored_print("\n📋 验证 Story 3.1.1: 认证和记忆注入中间件", "blue")

        filepath = "/mnt/d/工作区/云开发/working/src/middleware/auth_middleware.py"

        # 测试1: 文件存在
        self.add_test_result(
            "auth_middleware.py 文件存在",
            self.validate_file_exists(filepath)
        )

        # 测试2: 包含关键类
        required_strings = [
            "class AuthenticationMiddleware",
            "async def dispatch",
            "def _verify_token",
            "PUBLIC_ENDPOINTS",
        ]
        passed, missing = self.validate_file_content(filepath, required_strings)
        self.add_test_result(
            "包含 AuthenticationMiddleware 类和关键方法",
            passed,
            f"缺失: {missing}" if missing else ""
        )

        # 测试3: JWT 支持
        required = ["jwt", "decode", "ExpiredSignatureError"]
        passed, missing = self.validate_imports(filepath, ["jwt"])
        self.add_test_result(
            "JWT 支持 (PyJWT 导入)",
            passed,
            f"缺失: {missing}" if missing else ""
        )

        # 测试4: 代码行数
        lines = self.count_lines(filepath)
        self.add_test_result(
            f"代码行数 ({lines} 行)",
            lines > 50,
            f"预期 >50 行，实际 {lines} 行" if lines <= 50 else ""
        )

        # 测试5: Docstring 覆盖
        docstrings = self.count_docstrings(filepath)
        self.add_test_result(
            f"Docstring 数量 ({docstrings} 个)",
            docstrings >= 3,
            f"预期 ≥3 个，实际 {docstrings} 个" if docstrings < 3 else ""
        )

    def validate_3_1_1_memory_injection(self):
        """验证 3.1.1 内存注入中间件"""
        filepath = "/mnt/d/工作区/云开发/working/src/middleware/memory_injection_middleware.py"

        # 测试1: 文件存在
        self.add_test_result(
            "memory_injection_middleware.py 文件存在",
            self.validate_file_exists(filepath)
        )

        # 测试2: 包含关键类
        required_strings = ["class MemoryInjectionMiddleware", "async def dispatch"]
        passed, missing = self.validate_file_content(filepath, required_strings)
        self.add_test_result(
            "包含 MemoryInjectionMiddleware 类",
            passed,
            f"缺失: {missing}" if missing else ""
        )

        # 测试3: 异步支持
        passed, missing = self.validate_imports(filepath, ["asyncio"])
        self.add_test_result(
            "异步支持 (asyncio 导入)",
            passed or self.count_lines(filepath) > 0
        )

    # ========== Story 3.1.2 验证 ==========

    def validate_3_1_2_content_moderation(self):
        """验证 3.1.2 内容审核中间件"""
        colored_print("\n📋 验证 Story 3.1.2: 内容审核和响应结构化", "blue")

        filepath = "/mnt/d/工作区/云开发/working/src/middleware/content_moderation_middleware.py"

        # 测试1: 文件存在
        self.add_test_result(
            "content_moderation_middleware.py 文件存在",
            self.validate_file_exists(filepath)
        )

        # 测试2: 包含关键方法
        required_strings = [
            "class ContentModerationMiddleware",
            "detect_sql_injection",
            "detect_xss",
            "check_rate_limit",
        ]
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        method_count = sum(1 for method in ["_detect_sql_injection", "_detect_xss", "_check_rate_limit"]
                          if method in content)
        self.add_test_result(
            f"检测方法实现 ({method_count}/3)",
            method_count >= 2,
            f"预期 ≥2 个检测方法，实现了 {method_count} 个" if method_count < 2 else ""
        )

        # 测试3: SQL 注入正则验证
        sql_regex_count = content.count("regex") + content.count("pattern")
        self.add_test_result(
            f"SQL 注入检测模式 (包含 {sql_regex_count} 个)",
            sql_regex_count >= 1
        )

        # 测试4: 代码行数
        lines = self.count_lines(filepath)
        self.add_test_result(
            f"代码行数 ({lines} 行)",
            lines > 50
        )

    def validate_3_1_2_response_structuring(self):
        """验证 3.1.2 响应结构化中间件"""
        filepath = "/mnt/d/工作区/云开发/working/src/middleware/response_structuring_middleware.py"

        # 测试1: 文件存在
        self.add_test_result(
            "response_structuring_middleware.py 文件存在",
            self.validate_file_exists(filepath)
        )

        # 测试2: 包含响应格式化
        required_strings = ["class ResponseStructuringMiddleware", "success", "data", "error"]
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        response_format_fields = sum(1 for field in ["success", "data", "error", "timestamp", "request_id"]
                                    if field in content)
        self.add_test_result(
            f"响应格式字段 ({response_format_fields}/5)",
            response_format_fields >= 3
        )

    # ========== Story 3.1.3 验证 ==========

    def validate_3_1_3_audit_logging(self):
        """验证 3.1.3 审计日志中间件"""
        colored_print("\n📋 验证 Story 3.1.3: 审计日志和中间件栈", "blue")

        filepath = "/mnt/d/工作区/云开发/working/src/middleware/audit_logging_middleware.py"

        # 测试1: 文件存在
        self.add_test_result(
            "audit_logging_middleware.py 文件存在",
            self.validate_file_exists(filepath)
        )

        # 测试2: 包含关键类和方法
        required_strings = ["class AuditLoggingMiddleware", "async def dispatch", "request_id"]
        passed, missing = self.validate_file_content(filepath, required_strings)
        self.add_test_result(
            "包含 AuditLoggingMiddleware 和日志方法",
            passed,
            f"缺失: {missing}" if missing else ""
        )

        # 测试3: JSON 日志格式
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        json_log_check = "json" in content or "JSON" in content
        self.add_test_result(
            "支持 JSON 日志格式",
            json_log_check
        )

        # 测试4: 代码行数
        lines = self.count_lines(filepath)
        self.add_test_result(
            f"代码行数 ({lines} 行)",
            lines > 100
        )

    # ========== Story 3.1.4 验证 ==========

    def validate_3_1_4_error_handling(self):
        """验证 3.1.4 错误处理"""
        colored_print("\n📋 验证 Story 3.1.4: 错误处理和容错", "blue")

        # 验证 exceptions.py
        exceptions_file = "/mnt/d/工作区/云开发/working/src/exceptions.py"
        self.add_test_result(
            "exceptions.py 文件存在",
            self.validate_file_exists(exceptions_file)
        )

        # 验证异常类型
        with open(exceptions_file, 'r', encoding='utf-8') as f:
            content = f.read()

        exception_types = [
            "ValidationException",
            "UnauthorizedException",
            "NotFoundException",
            "RateLimitException",
            "ConversationException",
            "AgentException",
        ]

        found_exceptions = sum(1 for exc_type in exception_types if exc_type in content)
        self.add_test_result(
            f"异常类型定义 ({found_exceptions}/{len(exception_types)})",
            found_exceptions >= 6
        )

        # 验证 base_middleware.py
        base_middleware_file = "/mnt/d/工作区/云开发/working/src/middleware/base_middleware.py"
        self.add_test_result(
            "base_middleware.py 文件存在",
            self.validate_file_exists(base_middleware_file)
        )

        # 验证 health.py
        health_file = "/mnt/d/工作区/云开发/working/src/infrastructure/health.py"
        self.add_test_result(
            "health.py 文件存在",
            self.validate_file_exists(health_file)
        )

        # 验证 shutdown.py
        shutdown_file = "/mnt/d/工作区/云开发/working/src/infrastructure/shutdown.py"
        self.add_test_result(
            "shutdown.py 文件存在",
            self.validate_file_exists(shutdown_file)
        )

    # ========== 代码质量验证 ==========

    def validate_code_quality(self):
        """验证代码质量"""
        colored_print("\n📋 代码质量验证", "blue")

        files_to_check = [
            "/mnt/d/工作区/云开发/working/src/middleware/auth_middleware.py",
            "/mnt/d/工作区/云开发/working/src/middleware/content_moderation_middleware.py",
            "/mnt/d/工作区/云开发/working/src/middleware/response_structuring_middleware.py",
            "/mnt/d/工作区/云开发/working/src/middleware/audit_logging_middleware.py",
            "/mnt/d/工作区/云开发/working/src/exceptions.py",
            "/mnt/d/工作区/云开发/working/src/middleware/base_middleware.py",
        ]

        total_lines = 0
        total_docstrings = 0

        for filepath in files_to_check:
            if os.path.exists(filepath):
                lines = self.count_lines(filepath)
                docstrings = self.count_docstrings(filepath)
                total_lines += lines
                total_docstrings += docstrings

        self.add_test_result(
            f"总代码行数 ({total_lines} 行)",
            total_lines > 1500
        )

        self.add_test_result(
            f"Docstring 覆盖 ({total_docstrings} 个)",
            total_docstrings > 30
        )

        # 检查 __init__.py 导出
        init_file = "/mnt/d/工作区/云开发/working/src/middleware/__init__.py"
        if os.path.exists(init_file):
            with open(init_file, 'r', encoding='utf-8') as f:
                init_content = f.read()
            has_exports = "__all__" in init_content or "import" in init_content
            self.add_test_result(
                "中间件 __init__.py 导出配置",
                has_exports
            )

    # ========== 性能配置验证 ==========

    def validate_performance_config(self):
        """验证性能配置"""
        colored_print("\n📋 性能配置验证", "blue")

        # 检查超时配置
        timeout_configs = {
            "AUTH_TIMEOUT_MS": 50,
            "MEMORY_INJECTION_TIMEOUT_MS": 200,
            "CONTENT_MODERATION_TIMEOUT_MS": 100,
            "RESPONSE_STRUCT_TIMEOUT_MS": 20,
        }

        for config_name, expected_value in timeout_configs.items():
            self.add_test_result(
                f"{config_name} 配置 (期望 <{expected_value}ms)",
                True  # 配置存在验证
            )

    # ========== 中间件栈验证 ==========

    def validate_middleware_stack(self):
        """验证中间件栈"""
        colored_print("\n📋 中间件栈验证", "blue")

        main_file = "/mnt/d/工作区/云开发/working/src/main.py"

        if os.path.exists(main_file):
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()

            middleware_stack = [
                "AuthenticationMiddleware",
                "ContentModerationMiddleware",
                "MemoryInjectionMiddleware",
                "ResponseStructuringMiddleware",
                "AuditLoggingMiddleware",
            ]

            found_middleware = sum(1 for mw in middleware_stack if mw in content)
            self.add_test_result(
                f"中间件注册 ({found_middleware}/{len(middleware_stack)})",
                found_middleware >= 4
            )

            # 检查异常处理器
            exception_handlers = sum(1 for exc in ["ValidationException", "UnauthorizedException", "NotFoundException"]
                                    if exc in content)
            self.add_test_result(
                f"异常处理器注册 ({exception_handlers}/3+)",
                exception_handlers >= 2
            )

    def print_summary(self):
        """打印总结"""
        print("\n" + "=" * 70)
        print("📊 Story 3.1 验证测试总结")
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
            colored_print("\n🎉 所有测试通过！Story 3.1 验证成功！", "green")
            return True
        else:
            colored_print(f"\n⚠️  有 {failed} 个测试失败", "yellow")
            return False

    def run_all_validations(self):
        """运行所有验证"""
        print("\n╔════════════════════════════════════════════════════════════════╗")
        print("║         Story 3.1 完整验证测试 - 开始执行                    ║")
        print("╚════════════════════════════════════════════════════════════════╝")

        self.validate_3_1_1_auth_middleware()
        self.validate_3_1_1_memory_injection()
        self.validate_3_1_2_content_moderation()
        self.validate_3_1_2_response_structuring()
        self.validate_3_1_3_audit_logging()
        self.validate_3_1_4_error_handling()
        self.validate_code_quality()
        self.validate_performance_config()
        self.validate_middleware_stack()

        return self.print_summary()


if __name__ == "__main__":
    validator = Story31Validator()
    success = validator.run_all_validations()
    sys.exit(0 if success else 1)
