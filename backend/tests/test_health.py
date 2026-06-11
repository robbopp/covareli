async def test_health(api):
    resp = await api.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
