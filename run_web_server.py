import logging
import asyncio
from pancake.web.server import HttpServer

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    server = HttpServer(8081, loop=loop)
    try:
        loop.run_until_complete(server.start())
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Stopping server...")
    finally:
        loop.run_until_complete(server.stop())
        logger.info('Server stopped!')
