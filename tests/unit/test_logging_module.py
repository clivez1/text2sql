import json
import logging
from datetime import datetime

from app.core import logging as logmod


def test_custom_json_formatter_outputs_json():
    formatter = logmod.CustomJsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello",
        args=(),
        exc_info=None,
    )
    payload = json.loads(formatter.format(record))
    assert payload["level"] == "INFO"
    assert payload["message"] == "hello"
    assert payload["timestamp"].endswith("Z")
    datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))


def test_setup_logging_returns_root_logger(tmp_path):
    log_file = tmp_path / "app.log"
    logger = logmod.setup_logging(level="DEBUG", log_file=str(log_file), json_format=False)
    logger.info("hello world")
    assert log_file.exists()
    assert logger is logging.getLogger()


def test_get_logger_returns_named_logger():
    logger = logmod.get_logger("demo")
    assert logger.name == "demo"


def test_log_context_injects_extra(caplog):
    logger = logging.getLogger("ctx-test")
    ctx = logmod.LogContext(logger, request_id="r1")
    with caplog.at_level(logging.INFO):
        ctx.info("msg", user="u1")
    assert "msg" in caplog.text


def test_init_app_logging(monkeypatch, tmp_path):
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("LOG_FILE", str(tmp_path / "x.log"))
    monkeypatch.setenv("LOG_JSON", "false")
    logger = logmod.init_app_logging()
    assert logger is logging.getLogger()
