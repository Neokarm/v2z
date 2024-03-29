#!/bin/bash

TEMP_PATH="/tmp/symp-update"
RPM_NAME="client.rpm"

function printHelp(){

   # Print Help
   echo "Install and update the symp cli"
   echo
   echo "Syntax: symp-update -c <Cluster_NB> [-k]"
   echo "options:"
   echo "c     cluster IP/Hostname."
   echo "k     Allow insecure server connections when using SSL."
   echo
}

function setUp(){
  [ -d $TEMP_PATH ] || mkdir $TEMP_PATH
}

function cleanUp(){
  rm -r -d -f $TEMP_PATH
}

function exitWithError(){
  [ ! -z "$STDERR" ] && echo $STDERR >> /dev/stderr
  cleanUp
  exit 1
}

function getStatusCode(){
  [ -z "$CLUSTER_IP" ] && printHelp && exitWithError

  if [ "$INSECURE" = true ]; then
    RESPONSE_CODE=$(curl --head --fail --silent --insecure --max-time 5 --output /dev/null --dump-header - $RPM_ENDPOINT | grep HTTP | awk '{print $2}')
  else
    RESPONSE_CODE=$(curl --head --fail --silent --max-time 5 --output /dev/null --dump-header - $RPM_ENDPOINT | grep HTTP | awk '{print $2}')
  fi

  if [ -z "$RESPONSE_CODE" ] || [ $RESPONSE_CODE -ne 200 ]; then
    STDERR="The Cluster is not reachable"
    [ ! -z "$RESPONSE_CODE" ] && STDERR="The Cluster is not reachable, response code $RESPONSE_CODE"
    exitWithError
  fi
}

function installSymp(){
  getStatusCode
  setUp

  if [ "$INSECURE" = true ]; then
    curl --fail --silent --insecure --output $TEMP_PATH/$RPM_NAME $RPM_ENDPOINT
  else
    curl --fail --silent --output $TEMP_PATH/$RPM_NAME  $RPM_ENDPOINT
  fi
  [ ! -f "$TEMP_PATH/$RPM_NAME" ] && STDERR="The RPM was not downloaded properly, try again." && exitWithError
  sudo yum install -y $TEMP_PATH/$RPM_NAME
  cleanUp
}

### Main ###

while getopts ":c:k" opt; do
  case ${opt} in
    c )
      CLUSTER_IP=$OPTARG
      RPM_ENDPOINT="https://$CLUSTER_IP/$RPM_NAME"
      ;;
    k )
      INSECURE=true
      ;;
    * )
      printHelp
      exitWithError
      ;;  
  esac
done

installSymp