variable "private_keypair_path" {
  type        = string
  description = "Keypair private key path"
}

variable "ssh_username" {
  type        = string
  default     = "fedora"
  description = "The ssh username for the packer builder"
}

variable "disk_size" {
  type        = string
  default     = "10000M"
  description = "VM disk size"
}