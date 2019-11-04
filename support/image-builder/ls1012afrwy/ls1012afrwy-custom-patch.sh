#!/bin/bash

echo "/dev/mmcblk0p3 swap swap defaults 0 0" >> /etc/fstab

chmod +x /usr/local/bin/resizefs.sh
ln -s /lib/systemd/system/resizefs.service /etc/systemd/system/multi-user.target.wants/resizefs.service
ln -s /lib/systemd/system/sshd-keygen.service /etc/systemd/system/multi-user.target.wants/sshd-keygen.service
ln -s /lib/systemd/system/sshd.service /etc/systemd/system/multi-user.target.wants/sshd.service

# ls1046a does not support grub2 efi boot yet. U-Boot loads /boot/vmlinuz directly.
# Make this symlink
vmlinuz_file=`ls -tu /boot/vmlinuz-* 2>/dev/null | head -n1`
test -n "$vmlinuz_file" && ln -sf "$vmlinuz_file" /boot/vmlinuz

