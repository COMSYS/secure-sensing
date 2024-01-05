echo "Building Python 3.7 from Source"
sudo apt-get -y build-dep python3.7

mkdir -p /home/vagrant/deps && cd /home/vagrant/deps
wget --progress=bar:force https://www.python.org/ftp/python/3.7.7/Python-3.7.7.tar.xz
tar xfJ Python-3.7.7.tar.xz
cd Python-3.7.7
#./configure --enable-shared --enable-optimizations
./configure --enable-shared
make
sudo make install
cd ..

sudo ldconfig /usr/local/lib

sudo update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
sudo update-alternatives --install /usr/bin/python python /usr/local/bin/python3.7 2
sudo update-alternatives --install /usr/bin/pip pip /usr/local/bin/pip3.7 1
