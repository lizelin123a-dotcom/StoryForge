"""StoryForge - Launcher
Fixes Python 3.14 PathFinder bug: __init__.py dir on sys.path not recognized.
"""
import os
import sys
import importlib.util
from pathlib import Path

# 项目根目录：使用当前文件位置，避免绑定到某台机器的绝对路径。
ROOT = Path(__file__).parent.resolve()
os.chdir(str(ROOT))

# Python 3.14 bug workaround: sys.path 上的 __init__.py 目录 PathFinder 不认
# 手动加载 storyforge 包
sys.path.insert(0, str(ROOT))
init_py = ROOT / "__init__.py"

spec = importlib.util.spec_from_file_location("storyforge", str(init_py), submodule_search_locations=[str(ROOT)])
storyforge_mod = importlib.util.module_from_spec(spec)
sys.modules["storyforge"] = storyforge_mod
spec.loader.exec_module(storyforge_mod)

# 加载 app
from storyforge.interfaces.main import app
from uvicorn import run

if __name__ == "__main__":
    print(f"StoryForge starting on http://0.0.0.0:8000")
    run(app, host="0.0.0.0", port=8000, reload=False)
