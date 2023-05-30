#!/bin/bash
WORK_DIR=$(cd `dirname $0`; pwd)
cd $WORK_DIR
VENV_NAME=$(crudini --get setup.cfg metadata conda_venv_name)
python_path=$(which python)
venv_path=$(dirname $(dirname $python_path))

if [ "/root/miniconda3/envs/$VENV_NAME" = "$venv_path" ]; then
  echo "in $VENV_NAME env, start work"
else
  echo "ERROR: not in $VENV_NAME env, exit"
  exit 1
fi

bash make.sh
package_base_name=$(crudini --get setup.cfg metadata name)
pip uninstall $package_base_name -y
pip install dist/$package_base_name-*.tar.gz
