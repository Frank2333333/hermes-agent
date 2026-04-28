"""Tests for cron/scheduler.py in the enterprise build."""

from unittest.mock import MagicMock, patch

from cron.scheduler import (
    SILENT_MARKER,
    _build_job_prompt,
    _deliver_result,
    _resolve_delivery_target,
    _resolve_origin,
    run_job,
)


class TestResolveOrigin:
    def test_full_origin(self):
        job = {"origin": {"platform": "telegram", "chat_id": "123", "thread_id": "42"}}
        assert _resolve_origin(job) == job["origin"]

    def test_missing_origin_fields_return_none(self):
        assert _resolve_origin({}) is None
        assert _resolve_origin({"origin": {"platform": "telegram"}}) is None


class TestEnterpriseDelivery:
    def test_origin_delivery_only_preserves_origin_metadata(self):
        job = {"deliver": "origin", "origin": {"platform": "telegram", "chat_id": "123", "thread_id": "7"}}
        assert _resolve_delivery_target(job) == job["origin"]

    def test_external_delivery_targets_are_ignored(self):
        assert _resolve_delivery_target({"deliver": "telegram:123"}) is None
        result = _deliver_result({"id": "job-1", "deliver": "telegram:123"}, "hello")
        assert result is not None
        assert "disabled in the enterprise build" in result

    def test_local_delivery_is_not_an_error(self):
        assert _deliver_result({"id": "job-2", "deliver": "local"}, "hello") is None


class TestPromptHint:
    def test_prompt_mentions_enterprise_delivery_behavior(self):
        prompt = _build_job_prompt({"id": "job-1", "prompt": "report"})
        assert "does not support external or cross-platform delivery" in prompt
        assert SILENT_MARKER in prompt


class TestRunJobSessionPersistence:
    def test_run_job_passes_session_db_and_cron_platform(self, tmp_path):
        job = {"id": "test-job", "name": "test", "prompt": "hello"}
        fake_db = MagicMock()

        with patch("cron.scheduler._hermes_home", tmp_path), \
             patch("cron.scheduler._resolve_origin", return_value=None), \
             patch("dotenv.load_dotenv"), \
             patch("hermes_state.SessionDB", return_value=fake_db), \
             patch(
                 "hermes_cli.runtime_provider.resolve_runtime_provider",
                 return_value={
                     "api_key": "test-key",
                     "base_url": "https://example.invalid/v1",
                     "provider": "openrouter",
                     "api_mode": "chat_completions",
                 },
             ), \
             patch("run_agent.AIAgent") as mock_agent_cls:
            mock_agent = MagicMock()
            mock_agent.run_conversation.return_value = {"final_response": "ok"}
            mock_agent_cls.return_value = mock_agent

            success, output, final_response, error = run_job(job)

        assert success is True
        assert error is None
        assert final_response == "ok"
        assert "ok" in output

        kwargs = mock_agent_cls.call_args.kwargs
        assert kwargs["session_db"] is fake_db
        assert kwargs["platform"] == "cron"
        assert kwargs["session_id"].startswith("cron_test-job_")
