#!/bin/bash
source symp_config.env

[ -d "$CONVERTED_VOLUMES_PATH" ] || mkdir "$CONVERTED_VOLUMES_PATH"
VMS_TO_CONVERT=$(cat convertlist.txt)

export_vm_properties() {
    local VM_NAME="${1}"
    local VM_FILE=$(find "$HYPERV_IMPORTER_VMS_PATH/$VM_NAME" -iname '*.xml' -type f)

    if [ -z "$VM_FILE" ]; then
        local VMRAM=$(cat "$HYPERV_IMPORTER_VMS_PATH/$VM_NAME/ram.txt")
        local VMCPU=$(cat "$HYPERV_IMPORTER_VMS_PATH/$VM_NAME/cpu.txt")
    else
        local VMCPU=$(xmlstarlet sel -t -v /configuration/settings/processors/count "$VM_FILE")
        local VMRAM=$(xmlstarlet sel -t -v /configuration/settings/memory/bank/size "$VM_FILE")
    fi
    local VM_NAME_NO_SPACES=$(echo ${VM_NAME} | sed 's/ //g')
    local SERIALIZATION_PATH="$CONVERTED_VOLUMES_PATH/$VM_NAME_NO_SPACES"
    [ -d "$SERIALIZATION_PATH" ] || mkdir "$SERIALIZATION_PATH"

    typeset -p VMCPU >>"$SERIALIZATION_PATH/VM_PROPERTIES.env"
    typeset -p VMRAM >>"$SERIALIZATION_PATH/VM_PROPERTIES.env"
}
convert_disk() {
    local DISK_PATH="${1}"
    local OUTPUT_PATH=$(echo ${2} | sed 's/ //g')
    local DISK_NAME=$(basename "$DISK_PATH")

    [ -d "$OUTPUT_PATH" ] || mkdir "$OUTPUT_PATH"

    sudo chown $USER "$DISK_PATH"
    echo "Converting $DISK_PATH, Output Path: $OUTPUT_PATH"
    export LIBGUESTFS_CACHEDIR=$OUTPUT_PATH
    export LIBGUESTFS_BACKEND_SETTINGS=force_tcg
    virt-v2v -i disk "$DISK_PATH" -o local -x -v -os "$OUTPUT_PATH" -of raw
    if [ $? -ne 0 ]; then
        echo "virt-v2v failed, attempting to convert using qemu-img"
        local OUTPUT_DISK_NAME=$(echo ${DISK_NAME} | sed 's/ //g')
        qemu-img convert -p -O raw "$DISK_PATH" "$OUTPUT_PATH"/"$OUTPUT_DISK_NAME".raw
    fi
}
convert_vm_disks() {
    local VMPath="${1}"
    local VMName="${2}"
    local OUTPUT_DIR="$CONVERTED_VOLUMES_PATH/$VMName"
    local DISKS_LOCATION="$VMPath/$VMName/Virtual Hard Disks/"

    export -f convert_disk
    find "$DISKS_LOCATION" -type f -exec sh -c "convert_disk '{}' '$OUTPUT_DIR'" \;
}


for vm in $VMS_TO_CONVERT; do
    convert_vm_disks "$HYPERV_IMPORTER_VMS_PATH" "$vm"
    export_vm_properties "$vm"
done
