#!/bin/bash
robot_webhook="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=d8ecf03a-2794-4f76-xxxx-0a2859bf9228"
need_exist_commands="jq curl trap"

function completed() {
    if [[ $1 -eq 0 ]]; then
        if [ ! -z "$2" ]; then
          echo -e "$2 success"
        fi
    else
        if [ ! -z "$2" ]; then
          echo -e "$2 failed"
        fi
        if [ ! -z "$3" ]; then
            echo -e "$3"
        fi
        exit 1
    fi
}

encrypt() {
  local plaintext="$1"
  local password="$2"
  local encrypted=$(echo -n "$plaintext" | openssl enc -aes-256-cbc -a -salt -pass "pass:$password")
  echo "$encrypted"
}

decrypt() {
  local encrypted="$1"
  local password="$2"
  local decrypted=$(echo "$encrypted" | openssl enc -aes-256-cbc -a -d -salt -pass "pass:$password")
  completed $? "" "decrypt webhook failed, maybe password is wrong"
  echo "$decrypted"
}

function check_command_exist() {
  for word in $1
  do
      type $word >/dev/null 2>&1
      completed $? "check command $word exist"
  done
}

function generate_json() {
    local key="$1"
    local value="$2"
    local json_string
    json_string=$(jq -nc --arg k "$key" --arg v "$value" '{ ($k): $v }' | tr -d '\n')
    echo "$json_string"
}

function decrypt_webhook() {
    if [[ -n $decrypt_password ]]; then
        echo decrypt "$robot_webhook" "$decrypt_password"
        robot_webhook=$(decrypt "$robot_webhook" "$decrypt_password")
    fi
    if [[ $robot_webhook != http* ]]; then
        echo "robot_webhook is $robot_webhook, not start with http/https"
        echo "maybe webhook need decrypt or decrypt failed"
        exit 1
    fi
    if [[ $robot_webhook == *"xxxx"* ]]; then
        echo "please use your own wechat robot webhook"
        exit 1
    fi
}

function send_msg(){
    cat > /tmp/wx-msg.sh << EOF
curl -s '$robot_webhook' \
   -H 'Content-Type: application/json' \
   -d '
   {
        "msgtype": "text",
        "text": {
            "content": "$1",
            "mentioned_mobile_list":["$2"]
        }
   }'
EOF
    send_result=$(sh /tmp/wx-msg.sh)
    code=$(echo $send_result | jq -r '.errcode')
    completed $code "send msg to robot" "failed send result: $send_result"
}

function finished() {
    echo "command exit $?"
    send_msg "desc: $task_name\ncmd: $task_command\nstate: exit $?"
}

function terminated() {
    echo "human terminated"
    send_msg "desc: $task_name\ncmd: $task_command\nstate: terminated"
}

function usage() {
    echo "need two arguments, first is task description, second is task command."
    echo ""
    exit 1
}

function usage {
    cat <<EOF
Usage: $0 COMMAND [options]

  COMMAND is your task command, like "bash a_long_time_task.sh"

Options:
    --name, -n <task_name>             give your task a name, not have space, default is "task"
    --decrypt, -d <decrypt_password>   if your webhook is encrypt, this is your decrypt password
    --help, -h                         Show this usage information
EOF
}

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            usage
            exit 0
            ;;
        -n|--name)
            task_name="$2"
            if [[ $task_name == *" "* ]]; then
                echo "error: task name can not contain space, use -h to see usage"
                exit 1
            fi
            shift 2
            ;;
        -d|--decrypt)
            decrypt_password="$2"
            shift 2
            echo "error: not support decrypt now, use -h to see usage"
            exit 1
            ;;
        *)
            if [[ -n "$task_command" ]]; then
                echo "error: only support one task command, use -h to see usage"
                exit 1
            fi
            task_command="$1"
            shift
            ;;
    esac
done

if [[ -z "$task_command" ]]; then
    echo "error: need task command, use -h to see usage"
    exit 1
fi

decrypt_webhook
trap finished EXIT
trap terminated 1 2 3 15
send_msg "desc: $task_name\ncmd: $task_command\nstate: start"
echo "Running command: $task_command"
eval ${task_command}