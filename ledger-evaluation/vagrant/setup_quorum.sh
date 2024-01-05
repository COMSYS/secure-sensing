echo "Quorum"
cd /home/vagrant/deps

echo " - Go 1.14"
wget --progress=bar:force https://dl.google.com/go/go1.14.4.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.14.4.linux-amd64.tar.gz

echo "export PATH=\$PATH:/usr/local/go/bin" | sudo tee -a /home/vagrant/.bashrc
source /home/vagrant/.bashrc
PATH=$PATH:/usr/local/go/bin

echo " - Build Quorum"
git clone https://github.com/jpmorganchase/quorum.git
cd quorum
git checkout 51e1f6354665ed7f6b098bf53ce3fd5944e14cb6
make all
QUORUMROOT=`pwd`
echo "export PATH=\$PATH:$QUORUMROOT/build/bin" | sudo tee -a /home/vagrant/.bashrc
PATH=$PATH:$QUORUMROOT/build/bin
source /home/vagrant/.bashrc
cd ..

mkdir /home/vagrant/eth
mkdir /home/vagrant/eth/nodes
cp /home/vagrant/blockchain-supply/vagrant/genesis.json /home/vagrant/eth/nodes
