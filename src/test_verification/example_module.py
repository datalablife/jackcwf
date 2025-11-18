"""
测试验证模块 - 用于验证 CLAUDE 模块文档更新规则的生效

该模块演示了如何创建新的功能模块，CLAUDE 应该在完成后
自动提示执行 /update-module-docs 命令来更新 MODULE_OVERVIEW.md

功能：
- ExampleService: 演示服务类，包含基本的 CRUD 操作
- example_helper(): 辅助函数示例

创建日期: 2025-11-18
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel


class ExampleData(BaseModel):
    """示例数据模型"""
    id: str
    name: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ExampleService:
    """
    示例服务类

    演示如何组织服务层代码，包含基本的数据操作逻辑。

    方法:
        create(data: ExampleData) -> ExampleData
        read(id: str) -> Optional[ExampleData]
        update(id: str, data: ExampleData) -> Optional[ExampleData]
        delete(id: str) -> bool
    """

    def __init__(self):
        """初始化服务"""
        self._storage: Dict[str, ExampleData] = {}

    def create(self, data: ExampleData) -> ExampleData:
        """
        创建新的数据记录

        参数:
            data: 要创建的数据模型

        返回:
            创建的数据记录
        """
        self._storage[data.id] = data
        return data

    def read(self, id: str) -> Optional[ExampleData]:
        """
        读取指定 ID 的数据记录

        参数:
            id: 数据记录的 ID

        返回:
            如果存在则返回数据，否则返回 None
        """
        return self._storage.get(id)

    def update(self, id: str, data: ExampleData) -> Optional[ExampleData]:
        """
        更新指定 ID 的数据记录

        参数:
            id: 数据记录的 ID
            data: 更新后的数据

        返回:
            如果成功则返回更新后的数据，否则返回 None
        """
        if id in self._storage:
            self._storage[id] = data
            return data
        return None

    def delete(self, id: str) -> bool:
        """
        删除指定 ID 的数据记录

        参数:
            id: 要删除的数据记录 ID

        返回:
            如果删除成功返回 True，否则返回 False
        """
        if id in self._storage:
            del self._storage[id]
            return True
        return False


def example_helper(value: str) -> str:
    """
    辅助函数示例

    演示如何编写简单的辅助函数。

    参数:
        value: 输入字符串

    返回:
        处理后的字符串

    示例:
        >>> example_helper("test")
        "test_processed"
    """
    return f"{value}_processed"


# 使用示例（仅用于演示，不在生产环境使用）
if __name__ == "__main__":
    # 创建服务实例
    service = ExampleService()

    # 创建数据
    data = ExampleData(id="1", name="Example", description="Test data")
    created = service.create(data)
    print(f"Created: {created}")

    # 读取数据
    read_data = service.read("1")
    print(f"Read: {read_data}")

    # 使用辅助函数
    result = example_helper("hello")
    print(f"Helper result: {result}")
