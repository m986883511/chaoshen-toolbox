#!/usr/bin/bash

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "you current dir can use git command"
else
    echo "your current dir not in git project"
    exit 1
fi

# 从环境变量中获取 token 值
GITHUB_TOKEN=${GITHUB_TOKEN:-}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
    -t | --token)
        GITHUB_TOKEN="$2"
        shift
        shift
        ;;
    *)
        shift
        ;;
    esac
done

# 检查 token 是否为空
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN is not set"
    exit 1
fi

push_url=$(git remote -v | grep push | awk '{print $2}' | sed 's/http[s]\?:\/\///g')
git_repo_author=$(echo $push_url | cut -d/ -f2)
push_url_with_token="https://$git_repo_author:$GITHUB_TOKEN@$push_url"

git pull --rebase
if [ "$?" != 0 ]; then
    echo "git pull --rebase failed, please fix it before push"
    exit 1
fi

not_push_commit=$(git log --branches --not --remotes --oneline --no-decorate)

if [[ -z "$not_push_commit" ]]; then
    echo "you have not commit need to push"
else
    echo "you will push this commit: $not_push_commit"
fi

read -p "Press Enter to push to $push_url: " input

if [[ -z "$input" ]]; then
    git push $push_url_with_token
    if [ "$?" != 0 ]; then
        echo "push failed"
        exit 1
    else
        echo "push success"
        git log --pretty=format:"%h %ad %s" --date=short -10
    fi
else
    echo "not press Enter, Exiting..."
    exit 1
fi
