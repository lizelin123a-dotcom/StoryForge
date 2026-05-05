from pathlib import Path

for directory in [
    "storyforge/application/planner/services",
    "storyforge/application/writer/services",
    "storyforge/application/audit/services",
]:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    (path / "__init__.py").touch(exist_ok=True)
