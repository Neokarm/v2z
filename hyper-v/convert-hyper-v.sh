#!/bin/bash  

source ./config 
LOG="log_for_last_run"
echo `date` > $LOG
TLOG="tee -a $LOG"
SYMP="/usr/bin/symp -q -k --url https://$SYMPIP -u $SYMPUSER -p $SYMPPASS -d $SYMPTENANT $SYMPPROJECT"


create_nk_vm() {
    local BOOT_VOL_ID="${2}"
    echo "NAME: $VM_NAME" >> $LOG
    echo "CPU: $CPU" >> $LOG
    echo "RAM: $RAM_MB" >> $LOG
    echo "BOOT DISK: $VMBOOTDISK" >> $LOG
    local VOLSTR="--boot-volumes id=$BOOT_VOL_ID:disk_bus=virtio:device_type=disk"
    local VMID=$($SYMP vm create -c id -f json --vcpu $CPU --ram ${RAM_MB} $VOLSTR $VM_NAME 2>&1 | $TLOG | jq -r .id | $TLOG)
    echo "created VM ID $VMID" >> $LOG
    echo $VMID
}

create_nk_volume() {
    local SOURCE_DISK=${1}
    local VM_NAME=${2}
    local DISK_NAME="boot"
    local DISK_SIZE_MB=$(du -m "$SOURCE_DISK" | cut -f1)
    local DISK_SIZE_GB=$(((${DISK_SIZE_MB}/1024)))
    POOLID=$($SYMP storage pool list -c name -c id -f json 2>>$LOG | jq ".[] | select( .name == \"$SYMPPOOLNAME\")" | jq -r .id )
    VOLID=$($SYMP volume create -c id --size $DISK_SIZE_GB --storage-pool $POOLID ${VM_NAME}-${DISK_NAME} 2>>$LOG | jq -r .id | $TLOG)
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
    local SOURCE_VM_PATH="${1}"

    echo "Source VM path: $SOURCE_VM_PATH" | $TLOG
    local SOURCE_DISK=$(find $SOURCE_VM_PATH -name "*-sda" -type f)
    echo "Migrating $SOURCE_DISK" | $TLOG
    local VOLID=$(disk_to_nk_volume "$SOURCE_DISK")
    echo "Creating VM $SOURCE_VM_PATH" | $TLOG
    local VMID=$(create_nk_vm "$SOURCE_VM_PATH" $VOLID)
    echo "$VMID VM Created" | $TLOG
    # find $SOURCE_VM_PATH -name "*.raw" -type f | while read line
    # do
    #     local SOURCE_DISK="$line"
    #     echo "Migrating $SOURCE_DISK" | $TLOG
    #     local VOLID=$(disk_to_nk_volume "$SOURCE_DISK")

    #     $SYMP vm volumes detach $IMPORTER_VM_ID $VOLID | $TLOG
    #     $SYMP vm volumes attach $VMID $VOLID | $TLOG
    # done
    echo "$VM_NAME received" | $TLOG;
}

TEMP_DIR=/data/$VM_NAME
mkdir $TEMP_DIR
export LIBGUESTFS_CACHEDIR=$DATA
export LIBGUESTFS_BACKEND_SETTINGS=force_tcg
export LIBGUESTFS_BACKEND=direct
virt-v2v -i disk "$VHD_PATH" -o local -os $TEMP_DIR -of raw
receive_vm $TEMP_DIR
