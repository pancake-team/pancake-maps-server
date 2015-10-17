import logging
import asyncio
from aiohttp import web
import numpy as np
import png
import io

logger = logging.getLogger(__name__)

class HttpServer:

    def __init__(self, port, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._port = port

        self._app = None
        self._connections_factory = None
        self._server = None

    def configure_router(self, router):
        router.add_route('GET', '/', self.get_main_page)
        router.add_route('GET', '/map', self.request_map)
        router.add_route('GET', '/overlay', self.request_overlay)
        router.add_route('GET', '/terrain/{detail}/{y}/{x}.terrain', self.request_terrain)
        router.add_route('GET', '/terrain/layer.json', self.request_terrain_layer_json)
        router.add_static('/', 'static')

    @asyncio.coroutine
    def start(self):
        self._app = web.Application()
        self.configure_router(self._app.router)
        self._connections_factory = self._app.make_handler()
        self._server = yield from self._loop.create_server(self._connections_factory, '0.0.0.0', self._port)
        logger.info('Server started at port={}.'.format(self._port))

    @asyncio.coroutine
    def stop(self):
        self._server.close()
        yield from self._connections_factory.finish_connections()
        yield from self._app.finish()

    @asyncio.coroutine
    def request_map(self, request):
        pixels = np.zeros((256, 256, 3), np.uint8)
        pixels[:] = (0, 255, 0)
        buf = io.BytesIO()
        png.from_array(pixels, mode='RGB').save(buf)
        return web.Response(body=buf.getvalue())

    @asyncio.coroutine
    def request_overlay(self, request):
        pixels = np.zeros((256, 256, 4), np.uint8)
        pixels[:] = (255, 0, 0, 100)
        pixels[::16, :, :] = (255, 0, 0, 255)
        pixels[:, ::32, :] = (255, 0, 0, 255)
        buf = io.BytesIO()
        png.from_array(pixels, mode='RGBA').save(buf)
        return web.Response(body=buf.getvalue())

    @asyncio.coroutine
    def request_terrain(self, request):
        heights = np.zeros((65, 65), np.uint16)
        heights[:] = np.arange(0, 65000, 1000)
        heights = heights.reshape(-1)
        meta = np.array([15, 0], np.uint8)
        return web.Response(body=heights.tostring() + meta.tostring())

    @asyncio.coroutine
    def request_terrain_layer_json(self, request):
        return web.Response(text="""
{
  "tilejson": "2.1.0",
  "format": "heightmap-1.0",
  "version": "1.0.0",
  "scheme": "tms",
  "tiles": ["{z}/{x}/{y}.terrain"]
}
""", headers={'Access-Control-Allow-Origin': '*'})

    @asyncio.coroutine
    def get_main_page(self, request):
        with open('static/index.html', 'rb') as inp:
            return web.Response(body=inp.read())