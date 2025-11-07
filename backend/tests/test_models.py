"""
Unit tests for ORM models and core services.

Tests the SQLAlchemy models, encryption service, and database configuration.
"""

import pytest
from datetime import datetime
from src.models import (
    DataSource, DataSourceType, DataSourceStatus,
    DatabaseConnection,
    FileUpload, FileFormat, FileParseStatus,
    Schema,
    DataSourceConfig
)
from src.services import EncryptionService


class TestDataSourceModel:
    """Test cases for DataSource ORM model."""

    def test_datasource_creation(self):
        """Test creating a DataSource instance."""
        ds = DataSource(
            name="Production DB",
            description="Main production database",
            type=DataSourceType.POSTGRESQL,
            status=DataSourceStatus.CONNECTED
        )

        assert ds.name == "Production DB"
        assert ds.description == "Main production database"
        assert ds.type == DataSourceType.POSTGRESQL
        assert ds.status == DataSourceStatus.CONNECTED

    def test_datasource_tablename(self):
        """Test DataSource table name."""
        assert DataSource.__tablename__ == "data_sources"

    def test_datasource_repr(self):
        """Test DataSource string representation."""
        ds = DataSource(id=1, name="Test", type=DataSourceType.CSV, status=DataSourceStatus.ERROR)
        repr_str = repr(ds)

        assert "DataSource" in repr_str
        assert "id=1" in repr_str
        assert "type=DataSourceType.CSV" in repr_str

    def test_datasource_can_be_instantiated(self):
        """Test that DataSource can be instantiated with minimal args."""
        ds = DataSource(name="Test")
        assert ds.name == "Test"


class TestDatabaseConnectionModel:
    """Test cases for DatabaseConnection ORM model."""

    def test_database_connection_creation(self):
        """Test creating a DatabaseConnection instance."""
        conn = DatabaseConnection(
            data_source_id=1,
            host="postgres.example.com",
            port=5432,
            database="mydb",
            username="user",
            encrypted_password="encrypted_pwd_123",
            ssl_enabled=True
        )

        assert conn.data_source_id == 1
        assert conn.host == "postgres.example.com"
        assert conn.port == 5432
        assert conn.database == "mydb"
        assert conn.username == "user"
        assert conn.ssl_enabled is True

    def test_database_connection_can_be_minimal(self):
        """Test DatabaseConnection can be created with minimal args."""
        conn = DatabaseConnection(
            data_source_id=1,
            host="localhost",
            database="db",
            username="user",
            encrypted_password="pwd"
        )

        assert conn.data_source_id == 1
        assert conn.host == "localhost"

    def test_database_connection_tablename(self):
        """Test DatabaseConnection table name."""
        assert DatabaseConnection.__tablename__ == "database_connections"


class TestFileUploadModel:
    """Test cases for FileUpload ORM model."""

    def test_file_upload_creation(self):
        """Test creating a FileUpload instance."""
        upload = FileUpload(
            data_source_id=2,
            filename="customers.csv",
            file_path="uploads/2025-11-08/customers_abc123.csv",
            file_format="csv",
            file_size=1024000,
            row_count=5000,
            column_count=12,
            parse_status=FileParseStatus.SUCCESS
        )

        assert upload.data_source_id == 2
        assert upload.filename == "customers.csv"
        assert upload.file_size == 1024000
        assert upload.row_count == 5000
        assert upload.column_count == 12

    def test_file_upload_can_be_minimal(self):
        """Test FileUpload can be created with minimal args."""
        upload = FileUpload(
            data_source_id=1,
            filename="data.csv",
            file_path="uploads/data.csv",
            file_format="csv",
            file_size=1000
        )

        assert upload.data_source_id == 1
        assert upload.filename == "data.csv"

    def test_file_upload_tablename(self):
        """Test FileUpload table name."""
        assert FileUpload.__tablename__ == "file_uploads"


class TestSchemaModel:
    """Test cases for Schema ORM model."""

    def test_schema_creation(self):
        """Test creating a Schema instance."""
        schema = Schema(
            data_source_id=1,
            table_name="customers",
            table_schema="public",
            column_count=5,
            column_info='[{"name": "id", "type": "integer"}]',
            row_count=100000,
            size_bytes=1048576
        )

        assert schema.data_source_id == 1
        assert schema.table_name == "customers"
        assert schema.table_schema == "public"
        assert schema.column_count == 5
        assert schema.row_count == 100000

    def test_schema_can_be_minimal(self):
        """Test Schema can be created with minimal args."""
        schema = Schema(
            data_source_id=1,
            table_name="test",
            column_info="[]"
        )

        assert schema.data_source_id == 1
        assert schema.table_name == "test"

    def test_schema_tablename(self):
        """Test Schema table name."""
        assert Schema.__tablename__ == "schemas"


class TestDataSourceConfigModel:
    """Test cases for DataSourceConfig ORM model."""

    def test_datasource_config_creation(self):
        """Test creating a DataSourceConfig instance."""
        config = DataSourceConfig(
            data_source_id=1,
            is_default=True,
            query_timeout=60,
            max_result_rows=50000,
            enable_cache=True,
            cache_ttl=600
        )

        assert config.data_source_id == 1
        assert config.is_default is True
        assert config.query_timeout == 60
        assert config.max_result_rows == 50000
        assert config.cache_ttl == 600

    def test_datasource_config_can_be_minimal(self):
        """Test DataSourceConfig can be created with minimal args."""
        config = DataSourceConfig(data_source_id=1)

        assert config.data_source_id == 1

    def test_datasource_config_tablename(self):
        """Test DataSourceConfig table name."""
        assert DataSourceConfig.__tablename__ == "datasource_configs"


class TestEncryptionService:
    """Test cases for EncryptionService."""

    @pytest.fixture
    def cipher(self):
        """Create an EncryptionService instance with a test key."""
        return EncryptionService(key=EncryptionService.generate_key())

    def test_encryption_service_creation(self):
        """Test creating an EncryptionService instance."""
        key = EncryptionService.generate_key()
        cipher = EncryptionService(key=key)

        assert cipher is not None
        assert cipher.cipher is not None

    def test_encrypt_decrypt_roundtrip(self, cipher):
        """Test encrypting and decrypting data."""
        plaintext = "MySecretPassword123!@#"

        encrypted = cipher.encrypt(plaintext)
        decrypted = cipher.decrypt(encrypted)

        assert encrypted != plaintext
        assert decrypted == plaintext

    def test_encrypt_empty_string(self, cipher):
        """Test encrypting empty string."""
        encrypted = cipher.encrypt("")
        assert encrypted == ""

    def test_decrypt_empty_string(self, cipher):
        """Test decrypting empty string."""
        decrypted = cipher.decrypt("")
        assert decrypted == ""

    def test_encrypt_unicode(self, cipher):
        """Test encrypting unicode characters."""
        plaintext = "密码123!@#"

        encrypted = cipher.encrypt(plaintext)
        decrypted = cipher.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_large_text(self, cipher):
        """Test encrypting large text."""
        plaintext = "x" * 10000

        encrypted = cipher.encrypt(plaintext)
        decrypted = cipher.decrypt(encrypted)

        assert decrypted == plaintext

    def test_generate_key(self):
        """Test key generation."""
        key1 = EncryptionService.generate_key()
        key2 = EncryptionService.generate_key()

        assert key1 is not None
        assert key2 is not None
        assert key1 != key2
        assert len(key1) > 0

    def test_different_keys_cannot_decrypt(self):
        """Test that data encrypted with one key cannot be decrypted with another."""
        key1 = EncryptionService.generate_key()
        key2 = EncryptionService.generate_key()

        cipher1 = EncryptionService(key=key1)
        cipher2 = EncryptionService(key=key2)

        encrypted = cipher1.encrypt("secret")

        with pytest.raises(ValueError):
            cipher2.decrypt(encrypted)

    def test_no_key_raises_error(self):
        """Test that EncryptionService raises error without key."""
        import os
        # Temporarily remove ENCRYPTION_KEY
        old_key = os.environ.pop("ENCRYPTION_KEY", None)

        try:
            with pytest.raises(ValueError, match="No encryption key provided"):
                EncryptionService(key=None)
        finally:
            # Restore the key
            if old_key is not None:
                os.environ["ENCRYPTION_KEY"] = old_key


class TestModelTimestamps:
    """Test cases for model timestamp fields."""

    def test_all_models_have_timestamp_columns(self):
        """Test that all models define timestamp columns."""
        # These are verified during ORM model definition
        models_with_timestamps = [
            DataSource,
            DatabaseConnection,
            FileUpload,
            Schema,
            DataSourceConfig,
        ]

        for model in models_with_timestamps:
            # Check that the model has created_at and updated_at columns defined
            assert hasattr(model, "created_at"), f"{model.__name__} missing created_at"
            assert hasattr(model, "updated_at"), f"{model.__name__} missing updated_at"

    def test_model_instantiation_with_explicit_timestamps(self):
        """Test that timestamp columns can be set explicitly."""
        from datetime import datetime
        now = datetime.utcnow()

        ds = DataSource(name="Test", created_at=now, updated_at=now)
        assert ds.created_at == now
        assert ds.updated_at == now
