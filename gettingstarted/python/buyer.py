# coding=utf8

import sys
import binascii
import argparse
from uuid import UUID
from pprint import pformat

import eth_keys
import web3

import txaio
txaio.use_twisted()

from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning

from autobahn.wamp import cryptosign
from autobahn.wamp.types import SubscribeOptions
from autobahn.wamp.serializer import CBORSerializer

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.twisted.xbr import SimpleBuyer


class XbrDelegate(ApplicationSession):

    def __init__(self, config=None):
        self.log.info('{klass}.__init__(config={config})', klass=self.__class__.__name__, config=config)

        ApplicationSession.__init__(self, config)

        self._ethkey_raw = config.extra['ethkey']
        self._ethkey = eth_keys.keys.PrivateKey(self._ethkey_raw)
        self._ethadr = web3.Web3.toChecksumAddress(self._ethkey.public_key.to_canonical_address())

        self.log.info("Client (delegate) Ethereum key loaded (adr=0x{adr})",
                      adr=self._ethadr)

        self._key = cryptosign.SigningKey.from_key_bytes(config.extra['cskey'])
        self.log.info("Client (delegate) WAMP-cryptosign authentication key loaded (pubkey=0x{pubkey})",
                      pubkey=self._key.public_key())

        self._running = True

    def onUserError(self, fail, msg):
        self.log.error(msg)
        self.leave('wamp.error', msg)

    async def onJoin(self, details):
        print('Buyer session joined', details)
        try:
            delegate_key = self._ethkey_raw
            delegate_adr = self._ethkey.public_key.to_canonical_address()
            print('Using delegate adr:', delegate_adr)

            config = await self.call('xbr.marketmaker.get_config')
            print('Using market maker adr:', config['marketmaker'])

            market_maker_adr = binascii.a2b_hex(config['marketmaker'][2:])
            max_price = 100 * 10 ** 18
            buyer = SimpleBuyer(market_maker_adr, delegate_key, max_price)
            balance = await buyer.start(self, details.authid)
            balance = int(balance / 10 ** 18)
            print("Remaining balance in active payment channel: {} XBR".format(balance))

            async def on_event(key_id, enc_ser, ciphertext, details=None):
                print('Received event {}, encrypted with key_id={}'.format(details.publication, UUID(bytes=key_id)))
                try:
                    payload = await buyer.unwrap(key_id, enc_ser, ciphertext)
                except:
                    self.log.failure()
                    self.leave()
                else:
                    print('Unencrypted event payload: {}'.format(pformat(payload)))

            await self.subscribe(on_event, "io.crossbar.example", options=SubscribeOptions(details=True))
        except:
            self.log.failure()
            self.leave()
        else:
            self.log.info('Buyer session ready! Waiting to receive events ..')

    def onLeave(self, details):
        self.log.info('{klass}.onLeave(details={details})', klass=self.__class__.__name__, details=details)

        self._running = False

        if details.reason == 'wamp.close.normal':
            self.log.info('Shutting down ..')
            # user initiated leave => end the program
            self.config.runner.stop()
            self.disconnect()
        else:
            # continue running the program (let ApplicationRunner perform auto-reconnect attempts ..)
            self.log.info('Will continue to run (reconnect)!')

    def onDisconnect(self):
        self.log.info('{klass}.onDisconnect()', klass=self.__class__.__name__)

        try:
            reactor.stop()
        except ReactorNotRunning:
            pass


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('-d',
                        '--debug',
                        action='store_true',
                        help='Enable debug output.')

    parser.add_argument('--url',
                        dest='url',
                        type=str,
                        default='ws://localhost:8070/ws',
                        help='The router URL (default: "ws://localhost:8070/ws").')

    parser.add_argument('--realm',
                        dest='realm',
                        type=str,
                        default='idma',
                        help='The realm to join (default: "idma").')

    parser.add_argument('--ethkey',
                        dest='ethkey',
                        type=str,
                        help='Member private Ethereum key (32 bytes as HEX encoded string)')

    parser.add_argument('--cskey',
                        dest='cskey',
                        type=str,
                        help='Member client private WAMP-cryptosign authentication key (32 bytes as HEX encoded string)')

    args = parser.parse_args()

    if args.debug:
        txaio.start_logging(level='debug')
    else:
        txaio.start_logging(level='info')

    extra = {
        'ethkey': binascii.a2b_hex(args.ethkey),
        'cskey': binascii.a2b_hex(args.cskey),
    }

    runner = ApplicationRunner(url=args.url, realm=args.realm, extra=extra, serializers=[CBORSerializer()])

    try:
        runner.run(XbrDelegate, auto_reconnect=True)
    except Exception as e:
        print(e)
        sys.exit(1)
    else:
        sys.exit(0)
