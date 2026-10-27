"""
Git Manager for Hermes Knowledge Base
负责知识资产库的版本控制、自动提交、提交历史追溯
"""
import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from config import BASE_DIR, GIT_AUTO_COMMIT, GIT_DEFAULT_AUTHOR

logger = logging.getLogger("hermes.git")

class GitManager:
    def __init__(self, repo_dir: Optional[Path] = None):
        self.repo_dir = repo_dir or BASE_DIR
        self._ensure_repo()

    def _run_cmd(self, cmd: List[str]) -> Tuple[int, str, str]:
        try:
            res = subprocess.run(
                cmd,
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                check=False
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except Exception as e:
            logger.error(f"Error running git command {' '.join(cmd)}: {e}")
            return -1, "", str(e)

    def _ensure_repo(self):
        """确保当前目录是合法的 Git 仓库，且配置了本地提交用户信息"""
        code, out, _ = self._run_cmd(["git", "rev-parse", "--is-inside-work-tree"])
        if code != 0 or out != "true":
            logger.info("Initializing new git repository...")
            self._run_cmd(["git", "init"])

        # 检查是否配置了 user.name 和 user.email
        code, name, _ = self._run_cmd(["git", "config", "user.name"])
        code_e, email, _ = self._run_cmd(["git", "config", "user.email"])
        if not name or code != 0:
            self._run_cmd(["git", "config", "user.name", "HermesKB Creator"])
        if not email or code_e != 0:
            self._run_cmd(["git", "config", "user.email", "hermes@local"])

    def status(self) -> str:
        """获取当前工作区状态"""
        _, out, _ = self._run_cmd(["git", "status", "--short"])
        return out

    def has_uncommitted_changes(self) -> bool:
        """检查是否有待提交的内容"""
        status = self.status()
        return len(status.strip()) > 0

    def commit(self, message: str, paths: Optional[List[str]] = None) -> Optional[str]:
        """
        自动添加并提交变更
        """
        if not GIT_AUTO_COMMIT:
            logger.info("Git auto-commit is disabled in config.")
            return None

        # 检查是否有改动
        if not self.has_uncommitted_changes():
            logger.info("No git changes to commit.")
            return None

        # git add
        if paths:
            cmd_add = ["git", "add"] + paths
        else:
            cmd_add = ["git", "add", "."]
        
        c1, _, err1 = self._run_cmd(cmd_add)
        if c1 != 0:
            logger.error(f"git add failed: {err1}")
            return None

        # git commit
        c2, out2, err2 = self._run_cmd(["git", "commit", "-m", message])
        if c2 == 0:
            # 提取 commit hash
            _, hash_out, _ = self._run_cmd(["git", "rev-parse", "--short", "HEAD"])
            logger.info(f"Git commit successful [{hash_out}]: {message}")
            return hash_out
        else:
            logger.warning(f"git commit notice: {err2 or out2}")
            return None

    def get_recent_commits(self, limit: int = 10) -> List[dict]:
        """获取最近提交历史"""
        cmd = ["git", "log", f"-n{limit}", "--pretty=format:%h|%an|%ad|%s", "--date=short"]
        code, out, _ = self._run_cmd(cmd)
        if code != 0 or not out:
            return []
        
        commits = []
        for line in out.splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3]
                })
        return commits
