cd /home/vagrant/blockchain-supply
echo "Python Libraries"
sudo pip install -r requirements.txt
sed -i '/scripts\/deploy.py/s/$/ --baseurl \"http:\/\/securesensing.comsys.rwth-aachen.de\/\"/' scripts/DEPLOY_ALL.sh
