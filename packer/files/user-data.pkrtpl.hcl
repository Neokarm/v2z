#cloud-config
hostname: toolbox
ssh_authorized_keys:
  - ${ public_key_content }
users:
  - default
#   - name: neokarm
#     gecos: Neokarm user
#     primary_group: neokarm
#     passwd: "$6$rounds=4096$o7ib3bkXRIFPWAId$GPV5HLt1BgBgTtxrgJ.a3pHpPJ/HEQ.jMF/G0YN90U/i7/EYcRS1q/xEZNthB4E1gSSzVjdMWWiRFJ25I/RdP1"
#     lock_passwd: false
#     chpasswd: { expire: True }
#     sudo: ['ALL=(ALL) NOPASSWD:ALL']
# chpasswd:
#   list: |
#     neokarm:Neok@rmRules!
#   expire: True
write_files:
  - path: /usr/bin/symp-update
    owner: root:root
    permissions: '755'
    content: |
      ${indent(6, symp_update)}