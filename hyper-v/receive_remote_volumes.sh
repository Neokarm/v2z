#!/bin/bash
source ./symp_config.env
NIC='eth0'
# sudo wondershaper "$NIC" 200000000 200000000

# NETCAT_PORT=19000


sudo groupadd fuse
sudo usermod -a centos -G fuse
sudo sed -i '/^#.*user_allow_other/s/^# //' /etc/fuse.conf

[ -d "$NEOKARM_HYPERV_REMOTE_PATH" ] || mkdir "$NEOKARM_HYPERV_REMOTE_PATH"

#wget --no-check-certificate http://"$SYMPIP"/client.rpm
#sudo yum install -y client.rpm
SYMP="/usr/bin/symp -q -k --url https://$SYMPIP -u $SYMPUSER -p $SYMPPASS -d $SYMPTENANT $SYMPPROJECT"

echo "Mounting remote $HYPERV_IMPORTER_USER@$HYPERV_IMPORTER_IP:$HYPERV_IMPORTER_CONVERTED_PATH" | $TLOG
echo "To local $NEOKARM_HYPERV_REMOTE_PATH" | $TLOG

sshfs -o IdentityFile="$HYPERV_IMPORTER_PEM" -C \
    "$HYPERV_IMPORTER_USER"@"$HYPERV_IMPORTER_IP":"$HYPERV_IMPORTER_CONVERTED_PATH" \
    "$NEOKARM_HYPERV_REMOTE_PATH" \
    -o allow_other

# nc version: faster but unstable
# receive_disk() {
#     local LOCAL_TARGET=$(basename "${1}")
#     local VM_NAME="${2}"
#     echo "local target: ${LOCAL_TARGET}"
#     nc -l $NETCAT_PORT | gzip -d | dd bs=16M of="$LOCAL_TARGET" &
#     sleep 1
#     SOURCE_REMOTE_PATH="$HYPERV_IMPORTER_CONVERTED_PATH/$VM_NAME/$LOCAL_TARGET"
#     echo "remote source: "$SOURCE_REMOTE_PATH
#     SEND_COMMAND="dd bs=16M if='$SOURCE_REMOTE_PATH' | gzip -c | nc $NEOKARM_IMPORTER_IP $NETCAT_PORT;"
#     # SEND_COMMAND="echo 'remote source: '$SOURCE_REMOTE_PATH"
#     echo "send command: $SEND_COMMAND"
#     ssh -ni $HYPERV_IMPORTER_PEM $HYPERV_IMPORTER_USER@$HYPERV_IMPORTER_IP "$SEND_COMMAND";
#     echo "$LOCAL_TARGET received"
# }
create_nk_vm() {
    local VM_VOLUMES_PATH="${1}"
    local BOOT_VOL_ID="${2}"
    local VM_NAME=$(basename $VM_VOLUMES_PATH)
    source "$VM_VOLUMES_PATH/VM_PROPERTIES.env"
    echo "NAME: $VM_NAME" >> $LOG
    echo "CPU: $VMCPU" >> $LOG
    echo "RAM: $VMRAM" >> $LOG
    echo "BOOT DISK: $VMBOOTDISK" >> $LOG
    local VOLSTR="--boot-volumes id=$BOOT_VOL_ID:disk_bus=virtio:device_type=disk"
    local VMID=`$SYMP vm create -c id --vcpu $VMCPU --ram ${VMRAM} $VOLSTR $VM_NAME 2>&1 | $TLOG | grep 'id' | awk '{print $4}'`
    echo "created VM ID $VMID" >> $LOG
    echo $VMID
}
create_nk_volume() {
    local SOURCE_DISK=${1}
    local VM_NAME=${2}
    local DISK_NAME=$(basename $SOURCE_DISK)
    local DISK_SIZE_MB=$(du -m "$SOURCE_DISK" | cut -f1)
    local DISK_SIZE_GB=$(((${DISK_SIZE_MB} / 1024)))
    POOLID=$($SYMP storage pool list -c id -c name -f json 2>>$LOG | grep -B1 -A1 "\"$SYMPPOOLNAME\"" | grep "\"id\":" | awk '{print $2}' | sed 's/"//g; s/,//g')
    VOLID=`$SYMP volume create -c id --size $DISK_SIZE_GB --storage-pool $POOLID ${VM_NAME}-Vol${DISK_NAME} 2>>$LOG | $TLOG | grep 'id' | awk '{print $4}'`
    echo $VOLID
}
receive_disk() {
    local SOURCE_FILE="${1}"
    local TARGET_DEVICE="${2}"
    echo "local target: ${TARGET_DEVICE}" >> $LOG
    # sudo dd bs=16M if="$SOURCE_FILE" of="$TARGET_DEVICE" >> $LOG
    dd bs=16M if="$SOURCE_FILE" | pv | sudo dd bs=16M of="$TARGET_DEVICE"
    echo "$LOCAL_TARGET received" >> $LOG
}
disk_to_nk_volume() {
    local SOURCE_DISK="${1}"
    local VOLID=$(create_nk_volume $SOURCE_DISK $VM_NAME)
    local IMPORTER_VM_ID=$($SYMP vm list --name $NEOKARM_IMPORTER_VM_NAME -f value -c id)
    $SYMP vm volumes attach $IMPORTER_VM_ID $VOLID >> $LOG
    local OUTPUT_DEVICE='/dev/'$(lsblk --output NAME -dn | grep -v vda)
    receive_disk $SOURCE_DISK $OUTPUT_DEVICE; 
    $SYMP vm volumes detach $IMPORTER_VM_ID $VOLID >> $LOG
    echo $VOLID
}
receive_vm() {
    unset VMID
    local VM_NAME="${1}"
    local SOURCE_VM_PATH="$NEOKARM_HYPERV_REMOTE_PATH/$VM_NAME"

    echo "Source VM path: $SOURCE_VM_PATH" | $TLOG
    local SOURCE_DISK=$(find $SOURCE_VM_PATH -name "*-sda" -type f)
    echo "Migrating $SOURCE_DISK" | $TLOG
    local VOLID=$(disk_to_nk_volume "$SOURCE_DISK")
    echo "Creating VM $SOURCE_VM_PATH" | $TLOG
    local VMID=$(create_nk_vm "$SOURCE_VM_PATH" $VOLID)
    echo "$VMID VM Created" | $TLOG
    find $SOURCE_VM_PATH -name "*.raw" -type f | while read line
    do
        local SOURCE_DISK="$line"
        echo "Migrating $SOURCE_DISK" | $TLOG
        local VOLID=$(disk_to_nk_volume "$SOURCE_DISK")

        $SYMP vm volumes detach $IMPORTER_VM_ID $VOLID | $TLOG
        $SYMP vm volumes attach $VMID $VOLID | $TLOG
    done
    echo "$VM_NAME received" | $TLOG;
}

VMS=$(ls "$NEOKARM_HYPERV_REMOTE_PATH")
echo "VMs: " | $TLOG
echo "$VMS" | $TLOG
for vm in $VMS; do
    receive_vm $vm
done

cd $HOME
sudo fusermount -u $NEOKARM_HYPERV_REMOTE_PATH