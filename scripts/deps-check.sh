#!/usr/bin/env bash
set -Eeuo pipefail

# ==============================================================================
# deps-check.sh — 每日依赖版本检测（方案 B：只检测 + Issue 报告）
# 流程：检测更新 → 调用 AI 分析 → 关闭旧 Issue → 创建新 Issue
# 由 CNB crontab 每日 9:00 触发
# ==============================================================================

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd -P)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
TODAY="$(date +%Y-%m-%d)"
LABEL="dependency-check"

# ---- 日志 ----
log_info()  { echo "[INFO]  $(date +%H:%M:%S) $*" >&2; }
log_warn()  { echo "[WARN]  $(date +%H:%M:%S) $*" >&2; }
log_error() { echo "[ERROR] $(date +%H:%M:%S) $*" >&2; }

# ---- 前置检查 ----
require_cmd() {
    command -v "$1" &>/dev/null || { log_error "$1 not found"; exit 1; }
}
require_cmd uv
require_cmd git
require_cmd curl
require_cmd jq

: "${CNB_TOKEN:?CNB_TOKEN is not set}"
: "${CNB_REPO_SLUG:?CNB_REPO_SLUG is not set}"
CNB_API_ENDPOINT="${CNB_API_ENDPOINT:-https://api.cnb.cool}"
DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"

# ---- 升级工具链自身 ----
log_info "升级工具链到最新版本..."
UV_OLD_VER=$(uv --version 2>/dev/null || echo "unknown")
uv self update 2>&1 | tail -3 || log_warn "uv self update 失败（CI 环境可能不支持自更新）"
UV_NEW_VER=$(uv --version 2>/dev/null || echo "unknown")
log_info "uv: ${UV_OLD_VER} → ${UV_NEW_VER}"

BUN_OLD_VER=""
BUN_NEW_VER=""
if command -v bun &>/dev/null; then
    BUN_OLD_VER=$(bun --version 2>/dev/null || echo "unknown")
    # bun upgrade 在 CI 中需要 -s (silent) 避免交互
    bun upgrade 2>&1 | tail -3 || log_warn "bun upgrade 失败"
    BUN_NEW_VER=$(bun --version 2>/dev/null || echo "unknown")
    log_info "bun: ${BUN_OLD_VER} → ${BUN_NEW_VER}"
fi

# ==============================================================================
# 1. 后端依赖检测（安全：不修改任何文件）
# ==============================================================================
detect_backend_updates() {
    cd "${BACKEND_DIR}"

    # 备份原始 uv.lock
    cp uv.lock uv.lock.bak

    # 执行升级（仅影响 lock 文件，不安装）
    uv lock --upgrade 2>&1 | tail -5 || true

    # 对比差异
    local diff_output
    diff_output=$(git diff --no-index -- uv.lock.bak uv.lock 2>/dev/null || true)

    # 恢复原始 lock 文件
    mv uv.lock.bak uv.lock

    if [[ -z "${diff_output}" ]]; then
        log_info "后端：无依赖更新"
        echo ""
        return 0
    fi

    # 解析变更的包：从 diff 中提取 name/version 对
    # uv.lock 格式：每个包是一个 [[package]] 段，含 name = "xxx" 和 version = "x.x.x"
    local updates=""
    local old_packages
    local new_packages

    # 提取旧版本映射 (name→version)
    old_packages=$(echo "${diff_output}" \
        | grep -E '^-name = |^-version = ' \
        | paste - - \
        | sed 's/-name = "\(.*\)"\s*-version = "\(.*\)"/\1 \2/' \
        | sort)

    # 提取新版本映射 (name→version)
    new_packages=$(echo "${diff_output}" \
        | grep -E '^\+name = |^\+version = ' \
        | paste - - \
        | sed 's/+name = "\(.*\)"\s*+version = "\(.*\)"/\1 \2/' \
        | sort)

    # 合并：找出有版本变化的包
    updates=$(comm -12 \
        <(echo "${old_packages}" | awk '{print $1}' | sort -u) \
        <(echo "${new_packages}" | awk '{print $1}' | sort -u) \
        | while read -r pkg; do
            local old_ver new_ver
            old_ver=$(echo "${old_packages}" | awk -v p="${pkg}" '$1 == p {print $2}' | head -1)
            new_ver=$(echo "${new_packages}" | awk -v p="${pkg}" '$1 == p {print $2}' | head -1)
            if [[ -n "${old_ver}" && -n "${new_ver}" && "${old_ver}" != "${new_ver}" ]]; then
                echo "${pkg}|${old_ver}|${new_ver}"
            fi
        done)

    if [[ -z "${updates}" ]]; then
        log_info "后端：解析后无实际版本变化"
        echo ""
        return 0
    fi

    log_info "后端：检测到 $(echo "${updates}" | wc -l) 个依赖有更新"
    echo "${updates}"
}

# ==============================================================================
# 2. 前端依赖检测（对比上游 vue-pure-admin 最新 release）
# ==============================================================================
UPSTREAM_REPO="pure-admin/vue-pure-admin"

detect_frontend_updates() {
    local pkg_version
    pkg_version=$(jq -r '.version' "${FRONTEND_DIR}/package.json" 2>/dev/null || echo "")

    if [[ -z "${pkg_version}" ]]; then
        log_warn "无法读取 frontend/package.json 中的 version"
        echo ""
        return 0
    fi

    log_info "前端当前版本: v${pkg_version}，检测上游 ${UPSTREAM_REPO} 最新 release..."

    # 从 GitHub API 获取最新 release（非 prerelease、非 draft）
    local release_json
    release_json=$(curl -sf "https://api.github.com/repos/${UPSTREAM_REPO}/releases?per_page=10" 2>/dev/null || echo "[]")

    if [[ "${release_json}" == "[]" ]]; then
        log_warn "无法获取上游 release 信息（API 限流或网络问题）"
        echo ""
        return 0
    fi

    # 找到最新的非 prerelease、非 draft 的 release
    local latest_tag latest_name latest_published latest_url latest_body
    latest_tag=$(echo "${release_json}" \
        | jq -r '[.[] | select(.prerelease == false and .draft == false)][0].tag_name // empty' 2>/dev/null)

    if [[ -z "${latest_tag}" ]]; then
        log_warn "上游无正式 release"
        echo ""
        return 0
    fi

    latest_name=$(echo "${release_json}" | jq -r '[.[] | select(.prerelease == false and .draft == false)][0].name // empty')
    latest_published=$(echo "${release_json}" | jq -r '[.[] | select(.prerelease == false and .draft == false)][0].published_at // empty')
    latest_url=$(echo "${release_json}" | jq -r '[.[] | select(.prerelease == false and .draft == false)][0].html_url // empty')
    latest_body=$(echo "${release_json}" | jq -r '[.[] | select(.prerelease == false and .draft == false)][0].body // empty')

    # 去掉 tag 前缀 v 做版本比较
    local latest_version="${latest_tag#v}"

    if [[ "${latest_version}" == "${pkg_version}" ]]; then
        log_info "前端：已是最新版本 v${pkg_version}"
        echo ""
        return 0
    fi

    # 判断是否为升级（latest > current），而非降级
    local is_upgrade=false
    local pkg_major pkg_minor pkg_patch latest_major latest_minor latest_patch
    IFS='.' read -r pkg_major pkg_minor pkg_patch <<< "${pkg_version}"
    IFS='.' read -r latest_major latest_minor latest_patch <<< "${latest_version}"

    pkg_major="${pkg_major:-0}"; pkg_minor="${pkg_minor:-0}"; pkg_patch="${pkg_patch:-0}"
    latest_major="${latest_major:-0}"; latest_minor="${latest_minor:-0}"; latest_patch="${latest_patch:-0}"

    if [[ "${latest_major}" -gt "${pkg_major}" ]] \
        || { [[ "${latest_major}" -eq "${pkg_major}" ]] && [[ "${latest_minor}" -gt "${pkg_minor}" ]]; } \
        || { [[ "${latest_major}" -eq "${pkg_major}" ]] && [[ "${latest_minor}" -eq "${pkg_minor}" ]] && [[ "${latest_patch}" -gt "${pkg_patch}" ]]; }; then
        is_upgrade=true
    fi

    if [[ "${is_upgrade}" == false ]]; then
        log_info "前端：当前版本 v${pkg_version} 不低于上游最新 v${latest_version}，无需更新"
        echo ""
        return 0
    fi

    # 收集当前版本和最新版本之间的所有 release
    local all_releases
    all_releases=$(echo "${release_json}" \
        | jq -r --arg cur "v${pkg_version}" \
            '[.[] | select(.prerelease == false and .draft == false and (.tag_name | .[1:] | split(".") | map(tonumber? // 0)) > ($cur | .[1:] | split(".") | map(tonumber? // 0)))] | sort_by(.published_at) | reverse | .[] | "\(.tag_name)|\(.name)|\(.published_at)|\(.html_url)|\(.body)"' 2>/dev/null || true)

    # 输出格式：第一行为当前版本信息，后续每行一个 release
    # 格式: CURRENT|pkg_version|latest_version|latest_published|latest_url
    # 后续: RELEASE|tag|name|published_at|html_url|body
    echo "CURRENT|${pkg_version}|${latest_version}|${latest_published}|${latest_url}"

    if [[ -n "${all_releases}" ]]; then
        while IFS= read -r line; do
            [[ -z "${line}" ]] && continue
            echo "RELEASE|${line}"
        done <<< "${all_releases}"
    else
        # fallback: 至少输出最新 release 的 body
        echo "RELEASE|${latest_tag}|${latest_name}|${latest_published}|${latest_url}|${latest_body}"
    fi
}

# ==============================================================================
# 3. 生成 Markdown 报告
# ==============================================================================
generate_report() {
    local backend_updates="$1"
    local frontend_updates="$2"
    local uv_old="$3"
    local uv_new="$4"
    local bun_old="$5"
    local bun_new="$6"

    local report=""
    report+="## 依赖更新检测报告 (${TODAY})\n\n"

    # ---- 工具链版本 ----
    report+="### 工具链版本\n\n"
    report+="| 工具 | 当前版本 | 最新版本 | 状态 |\n"
    report+="|------|---------|---------|------|\n"
    local uv_status="已最新 ✅"
    if [[ "${uv_old}" != "${uv_new}" ]]; then
        uv_status="有更新 ⬆️"
    fi
    report+="| \`uv\` | \`${uv_old}\` | \`${uv_new}\` | ${uv_status} |\n"
    if [[ -n "${bun_old}" ]]; then
        local bun_status="已最新 ✅"
        if [[ "${bun_old}" != "${bun_new}" ]]; then
            bun_status="有更新 ⬆️"
        fi
        report+="| \`bun\` | \`${bun_old}\` | \`${bun_new}\` | ${bun_status} |\n"
    fi
    report+="\n"

    # ---- 后端部分 ----
    if [[ -n "${backend_updates}" ]]; then
        report+="### 后端 (Python)\n\n"
        report+="| 包名 | 当前版本 | 最新版本 | 变更级别 |\n"
        report+="|------|---------|---------|--------|\n"

        while IFS='|' read -r pkg old_ver new_ver; do
            [[ -z "${pkg}" ]] && continue
            local level
            level=$(semver_level "${old_ver}" "${new_ver}")
            report+="| \`${pkg}\` | \`${old_ver}\` | \`${new_ver}\` | ${level} |\n"
        done <<< "${backend_updates}"
        report+="\n"
    else
        report+="### 后端 (Python)\n\n所有依赖均为最新版本。\n\n"
    fi

    # ---- 前端部分 ----
    if [[ -n "${frontend_updates}" ]]; then
        # 解析前端更新数据
        local current_line=""
        local release_lines=""
        while IFS= read -r line; do
            [[ -z "${line}" ]] && continue
            if [[ "${line}" == CURRENT* ]]; then
                current_line="${line}"
            elif [[ "${line}" == RELEASE* ]]; then
                release_lines+="${line}"$'\n'
            fi
        done <<< "${frontend_updates}"

        if [[ -n "${current_line}" ]]; then
            local cur_ver latest_ver latest_pub latest_link
            IFS='|' read -r _ cur_ver latest_ver latest_pub latest_link <<< "${current_line}"
            local level
            level=$(semver_level "${cur_ver}" "${latest_ver}")
            report+="### 前端（vue-pure-admin 上游）\n\n"
            report+="| 项目 | 当前版本 | 上游最新 | 变更级别 |\n"
            report+="|------|---------|---------|--------|\n"
            report+="| \`vue-pure-admin\` | \`v${cur_ver}\` | [\`v${latest_ver}\`](${latest_link}) | ${level} |\n\n"
        fi

        if [[ -n "${release_lines}" ]]; then
            report+="<details><summary>📋 上游 Release Notes</summary>\n\n"
            while IFS= read -r rline; do
                [[ -z "${rline}" ]] && continue
                # RELEASE|tag|name|published_at|html_url|body
                local r_tag r_name r_pub r_url r_body
                IFS='|' read -r _ r_tag r_name r_pub r_url r_body <<< "${rline}"
                local pub_date="${r_pub%%T*}"
                report+="### [${r_tag}](${r_url}) (${pub_date})\n\n"
                report+="${r_body}\n\n---\n\n"
            done <<< "${release_lines}"
            report+="</details>\n\n"
        fi
    else
        report+="### 前端（vue-pure-admin 上游）\n\n已是最新版本，无需更新。\n\n"
    fi

    echo -e "${report}"
}

# 判断 semver 变更级别
semver_level() {
    local old="$1" new="$2"

    # 提取 major.minor.patch
    local old_major old_minor old_patch
    IFS='.' read -r old_major old_minor old_patch <<< "${old%%[+a-zA-Z]*}"
    local new_major new_minor new_patch
    IFS='.' read -r new_major new_minor new_patch <<< "${new%%[+a-zA-Z]*}"

    old_major="${old_major:-0}"; old_minor="${old_minor:-0}"; old_patch="${old_patch:-0}"
    new_major="${new_major:-0}"; new_minor="${new_minor:-0}"; new_patch="${new_patch:-0}"

    if [[ "${new_major}" -gt "${old_major}" ]]; then
        echo "**major**"
    elif [[ "${new_minor}" -gt "${old_minor}" ]]; then
        echo "minor"
    else
        echo "patch"
    fi
}

# ==============================================================================
# 4. AI 影响分析（DeepSeek）
# ==============================================================================
ai_analysis() {
    local report="$1"

    if [[ -z "${DEEPSEEK_API_KEY}" ]]; then
        log_warn "DEEPSEEK_API_KEY 未设置，跳过 AI 分析"
        echo "AI 分析未启用（缺少 DEEPSEEK_API_KEY）。请人工查看上述更新的官方 changelog。"
        return
    fi

    local prompt
    read -r -d '' prompt << 'PROMPT_EOF'
你是一个专业的 Python/Node.js 依赖管理专家。以下是今日自动检测到的依赖更新列表。

请对每个更新的依赖做以下分析：
1. **更新内容**：该版本的官方更新说明摘要（如不确定请标注"未验证"）
2. **影响评估**：对 ZgAdmin 项目的影响等级（低/中/高）
3. **是否需要优化**：是否需要针对此更新对项目代码做适配或优化

项目技术栈：
- 后端：FastAPI + SQLModel + Uvicorn + Redis + APScheduler
- 前端：基于 vue-pure-admin（上游仓库 pure-admin/vue-pure-admin），Vue 3 + Element Plus + Pinia + Vite + Tailwind CSS
- 前端版本升级指上游 vue-pure-admin 发布了新版本，需评估是否需要同步升级

注意：
- 后端依赖仅分析有版本变化的包
- 前端如果检测到上游有新版本，分析其 Release Notes 中是否有破坏性变更、新特性值得跟进、或需要适配的地方
- 如有安全更新，需特别标注
- 如无破坏性变更，明确说明"无需适配"
PROMPT_EOF

    local response
    response=$(curl -sf -X POST "https://api.deepseek.com/chat/completions" \
        -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "$(jq -n \
            --arg prompt "${prompt}"$'\n\n'"${report}" \
            '{
                model: "deepseek-chat",
                messages: [{role: "user", content: $prompt}],
                temperature: 0.3,
                max_tokens: 3000
            }')" 2>/dev/null || true)

    if [[ -z "${response}" ]]; then
        log_warn "DeepSeek API 请求失败，跳过 AI 分析"
        echo "AI 分析暂时不可用。请人工查看上述更新的官方 changelog。"
        return
    fi

    local ai_content
    ai_content=$(echo "${response}" | jq -r '.choices[0].message.content // "AI 分析返回为空"' 2>/dev/null || echo "AI 分析解析失败")

    echo "${ai_content}"
}

# ==============================================================================
# 5. CNB Issue 管理
# ==============================================================================

# 查找已有的 open 的 dependency-check Issue
find_existing_issue() {
    local response
    response=$(curl -sf \
        "${CNB_API_ENDPOINT}/${CNB_REPO_SLUG}/-/issues?state=open&labels=${LABEL}&page=1&page_size=10" \
        -H "Accept: application/vnd.cnb.api+json" \
        -H "Authorization: Bearer ${CNB_TOKEN}" 2>/dev/null || echo "[]")

    echo "${response}" | jq -r '.[0].number // empty' 2>/dev/null || true
}

# 关闭旧 Issue
close_old_issue() {
    local issue_number="$1"

    log_info "关闭旧 Issue #${issue_number}"

    # 先添加评论说明原因
    curl -sf -X POST \
        "${CNB_API_ENDPOINT}/${CNB_REPO_SLUG}/-/issues/${issue_number}/comments" \
        -H "Accept: application/vnd.cnb.api+json" \
        -H "Authorization: Bearer ${CNB_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$(jq -n --arg body "此 Issue 已被 ${TODAY} 的新检测报告替代，自动关闭。" \
            '{body: $body}')" &>/dev/null || true

    # 关闭 Issue
    curl -sf -X PATCH \
        "${CNB_API_ENDPOINT}/${CNB_REPO_SLUG}/-/issues/${issue_number}" \
        -H "Accept: application/vnd.cnb.api+json" \
        -H "Authorization: Bearer ${CNB_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{"state": "closed", "state_reason": "not_planned"}' &>/dev/null || true
}

# 创建新 Issue
create_issue() {
    local title="$1"
    local body="$2"

    log_info "创建新 Issue: ${title}"

    local http_code
    http_code=$(curl -s -o /tmp/cnb-issue-resp.json -w "%{http_code}" \
        -X POST \
        "${CNB_API_ENDPOINT}/${CNB_REPO_SLUG}/-/issues" \
        -H "Accept: application/vnd.cnb.api+json" \
        -H "Authorization: Bearer ${CNB_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$(jq -n \
            --arg title "${title}" \
            --arg body "${body}" \
            '{
                title: $title,
                body: $body,
                labels: ["dependency-check"],
                priority: "P3"
            }')")

    if [[ "${http_code}" -ge 200 && "${http_code}" -lt 300 ]]; then
        local issue_number
        issue_number=$(jq -r '.number // "unknown"' /tmp/cnb-issue-resp.json)
        log_info "Issue 创建成功: #${issue_number}"
    else
        log_error "Issue 创建失败: HTTP ${http_code}"
        cat /tmp/cnb-issue-resp.json >&2 || true
    fi
}

# ==============================================================================
# 主流程
# ==============================================================================
main() {
    cd "${PROJECT_ROOT}"

    log_info "========== 依赖版本检测开始 =========="

    # 记录工具链版本（已在前面升级过）
    local uv_old="${UV_OLD_VER}"
    local uv_new="${UV_NEW_VER}"
    local bun_old="${BUN_OLD_VER}"
    local bun_new="${BUN_NEW_VER}"

    # 1. 检测后端更新
    log_info "检测后端依赖..."
    local backend_updates
    backend_updates=$(detect_backend_updates)

    # 2. 检测前端更新
    log_info "检测前端依赖..."
    local frontend_updates
    frontend_updates=$(detect_frontend_updates)

    # 3. 如果都没有更新，退出
    local toolchain_changed=false
    if [[ "${uv_old}" != "${uv_new}" || ( -n "${bun_old}" && "${bun_old}" != "${bun_new}" ) ]]; then
        toolchain_changed=true
    fi

    if [[ -z "${backend_updates}" && -z "${frontend_updates}" && "${toolchain_changed}" == false ]]; then
        log_info "所有依赖和工具链均为最新版本，无需报告。"
        exit 0
    fi

    # 4. 生成 Markdown 报告
    log_info "生成检测报告..."
    local report
    report=$(generate_report "${backend_updates}" "${frontend_updates}" \
        "${uv_old}" "${uv_new}" "${bun_old}" "${bun_new}")

    # 5. AI 分析
    log_info "调用 AI 分析..."
    local ai_result
    ai_result=$(ai_analysis "${report}")

    # 6. 组装 Issue 正文
    local issue_body
    issue_body=$(cat <<BODY_EOF
${report}

---

## AI 影响分析

${ai_result}

---

> 此 Issue 由每日定时依赖检测脚本自动生成。请根据 AI 分析结果决定是否需要手动更新依赖。
BODY_EOF
)

    local issue_title="📦 依赖更新检测报告 (${TODAY})"

    # 7. 关闭旧的同标签 Issue
    local old_issue
    old_issue=$(find_existing_issue)
    if [[ -n "${old_issue}" ]]; then
        close_old_issue "${old_issue}"
    fi

    # 8. 创建新 Issue
    create_issue "${issue_title}" "${issue_body}"

    log_info "========== 依赖版本检测完成 =========="
}

main "$@"
