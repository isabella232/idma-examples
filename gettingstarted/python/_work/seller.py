# coding=utf8

import txaio
txaio.use_twisted()

from txaio import time_ns, make_logger

import argparse
import treq

import sys
import binascii
import argparse

import eth_keys
import web3
import uuid

import txaio
txaio.use_twisted()

from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning

from autobahn.wamp.types import PublishOptions
from autobahn.wamp.serializer import CBORSerializer
from autobahn.wamp import cryptosign

from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.twisted.xbr import SimpleSeller


class HttpProbe(object):
    """
    HTTP test probe able to measure response time and size to a testee URL.
    """
    log = make_logger()

    def __init__(self, url, reactor=None, headers=None, timeout=5, repeat=5):
        """

        :param reactor: Twisted reactor to run under.
        :param url: URL of the testee to issue HTTP request to.
        :param headers: optional HTTP header to send when testing the target URL.
        :param timeout: Timeout in seconds for each request.
        :param repeat: Number of requests to issue (sequentially). Results are collected for all requests.
        """
        if reactor is None:
            from twisted.internet import reactor
        self._reactor = reactor
        self._url = url
        self._headers = headers
        self._timeout = timeout
        self._repeat = repeat

    async def run(self):
        """
        Issue the test request setup and collect results.

        :return: Collected results for all requests (the number of requests is determined by ``repeat``).
        """
        results = []
        for i in range(self._repeat):
            res = await self._do_request()
            results.append(res)
        return results

    async def _do_request(self):
        res = {
            'received': 0,
            'started': time_ns(),
        }

        def collect(data):
            res['received'] += len(data)

        # https://treq.readthedocs.io/en/release-20.3.0/api.html#treq.request
        # https://twistedmatrix.com/documents/current/api/twisted.web.iweb.IResponse.html
        response = await treq.get(self._url, reactor=self._reactor, headers=self._headers, timeout=self._timeout,
                                  persistent=False, allow_redirects=False, browser_like_redirects=False)

        res['version'] = 'HTTP/{}.{}'.format(response.version[1], response.version[2])
        res['code'] = response.code
        res['length'] = response.length

        await treq.collect(response, collect)

        res['ended'] = time_ns()
        res['duration'] = res['ended'] - res['started']
        return res


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

        self._probes = {}

    def init_probe(self, url):
        probe_id = uuid.UUID()
        self._probes[probe_id] = HttpProbe(url, repeat=5)
        return probe_id.bytes

    def onUserError(self, fail, msg):
        self.log.error(msg)
        self.leave('wamp.error', msg)

    async def onJoin(self, details):
        print('Seller session joined', details)
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
        except:
            self.log.failure()
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
        print('Seller session joined', details)
