FROM docker.cnb.cool/pylover/docker

# 安装一些常用的工具
RUN apt-get update && \
    apt-get install -y sqlite3 libmagic1 file jq && \
    apt-get -y autoremove && \
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
    && echo done
