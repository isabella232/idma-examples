import txaio
txaio.use_twisted()

from txaio import time_ns, make_logger

import argparse
import treq


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


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('-d',
                        '--debug',
                        action='store_true',
                        help='Enable debug output.')

    parser.add_argument('--gateway',
                        dest='gateway',
                        type=str,
                        default='http://localhost:1545',
                        help='Ethereum HTTP gateway URL or None for auto-select.')

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

    parser.add_argument('--market',
                        dest='market',
                        type=str,
                        help='Market OID in which to open a channel.')

    parser.add_argument('--marketmaker',
                        dest='marketmaker',
                        type=str,
                        help='Market maker address for the channel.')

    parser.add_argument('--channel',
                        dest='channel',
                        type=str,
                        help='Channel OID for the new channel.')

    parser.add_argument('--channel_type',
                        dest='channel_type',
                        type=int,
                        help='Type of channel to open: 1=paying, 2=payment')

    parser.add_argument('--delegate',
                        dest='delegate',
                        type=str,
                        help='Address of delegate allowed to use the channel for off-chain transactions.')

    parser.add_argument('--recipient',
                        dest='recipient',
                        type=str,
                        help='The address of the beneficiary for any channel payout when the channel is closed.')

    parser.add_argument('--amount',
                        dest='amount',
                        type=int,
                        help='Channel amount (in market coins).')

    args = parser.parse_args()

    if args.debug:
        txaio.start_logging(level='debug')
    else:
        txaio.start_logging(level='info')

    if args.gateway:
        w3 = web3.Web3(web3.Web3.HTTPProvider(args.gateway))
    else:
        from web3.auto import w3

    if not w3.isConnected():
        print('Could not connect to Web3/Ethereum at: {}'.format(args.gateway or 'auto'))
        sys.exit(1)
    else:
        print('Using web3.py {}, connected to provider {}'.format(hlid('v' + web3.__version__),
                                                                  hlid(args.gateway or 'auto')))
    xbr.setProvider(w3)

    assert args.channel_type in [ActorType.PROVIDER, ActorType.CONSUMER, ActorType.PROVIDER_CONSUMER]

    extra = {
        'w3': w3,
        'ethkey': binascii.a2b_hex(args.ethkey),
        'cskey': binascii.a2b_hex(args.cskey),
        'market_oid': UUID(args.market),
        'channel_oid': UUID(args.channel),
        'channel_type': args.channel_type,
        'delegate_adr': binascii.a2b_hex(args.delegate[2:]),
        'marketmaker_adr': binascii.a2b_hex(args.marketmaker[2:]),
        'recipient_adr': binascii.a2b_hex(args.recipient[2:]),
        'amount': args.amount * 10**18,
    }

    runner = ApplicationRunner(url=args.url, realm=args.realm, extra=extra, serializers=[CBORSerializer()])

    try:
        runner.run(XbrDelegate, auto_reconnect=True)
    except Exception as e:
        print(e)
        sys.exit(1)
    else:
        sys.exit(0)
