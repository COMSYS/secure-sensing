echo "Apache Webserver and ModWSGI"
sudo apt-get -y install apache2 apache2-dev libffi-dev libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev build-essential

echo " - ModWSGI 4.7.1"
cd /home/vagrant/deps
wget --progress=bar:force https://github.com/GrahamDumpleton/mod_wsgi/archive/4.7.1.tar.gz
tar -xvzf 4.7.1.tar.gz
cd mod_wsgi-4.7.1
echo "/usr/local/lib/python3.7" | sudo tee -a /etc/ld.so.conf
sudo /sbin/ldconfig -v
./configure --with-python=/usr/local/bin/python3.7
make
sudo make install
echo "LoadModule wsgi_module /usr/lib/apache2/modules/mod_wsgi.so" | sudo tee /etc/apache2/mods-available/wsgi.load
sudo a2enmod wsgi
sudo systemctl restart apache2
cd ..

echo " - Setting up vHost"
sudo cp /home/vagrant/blockchain-supply/vagrant/vhost.conf /etc/apache2/sites-available/securesensing.conf
sudo a2ensite securesensing
sudo systemctl reload apache2
echo -e "127.0.0.1\tlbma.comsys.rwth-aachen.de" | sudo tee -a /etc/hosts
