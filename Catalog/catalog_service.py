import cherrypy
import json


class CatalogService:
    exposed = True

    def __init__(self, settings_file):
        self.settings_file = settings_file
        # بارگذاری تنظیمات اولیه
        try:
            with open(self.settings_file) as f:
                self.catalog_data = json.load(f)
            print("✅ Catalog System Loaded.")
        except Exception as e:
            print(f"❌ Error loading catalog: {e}")

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        # پاسخ به درخواست سرویس‌های دیگر
        if len(uri) > 0:
            cmd = uri[0]
            if cmd == "broker":
                return self.catalog_data["broker"]
            elif cmd == "all":
                return self.catalog_data
            elif cmd == "rooms":
                return self.catalog_data["rooms"]

        return "IoT Catalog Service is Running..."


if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.tree.mount(CatalogService('catalog.json'), '/', conf)

    cherrypy.config.update({
        'server.socket_host': '127.0.0.1',
        'server.socket_port': 8080
    })

    cherrypy.engine.start()
    cherrypy.engine.block()