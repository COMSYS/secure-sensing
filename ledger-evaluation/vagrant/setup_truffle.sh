echo "NodeJS and Truffle"
echo " - NodeJS"
sudo su -c 'curl -sL https://deb.nodesource.com/setup_14.x | bash -'
sudo apt-get install -y nodejs


echo " - Truffle"
sudo npm install --unsafe-perm -g truffle
