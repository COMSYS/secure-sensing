echo "MongoDB"
wget -qO - https://www.mongodb.org/static/pgp/server-4.2.asc | sudo apt-key add -
echo "deb http://repo.mongodb.org/apt/debian buster/mongodb-org/4.2 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.2.list
sudo apt-get update
sudo apt-get -y install mongodb-org mongodb-org-server
sudo systemctl daemon-reload
sudo systemctl start mongod
sudo systemctl enable mongod
