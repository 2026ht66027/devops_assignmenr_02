"""Tests for ACEest's Flask routes and basic project integrity."""
import ast
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_application_source_is_valid_python():
    ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))


def test_required_routes_are_declared():
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    for route in ['"/"', '"/clients"', '"/health"', '"/ready"']:
        assert route in source


def test_programmes_have_expected_goals():
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "PROGRAMS" for target in node.targets)
    )
    goals = {key.value for key in assignment.value.keys}
    assert goals == {"Fat Loss", "Muscle Gain", "Beginner"}


def test_flask_routes_and_client_workflow(tmp_path, monkeypatch):
    pytest.importorskip("flask")
    import app as application

    monkeypatch.setattr(application, "DATABASE", tmp_path / "test.db")
    application.init_db()
    flask_app = application.create_app()
    flask_app.config.update(TESTING=True, SECRET_KEY="test")

    with flask_app.test_client() as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 200
        assert client.get("/").status_code == 200

        invalid = client.post("/clients", data={"name": "", "age": "25", "goal": "Beginner"})
        assert invalid.status_code == 302

        response = client.post(
            "/clients",
            data={"name": "Test Member", "age": "25", "goal": "Beginner"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Test Member" in response.data

        deleted = client.post("/clients/1/delete", follow_redirects=True)
        assert deleted.status_code == 200
        assert b"Test Member" not in deleted.data
