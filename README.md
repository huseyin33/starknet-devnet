## Introduction
A Flask wrapper of Starknet dummy network. Similar in purpose to Ganache.

## Install

This is an early stage of the project, so you'll need to clone this repo and install manually.

The version on the `master` branch works with versions `0.4.0` and `0.4.1`.

The branch `support-0.4.2` supports version `0.4.2`.

Run (preferably in a virtual environment):
```
pip install Flask[async] cairo-lang==<VERSION>
```


## Run
```
usage: python server.py [-h] [--host HOST] [--port PORT]

Run a local instance of Starknet devnet

optional arguments:
  -h, --help   show this help message and exit
  --host HOST  address to listen at; defaults to localhost
  --port PORT  the port to listen at; defaults to 5000
```

## Test
```
$ ./test.sh
```

## Interaction
Interact with this devnet as you would with the official Starknet [alpha network](https://www.cairo-lang.org/docs/hello_starknet/amm.html?highlight=alpha#interaction-examples).

## Hardhat integration
If you're using [the Hardhat plugin](https://github.com/Shard-Labs/starknet-hardhat-plugin), see [here](https://github.com/Shard-Labs/starknet-hardhat-plugin#testing-network) on how to edit its config file to integrate this devnet.
