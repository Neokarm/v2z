packer {
  required_plugins {
    qemu = {
      version = ">= 1.0.2"
      source  = "github.com/hashicorp/qemu"
    }
  }
}

source "qemu" "fedora-toolbox" {
  iso_url              = "https://download.fedoraproject.org/pub/fedora/linux/releases/36/Cloud/x86_64/images/Fedora-Cloud-Base-36-1.5.x86_64.qcow2"
  iso_checksum         = "ca9e514cc2f4a7a0188e7c68af60eb4e573d2e6850cc65b464697223f46b4605"
  disk_image           = true
  output_directory     = "output"
  shutdown_command     = "echo 'packer' | sudo -S shutdown -P now"
  disk_size            = var.disk_size
  format               = "qcow2"
  disk_compression     = true
  accelerator          = "kvm"
  http_directory       = "."
  ssh_port             = 22
  ssh_private_key_file = var.private_keypair_path
  ssh_username         = var.ssh_username
  ssh_timeout          = "20m"
  vm_name              = "fedora-36-cloud-zadara-toolbox.qcow2"
  net_device           = "virtio-net"
  disk_interface       = "virtio"
  boot_wait            = "10s"
  cd_label             = "cidata"
  cd_content = {
    "meta-data" = file("./files/meta-data")
    "user-data" = templatefile("./files/user-data.pkrtpl.hcl", {
      public_key_content = file("${var.private_keypair_path}.pub")
      symp_update        = file("./files/symp-update")
    })
  }
}

build {
  name = "toolbox"
  sources = [
    "source.qemu.fedora-toolbox"
  ]

  provisioner "file" {
    source      = "./files/rpm-packages.txt"
    destination = "/tmp/rpm-packages.txt"
  }

  provisioner "file" {
    source      = "./files/python3-requirements.txt"
    destination = "/tmp/python3-requirements.txt"
  }

  # install dependencies
  provisioner "shell" {
    inline = [
      "echo 'Waiting for cloud-init to finish' && sudo cloud-init status --wait",
      "echo 'Updating dnf' && sudo dnf update -y",
      "echo 'Adding docker repo' && sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo'",
      "echo 'Adding hashicorp repo' && sudo dnf config-manager --add-repo https://rpm.releases.hashicorp.com/fedora/hashicorp.repo",
      "echo 'Adding virtio-win repo' && sudo dnf config-manager --add-repo https://fedorapeople.org/groups/virt/virtio-win/virtio-win.repo",
      "sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc"
      "echo 'Adding microsoft rhel 8 repo' && sudo dnf config-manager --add-repo https://https://packages.microsoft.com/config/rhel/8/prod.repo",
      "sudo dnf install -y $(cat rpm-packages.txt)",
      "python3 -m ensurepip",
      "python3 -m pip install -r /ymp/python3-requirements.txt",
      "python2 -m ensurepip",
      "sudo ln -s /usr/local/bin/python3.9 /usr/bin/python3"
    ]
  }

  # configure docker deamon
  provisioner "shell" {
    inline = [
      "sudo usermod -aG docker neokarm",
      "sudo usermod -aG docker fedora",
      "sudo systemctl enable docker",
      "sudo systemctl start docker",
    ]
  }

  # Install Powershell
  provisioner "shell" {
    inline = [
      "sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc",
      "curl https://packages.microsoft.com/config/rhel/8/prod.repo | sudo tee /etc/yum.repos.d/microsoft.repo",
      "sudo dnf install -y powershell"
    ]
  }

  provisioner "powershell" {
    inline = [
      "Set-PSRepository PSGallery -InstallationPolicy Trusted",
      "Install-Module -Name VMware.PowerCLI -Scope AllUsers",
      "Set-PowerCLIConfiguration -Scope AllUsers -ParticipateInCEIP $true -Confirm:$false",
      "Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Scope AllUsers -Confirm:$false"
      "
    ]
  }
  
  # Install aws cli
  provisioner "shell" {
    inline = [
      "echo 'Installing AWS'",
      "curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'",
      "unzip awscliv2.zip",
      "sudo ./aws/install",
      "rm -rf awscliv2.zip aws"
    ]
  }

  # configure MOTD
  provisioner "file" {
    source      = "./files/motd"
    destination = "/tmp/motd"
  }

  provisioner "shell" {
    inline = [
      "sudo mv /tmp/motd /etc/motd",
    ]
  }

  # Validate
  provisioner "shell" {
    inline = [
      "aws --version",
      "git --version",
      "python --version",
      "pip --version",
      "python3 --version",
      "pip3 --version",
      "docker --version",
      "terraform --version",
    ]
  }


  # Cleanup
  provisioner "shell" {
    inline = [
      "sudo cloud-init clean",
      "sudo yum clean all",
      "rm -rf /home/fedora/.ssh/authorized_keys",
      "touch /home/fedora/.ssh/authorized_keys",
      "chmod 0600 /home/fedora/.ssh/authorized_keys"
    ]
  }
}