# coding=utf8

# connect to WAMP router, join a XBR realm (with WAMP-cryptosign authentication), and publish (XBR encrypted) events
# to a topic selling data encryption keys

import sys
import pyqrcode
import argparse
import binascii
import uuid

import eth_keys
import web3

import txaio
txaio.use_twisted()

from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning

from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.twisted.xbr import SimpleSeller

from autobahn.wamp.serializer import CBORSerializer
from autobahn.wamp.types import PublishOptions
from autobahn.wamp import cryptosign
from autobahn.xbr import unpack_uint256, load_or_create_profile


class XbrDelegate(ApplicationSession):

    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        self._ethkey_raw = config.extra['ethkey']
        self._ethkey = eth_keys.keys.PrivateKey(self._ethkey_raw)
        self._ethadr = web3.Web3.toChecksumAddress(self._ethkey.public_key.to_canonical_address())
        self._key = cryptosign.SigningKey.from_key_bytes(config.extra['cskey'])
        self._running = True

    def onUserError(self, fail, msg):
        self.log.error(msg)
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

            api_id = uuid.UUID('627f1b5c-58c2-43b1-8422-a34f7d3f5a04').bytes
            topic = 'io.crossbar.example'
            counter = 1

            # 5 XBR / 10s
            price = 5 * 10 ** 18
            interval = 10

            seller = SimpleSeller(market_maker_adr, delegate_key)
            seller.add(api_id, topic, price, interval, None)

            balance = await seller.start(self)
            balance = int(balance / 10 ** 18)
            print("Remaining balance: {} XBR".format(balance))

            self.log.info('Seller session ready! Starting to publish events ..')
            running = True
            while running:
                payload = {'data': 'py-seller', 'counter': counter}
                key_id, enc_ser, ciphertext = await seller.wrap(api_id,
                                                                topic,
                                                                payload)

                pub = await self.publish(topic, key_id, enc_ser, ciphertext,
                                         options=PublishOptions(acknowledge=True))

                print('Published event {}: {}'.format(pub.id, payload))

                counter += 1
                await sleep(1)
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
