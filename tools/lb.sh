#!/bin/bash
liquibase=$(which liquibase)

if [ -f $$liquibase ] 
then
	echo "unable to find liquibase, please install http://www.liquibase.org/index.html"
fi
DB=bitwarden.sqlite
MY_PATH=$(dirname $0)              # relative
MY_PATH=$( cd $MY_PATH && pwd )  # absolutized and normalized

$liquibase --classpath=$MY_PATH/sqlite-jdbc-3.21.0.1.jar --driver=org.sqlite.JDBC --url="jdbc:sqlite:$DB" --changeLogFile=$MY_PATH/../schema/bitwarden.sql update
