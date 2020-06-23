# coding=utf8

# connect to WAMP router, join a XBR realm (with WAMP-cryptosign authentication), and
# subscribe to (XBR encrypted) events buying data encryption keys

import sys
import pyqrcode
import argparse
import binascii
from uuid import UUID
from pprint import pformat

import eth_keys
import web3

import txaio
txaio.use_twisted()

from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.twisted.xbr import SimpleBuyer

from autobahn.wamp.types import SubscribeOptions
from autobahn.wamp.serializer import CBORSerializer
from autobahn.wamp import cryptosign

from autobahn.xbr import load_or_create_profile


class XbrDelegate(ApplicationSession):

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        self._ethkey_raw = config.extra['ethkey']
        self._ethkey = eth_keys.keys.PrivateKey(self._ethkey_raw)
        self._ethadr = web3.Web3.toChecksumAddress(self._ethkey.public_key.to_canonical_address())
        self._key = cryptosign.SigningKey.from_key_bytes(config.extra['cskey'])
        self._running = True

    def onUserError(self, fail, msg):
        self.leave('wamp.error', msg)

    async def onJoin(self, details):
        self.log.info('{klass}.onJoin(details={details})', klass=self.__class__.__name__, details=details)

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
        except Exception as e:
            self.log.failure()
            self.config.extra['error'] = e
        finally:
            self.leave()

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

    args = parser.parse_args()

    if args.debug:
        txaio.start_logging(level='debug')
    else:
        txaio.start_logging(level='info')

    profile = load_or_create_profile()

    privkey = eth_keys.keys.PrivateKey(profile.ethkey)
    adr_raw = privkey.public_key.to_canonical_address()
    eth_adr = web3.Web3.toChecksumAddress(adr_raw)
    eth_adr_qr = pyqrcode.create(eth_adr, error='L', mode='binary').terminal()
    print('Delegate Ethereum address is {}:\n{}'.format(eth_adr, eth_adr_qr))

    extra = {
        'ethkey': profile.ethkey,
        'cskey': profile.cskey,
    }

    runner = ApplicationRunner(url=profile.market_url, realm=profile.market_realm, extra=extra,
                               serializers=[CBORSerializer()])

    try:
        runner.run(XbrDelegate, auto_reconnect=True)
    except Exception as e:
        print(e)
        sys.exit(1)
    else:
        sys.exit(0)
