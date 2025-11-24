from agent.dependency_updater import DependencyUpdater


def test_dependency_updater_returns_true(tmp_path):
    updater = DependencyUpdater()
    result = updater.update_dependencies(tmp_path, [])
    assert result == []
