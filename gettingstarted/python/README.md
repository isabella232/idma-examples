# XBR Buyer and Seller in Python

This folder contains examples for simple XBR seller and buyer delegates written in Python,
and using [Autobahn|Python](https://github.com/crossbario/autobahn-python).

## Prerequisites

You will need Python 3 (we test using CPython and PyPy). We recommend to create a new Python
virtual environment for all your tests:

```console
python3 -m venv ${HOME}/xbrtest1
source ${HOME}/xbrtest1/bin/activate
```

To install Autobahn with all necessary XBR support:

```console
pip3 install autobahn[twisted,encryption,serialization,xbr]
```

To test Autobahn:

```console
python3 -c "import autobahn; print(autobahn.version)"
```

Included with Autobahn is also the [XBR CLI](https://autobahn.readthedocs.io/en/latest/xbr-cli.html), which you can
test using:

```console
xbrnetwork version
```

## Getting started

### Registering in the XBR Network

To run the examples, you need to be registered in the [XBR Network](https://xbr.network/).

Registering is free and you don't need any crypto (Ether or tokens). But you will need a crypto
wallet, specifically, the only supported wallet currently is [MetaMask](https://metamask.io/).
After installing MetaMask (in Chrome or FireFox), please visit [https://planet.xbr.network/](https://planet.xbr.network/) to register.

### Joining the IDMA Data Market

The XBR Network consists of potentially many XBR data markets, and to buy or sell data in a given market,
you need to join that market and accept the market user terms.

To join the data market we've created for the IDMA contests, please visit the [IDMA market homepage](https://planet.xbr.network/market/1388ddf6fe364201b1aacb7e36b4cfb3).

### Initializing your XBR delegates

Selling or buying data on the XBR network is done by so-called "delegates", which are just pieces of software
run in the name of a user. For example, an installed XBR mobile app might act as a data seller delegate for the
users device the app is installed on.

Delegates can be buyers, sellers or buyer-and-sellers in a given market. Then, to buy or sell, the delegate will
be using an off-chain buyer-channel for payment transactions or seller-channel for payout transactions.

First, you will need the public address of your delegate. Usually, delegates generate a new Ethereum private key
when first started, and the public address for that key is printed or made accessible for the user.

### Opening XBR buyer/seller channels for your delegates

### Run your buyer/seller delegate
