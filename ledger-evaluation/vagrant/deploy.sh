cd /home/vagrant/blockchain-supply/

# Make root bash use vagrants bashrc
sudo cp /home/vagrant/.bashrc /root/.bashrc
source /home/vagrant/.bashrc

echo 'Use "vagrant ssh" to connect to the deployed container.'
echo 'You will need to run "sudo su" first and "cd /home/vagrant/blockchain-supply/" before running the commands from the documentation!'
