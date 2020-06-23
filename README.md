# IDMA/XBR Examples

## Market configuration

The **IDMA test market** on [XBR/Rinkeby](https://github.com/crossbario/xbr-protocol/issues/127)
is using one WAMP routing realm for both market transactions and application data messaging:


| Config | Value
|--------|---------
| **Homepage** (XBR market) | `https://markets.international-data-monetization-award.com/idma`
| **URL** (WAMP market- and data-plane) | `wss://markets.international-data-monetization-award.com/ws`
| **Realm** (WAMP market- and data-plane) | `idma`
