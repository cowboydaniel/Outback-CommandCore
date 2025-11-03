"""
Basic test cases for the Vantage application.
"""

def test_import_app():
    """Test that the application can be imported."""
    try:
        from app.main import main
        from app.config import Config
        assert True
    except ImportError as e:
        assert False, f"Failed to import application: {e}"

def test_config():
    """Test that the configuration is properly loaded."""
    from app.config import Config
    config = Config()
    assert hasattr(config, 'APP_NAME')
    assert config.APP_NAME == "Vantage"
