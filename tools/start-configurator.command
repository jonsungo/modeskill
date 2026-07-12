#!/bin/zsh

set -u

SCRIPT_DIR="${0:A:h}"
REPO_ROOT="${SCRIPT_DIR:h}"
SERVER="$REPO_ROOT/.agents/skills/modeskill/configurator/server.py"
URL="http://127.0.0.1:8765/"

cd "$REPO_ROOT" || {
  print -u2 "无法进入 Modeskill 仓库目录：$REPO_ROOT"
  exit 1
}

if [[ ! -f "$SERVER" ]]; then
  print -u2 "找不到 Modeskill 设置服务：$SERVER"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  print -u2 "未找到 Python 3，无法启动 Modeskill 设置页。"
  exit 1
fi

print "正在启动 Modeskill 设置页：$URL"
print "关闭此终端窗口即可停止设置服务。"

(sleep 1; open "$URL") &
exec python3 "$SERVER"
