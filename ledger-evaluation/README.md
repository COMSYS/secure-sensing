# Section V.A.3) Database & Tamperproof Storage

This README provides a step-by-step guide to running the experiments.

Code and evaluation scripts will be made publicly available on Github.

The artifacts can be used to validate the claims made in our paper regarding the performance of tamperproof storage (here realized as immutable ledger).
Specifically, we verify the following assertions:

1) A single fingerprint per transaction results in a compact transaction size of **267 Bytes**.
2) The preparation of a transaction that includes a single fingerprint, including signature calculation, takes only **20 milliseconds**, resulting in a **50 transactions per second**.

To conduct the evaluation, we employed a single server with Intel Core i3-7100U and 16 GB of RAM, and executed four Quorum nodes on it.
To simulate real-world inputs, we generate transactions using synthetic data from `json_data/fakedata1k.json`, which produces the hash `ec6fff2c0ae647a1e24962029b2c0d87e883184ed30234264c5d5162`.

### Step 0: Prerequisites

To execute the following commands, `vagrant` and `virtualbox` are required as dependencies.
We provide exemplary instructions for Ubuntu, but the installation is similar on any other Linux distribution:

```bash
# Update package list
sudo apt update
# Install required dependencies `virtualbox` and `vagrant` with apt
sudo apt install virtualbox vagrant
```

### Step 1: Initial deployment

To deploy the entire project, run the following setup command to create a virtual machine with all dependencies installed.
This step may take quite a while to complete.

```bash
# Install project and dependencies
# Note: This step takes up to 30 minutes!
vagrant up
```

### Step 2: Deployment of Nodes and Setup

After the virtual machine is set up, follow the instructions to start the blockchain, create clients and register them:

```bash
# SSH into set up VM
vagrant ssh

# Get root privileges and deploy
sudo su
cd /home/vagrant/blockchain-supply/
./scripts/DEPLOY_ALL.sh
```

### Step 3: Verification of Claims

> **Note**: All commands must be executed exclusively within the `/home/vagrant/blockchain-supply` directory.

#### Claim 1: Transaction Size

To determine the size of a single fingerprint transaction, run the following command:

```bash
python3.7 scripts/bc_tx_creator_gen.py --mode api --account storage/config/api_account.json --timing timings.json --maxtx 1 --txsize
```

The output of this command will include the following information:

```bash
Size in Bytes: 267
```


#### Claims 2: Transaction Preparation Time

To verify the time it takes to prepare transaction, execute the following command:

```bash
python3.7 scripts/bc_tx_creator_gen.py --mode api --account storage/config/api_account.json --timing timings.json --maxtx 1000
```

The output of this command will include the following information:

```bash
PREPARATION AVG:    zzz.yyyyyyyyyyyyyy
TRANSACTIONS / SEC: zzz.yyyyyyyyyyyyyy
```

For more detailed information on the measured times, please refer to `timings.json`.


## Step 4: Clean up

After successful evaluation, you may execute `vagrant destroy` to remove the virtual machine from the host system.
