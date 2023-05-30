#!/bin/bash -x
WORK_DIR=`dirname $0`
cd $WORK_DIR
PROJECT_DIR=`pwd`

git log --pretty=format:"%h %ad %s" --date=short -30 > ChangeLog
openssl enc -aes-256-cbc -salt -in ChangeLog -out doc/ChangeLog -pass pass:astute -md sha256

if [ -z $BUILD_NUMBER ];then BUILD_NUMBER=0; fi
BIG_NUMBER=$(crudini --get setup.cfg metadata big_number_version)
SMALL_NUMBER=$(crudini --get setup.cfg metadata small_number_version)
PBR_VERSION=$BIG_NUMBER.$SMALL_NUMBER.$BUILD_NUMBER
export PBR_VERSION

rm -rf dist
python setup.py sdist
