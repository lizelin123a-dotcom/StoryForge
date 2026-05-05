import os
import sys
from pathlib import Path

# 把项目根目录加入 sys.path，确保 Python 3.14 能找到 storyforge 模块
_project_root = str(Path(__file__).parent.resolve())
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from uvicorn import run

# 自动加载 .env 文件到环境变量
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("\"'").strip()
        if key and not os.getenv(key):
            os.environ[key] = value


def main() -> None:
    # 不能 import storyforge.interfaces.main:app 之前先把根目录加到 sys.path
    # uvicorn 内部用的是自己的 import_from_string，不一定继承 __main__ 的 sys.path
    # 所以在这里直接 import app 对象传入 uvicorn
    from storyforge.interfaces.main import app
    run(app, host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
