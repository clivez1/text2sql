"""
权限控制模块测试
"""
import pytest
from app.core.auth.permission import (
    PermissionLevel,
    TablePermission,
    UserContext,
    PermissionManager,
    get_permission_manager,
    check_table_access,
    filter_sensitive_columns,
)


class TestPermissionLevel:
    """权限级别测试"""
    
    def test_permission_levels_exist(self):
        """测试权限级别存在"""
        assert PermissionLevel.READ_ONLY.value == "read_only"
        assert PermissionLevel.READ_WRITE.value == "read_write"
        assert PermissionLevel.ADMIN.value == "admin"


class TestTablePermission:
    """表权限测试"""
    
    def test_create_table_permission(self):
        """测试创建表权限"""
        perm = TablePermission(
            table_name="orders",
            permission_level=PermissionLevel.READ_ONLY,
        )
        
        assert perm.table_name == "orders"
        assert perm.permission_level == PermissionLevel.READ_ONLY
    
    def test_is_column_allowed(self):
        """测试列权限检查"""
        perm = TablePermission(
            table_name="users",
            denied_columns={"password", "secret"},
        )
        
        assert perm.is_column_allowed("name") is True
        assert perm.is_column_allowed("password") is False
    
    def test_get_allowed_columns(self):
        """测试获取允许的列"""
        perm = TablePermission(
            table_name="users",
            denied_columns={"password"},
        )
        
        all_columns = ["id", "name", "email", "password"]
        allowed = perm.get_allowed_columns(all_columns)
        
        assert "password" not in allowed
        assert "id" in allowed


class TestUserContext:
    """用户上下文测试"""
    
    def test_create_user_context(self):
        """测试创建用户上下文"""
        ctx = UserContext(
            user_id="test_user",
            roles={"analyst", "viewer"},
        )
        
        assert ctx.user_id == "test_user"
        assert ctx.has_role("analyst") is True
    
    def test_has_role(self):
        """测试角色检查"""
        ctx = UserContext(
            user_id="admin_user",
            roles={"admin"},
        )
        
        assert ctx.has_role("admin") is True
        assert ctx.has_role("viewer") is False


class TestPermissionManager:
    """权限管理器测试"""
    
    @pytest.fixture
    def manager(self):
        return PermissionManager()
    
    def test_create_manager(self, manager):
        """测试创建管理器"""
        assert manager is not None
    
    def test_default_sensitive_columns(self, manager):
        """测试默认敏感列"""
        assert "password" in manager.DEFAULT_SENSITIVE_COLUMNS
    
    def test_check_table_access(self, manager):
        """测试表访问检查"""
        # 默认允许访问
        result = manager.check_table_access("orders")
        assert isinstance(result, bool)

    def test_register_permission_and_get_allowed_columns(self, manager):
        perm = TablePermission(
            table_name="users",
            allowed_columns={"id", "name", "email"},
            denied_columns={"email"},
        )
        manager.register_table_permission(perm)
        cols = manager.get_allowed_columns("users", ["id", "name", "email", "password"])
        assert cols == ["id", "name"]

    def test_admin_can_see_sensitive_columns(self, manager):
        ctx = UserContext(user_id="u1", roles={"admin"})
        cols = manager.get_allowed_columns("users", ["id", "password"], ctx)
        assert "password" in cols

    def test_row_filter_and_max_rows(self, manager):
        manager.register_table_permission(
            TablePermission(table_name="orders", row_filter="tenant_id = 1", max_rows=50)
        )
        assert manager.get_row_filter("orders") == "tenant_id = 1"
        assert manager.get_max_rows("orders") == 50
        assert manager.get_max_rows("missing", default_max=123) == 123

    def test_validate_sql_tables_and_extract(self, manager):
        manager.set_allowed_tables({"orders"})
        ok, denied = manager.validate_sql_tables(
            "SELECT * FROM orders JOIN users ON orders.user_id = users.id"
        )
        assert ok is False
        assert "users" in denied
        assert manager._extract_tables_from_sql("SELECT * FROM orders JOIN users u ON 1=1") == {"orders", "users"}

    def test_role_based_table_access(self, manager):
        ctx = UserContext(user_id="u2", roles={"analyst"})
        manager.set_role_tables("analyst", {"metrics"})
        assert manager.check_table_access("metrics", ctx) is True

    def test_permission_level_ordering(self, manager):
        assert manager._check_permission_level(PermissionLevel.ADMIN, PermissionLevel.READ_ONLY) is True
        assert manager._check_permission_level(PermissionLevel.DENIED, PermissionLevel.READ_ONLY) is False


class TestPermissionFunctions:
    """便捷函数测试"""
    
    def test_get_permission_manager(self):
        """测试获取权限管理器"""
        manager = get_permission_manager()
        
        assert manager is not None
    
    def test_check_table_access_function(self):
        """测试表访问检查函数"""
        result = check_table_access("orders")
        
        assert isinstance(result, bool)
    
    def test_filter_sensitive_columns(self):
        """测试敏感列过滤"""
        import pandas as pd
        df = pd.DataFrame({
            "id": [1, 2],
            "name": ["Alice", "Bob"],
            "password": ["secret1", "secret2"],
        })
        result = filter_sensitive_columns(df, "users")
        
        # 返回过滤后的 DataFrame
        assert "password" not in result.columns
        assert "id" in result.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])