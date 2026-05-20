"""Regression tests for registry disabled entry leak (#545)."""

import pytest

from src.agent.registry import AgentRegistry, AgentStatus


class TestRegistryDisabledLeak:
    """Bounty #545: Disabled entries must not leak in capability discovery listings."""

    def setup_method(self):
        self.registry = AgentRegistry()

    # --- list() filtering ---

    def test_list_excludes_stopped_agents_by_default(self):
        aid = self.registry.register("a1", "worker.processor")
        self.registry.update_status(aid, AgentStatus.STOPPED)
        assert len(self.registry.list()) == 0

    def test_list_excludes_terminated_agents_by_default(self):
        aid = self.registry.register("a1", "worker.processor")
        self.registry.update_status(aid, AgentStatus.TERMINATED)
        assert len(self.registry.list()) == 0

    def test_list_includes_disabled_when_flag_set(self):
        aid = self.registry.register("a1", "worker.processor")
        self.registry.update_status(aid, AgentStatus.STOPPED)
        assert len(self.registry.list(include_disabled=True)) == 1

    def test_list_mixed_enabled_disabled(self):
        a1 = self.registry.register("a1", "worker.processor")
        self.registry.register("a2", "worker.analyzer")
        self.registry.update_status(a1, AgentStatus.STOPPED)
        result = self.registry.list()
        assert len(result) == 1
        assert result[0]["name"] == "a2"

    # --- discover_capabilities() ---

    def test_discover_excludes_stopped(self):
        aid = self.registry.register("a1", "worker.processor")
        self.registry.update_status(aid, AgentStatus.STOPPED)
        assert len(self.registry.discover_capabilities()) == 0

    def test_discover_excludes_terminated(self):
        aid = self.registry.register("a1", "worker.processor")
        self.registry.update_status(aid, AgentStatus.TERMINATED)
        assert len(self.registry.discover_capabilities()) == 0

    def test_discover_includes_running(self):
        aid = self.registry.register("a1", "worker.processor")
        self.registry.update_status(aid, AgentStatus.RUNNING)
        assert len(self.registry.discover_capabilities()) == 1

    def test_discover_by_group_excludes_disabled(self):
        a1 = self.registry.register("a1", "worker.processor")
        self.registry.register("a2", "worker.analyzer")
        self.registry.update_status(a1, AgentStatus.STOPPED)
        result = self.registry.discover_capabilities(group="worker")
        assert len(result) == 1
        assert result[0]["name"] == "a2"

    # --- cache invalidation ---

    def test_cache_invalidated_on_status_change(self):
        """After changing status to STOPPED, the capability cache must be refreshed."""
        aid = self.registry.register("a1", "worker.processor")
        # Populate cache
        assert len(self.registry.discover_capabilities()) == 1
        # Disable the agent
        self.registry.update_status(aid, AgentStatus.STOPPED)
        # Cache should be invalidated, so next call returns fresh data
        assert len(self.registry.discover_capabilities()) == 0

    def test_cache_invalidated_on_register(self):
        """After registering a new agent, the cache must be invalidated."""
        assert len(self.registry.discover_capabilities()) == 0
        self.registry.register("a1", "worker.processor")
        assert len(self.registry.discover_capabilities()) == 1

    def test_cache_invalidated_on_delete(self):
        """After deleting an agent, the cache must be invalidated."""
        aid = self.registry.register("a1", "worker.processor")
        assert len(self.registry.discover_capabilities()) == 1
        self.registry.delete(aid)
        assert len(self.registry.discover_capabilities()) == 0

    # --- resolve() ---

    def test_resolve_skips_disabled(self):
        """resolve() must not return agents with disabled statuses."""
        aid = self.registry.register("a1", "worker.processor")
        self.registry.update_status(aid, AgentStatus.STOPPED)
        assert self.registry.resolve("worker.processor") is None

    def test_resolve_finds_active(self):
        aid = self.registry.register("a1", "worker.processor")
        self.registry.update_status(aid, AgentStatus.RUNNING)
        result = self.registry.resolve("worker.processor")
        assert result is not None
        assert result["id"] == aid

    def test_resolve_picks_first_active(self):
        a1 = self.registry.register("a1", "worker.processor")
        a2 = self.registry.register("a2", "worker.processor")
        self.registry.update_status(a1, AgentStatus.STOPPED)
        result = self.registry.resolve("worker.processor")
        assert result["id"] == a2
