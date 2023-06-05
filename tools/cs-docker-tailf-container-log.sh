#!/usr/bin/bash

notail=false
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
  --notail)
    notail=true
    shift
    ;;
  *)
    name="$1"
    shift
    ;;
  esac
done

container_id_number=$(docker ps --no-trunc | grep $name | grep -v pause | awk '{print $1}' | wc -l)

if [[ $container_id_number -gt 1 ]]; then
  echo "ERROR: input can not calc uniqe container"
  docker ps --no-trunc | grep $1 | grep -v pause
  exit 1
else
  container_id=$(docker ps --no-trunc | grep $name | grep -v pause | awk '{print $1}')
  container_name=$(docker ps --no-trunc | grep $container_id | awk '{print $NF}')
  echo container_id is $container_id
  echo container_name is $container_name
fi

path="/var/lib/docker/containers/$container_id/$container_id-json.log"
if [ -f $path ]; then
  echo container_log_path is $path
  if $notail; then
    echo "you can tail container log use: tail -f $path"
  else
    tail -f $path
  fi
else
  echo "ERROR: $path not exist"
fi

