# =============================================================================
# 基础镜像: pylover/docker（基于 cnbcool/default-dev-env 重构）
# 继承链: cnbcool/default-dev-env → pylover/docker → 本层
#
# 基础镜像已提供的能力:
#   - code-server 4.117.0
#   - VSCode 插件: cnb-welcome, redhat.vscode-yaml, mhutchie.git-graph,
#     donjayamanne.githistory, cloudstudio.live-server,
#     tencent-cloud.coding-copilot, bierner.markdown-mermaid
#   - APT 包: wget, unzip, xz-utils, lsof, nload, htop, net-tools,
#     dnsutils, openssh-server, zsh, locales
#   - Node.js 22, npm, uv, oh-my-zsh, zsh 补全插件
#
# 本层额外安装:
#   - APT: sqlite3, libmagic1, file, jq
#   - 15 个 VSCode 插件（见下方）
# =============================================================================
FROM docker.cnb.cool/pylover/docker

# 安装一些常用的工具
RUN apt-get update && \
    apt-get install -y sqlite3 libmagic1 file jq && \
    apt-get -y autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 安装 vscode 常用插件
RUN code-server --install-extension christian-kohler.path-intellisense \
    && code-server --install-extension vscode-icons-team.vscode-icons \
    && code-server --install-extension davidanson.vscode-markdownlint \
    && code-server --install-extension stylelint.vscode-stylelint \
    && code-server --install-extension bradlc.vscode-tailwindcss \
    && code-server --install-extension dbaeumer.vscode-eslint \
    && code-server --install-extension esbenp.prettier-vscode \
    && code-server --install-extension lokalise.i18n-ally \
    && code-server --install-extension csstools.postcss \
    && code-server --install-extension mikestead.dotenv \
    && code-server --install-extension antfu.iconify \
    && code-server --install-extension Vue.volar \
    && code-server --install-extension redjue.git-commit-plugin \
    && code-server --install-extension aaron-bond.better-comments \
    && code-server --install-extension cweijan.vscode-database-client2 \
    && code-server --install-extension ms-python.python \
    && echo done
