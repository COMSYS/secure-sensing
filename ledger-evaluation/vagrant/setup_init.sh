sudo apt-get update
sudo apt-get -y upgrade

sudo apt-get -y install git gnupg curl build-essential zlib1g-dev libssl-dev libffi-dev

sudo apt-get remove python3*

echo "Fixing CA-Certificate..."
sudo sed -i 's/mozilla\/AddTrust_External_Root.crt/!mozilla\/AddTrust_External_Root.crt/' /etc/ca-certificates.conf
sudo su -c update-ca-certificates
