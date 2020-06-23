# coding=utf8

import sys
import pyqrcode
import argparse
import binascii

from pprint import pformat

import eth_keys
import web3

import txaio

txaio.use_twisted()

from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp.serializer import CBORSerializer
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
        self.leave('wamp.error', msg)

    async def onJoin(self, details):
        self.log.info('{klass}.onJoin(details={details})', klass=self.__class__.__name__, details=details)

        try:
            delegate_key = self._ethkey_raw
            delegate_adr = self._ethkey.public_key.to_canonical_address()
            await self._do_get_channel(delegate_key, delegate_adr)
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

    async def _do_get_channel(self, delegate_key, delegate_adr):
        print('*' * 100)
        channel = await self.call('xbr.marketmaker.get_active_payment_channel', delegate_adr)
        self.log.debug('{channel}', channel=pformat(channel))
        if channel:
            self.log.info('Active buyer (payment) channel found: {amount} amount',
                          amount=int(unpack_uint256(channel['amount']) / 10**18))
            balance = await self.call('xbr.marketmaker.get_payment_channel_balance', channel['channel_oid'])
            self.log.debug('{balance}', channel=pformat(balance))
            self.log.info('Current off-chain amount remaining: {remaining} [sequence {sequence}]',
                          remaining=int(unpack_uint256(balance['remaining']) / 10 ** 18), sequence=balance['seq'])
        else:
            self.log.info('No active buyer (payment) channel found!')
        print('.' * 100)
        channel = await self.call('xbr.marketmaker.get_active_paying_channel', delegate_adr)
        self.log.debug('{channel}', channel=pformat(channel))
        if channel:
            self.log.info('Active seller (paying) channel found: {amount} amount',
                          amount=int(unpack_uint256(channel['amount']) / 10**18))
            balance = await self.call('xbr.marketmaker.get_paying_channel_balance', channel['channel_oid'])
            self.log.debug('{balance}', channel=pformat(balance))
            self.log.info('Current off-chain amount remaining: {remaining} [sequence {sequence}]',
                          remaining=int(unpack_uint256(balance['remaining']) / 10 ** 18), sequence=balance['seq'])
        else:
            self.log.info('No active seller (paying) channel found!')
        print('*' * 100)


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
