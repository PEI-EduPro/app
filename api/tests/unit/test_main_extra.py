import pytest
from src.main import app
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Education Platform API is running"}

@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/api/")
    assert response.status_code == 200
    assert "documentation" in response.json()

@pytest.mark.asyncio
async def test_security_headers(client):
    response = await client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"

@pytest.mark.asyncio
async def test_lifespan_db_init_failure():
    with patch("src.main.create_db_and_tables", side_effect=Exception("DB fail")):
        from src.main import lifespan
        with pytest.raises(Exception, match="DB fail"):
            async with lifespan(None):
                pass

@pytest.mark.asyncio
async def test_lifespan_db_verify_failure():
    with patch("src.main.create_db_and_tables", new_callable=AsyncMock), \
         patch("src.core.db.engine", spec=True) as mock_engine:
        mock_engine.connect.side_effect = Exception("Conn fail")
        from src.main import lifespan
        # verify failure shouldn't raise, just log
        async with lifespan(None):
            pass
