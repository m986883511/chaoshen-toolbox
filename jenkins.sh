#!/bin/bash -x
# by: wang.chao
# date: 2023-5-8
# export BUILD_NUMBER=0; export JOB_NAME=kolla-zed; export GIT_BRANCH=master

WORK_DIR=`dirname $0`
cd $WORK_DIR
package_base_name=$(crudini --get setup.cfg metadata name)

if [ -z $BUILD_NUMBER ] || [ -z $JOB_NAME ] || [ -z $GIT_BRANCH ]; then
   echo "Not in jenkins!"
   exit -1
fi
if [[ "$GIT_BRANCH"x =~ "master" ]];then
   BRANCH_FLAG=3.999
else
   BRANCH_FLAG=${GIT_BRANCH##*v}
fi

ls dist |grep "^$package_base_name.*\.tar\.gz$" | wc -l | grep -q "^1$"
if [ $? -ne 0 ]; then
    echo "Error: $package_base_name*.tar.gz not found!"
    exit -1
fi

package_name=$(ls dist |grep "^$package_base_name.*\.tar\.gz$")
package_new_name=$package_base_name-$BRANCH_FLAG.$BUILD_NUMBER.tar.gz
/bin/cp dist/$package_name $package_new_name

IDENTITY=fileserver@192.222.1.150
FILEDIR=/var/lib/astute/fileserver/jenkins/jenkins1/production-kolla/$JOB_NAME/${GIT_BRANCH##*/}
md5sum $package_new_name > $package_new_name.md5
ssh $IDENTITY mkdir -p $FILEDIR/$BUILD_NUMBER
scp $package_new_name $package_new_name.md5 $IDENTITY:$FILEDIR/$BUILD_NUMBER/
ssh $IDENTITY "rm -rf $FILEDIR/latest;ln -sf $FILEDIR/$BUILD_NUMBER $FILEDIR/latest"
