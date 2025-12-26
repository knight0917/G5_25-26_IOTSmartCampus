import cherrypy
import json # Used for loading and dumping JSON data
import os # Used for robust file path handling

class CatalogService:
    exposed = True

    def __init__(self, settings_file):
        # Resolve path relative to this script to be safe
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_file = os.path.join(base_dir, settings_file)
        
        self.catalog_data = {}
        # Load settings initially
        self.load_catalog()

    def load_catalog(self):
        try:
            with open(self.settings_file) as f:
                self.catalog_data = json.load(f)
            print(f"✅ Catalog System Loaded from {self.settings_file}")
        except Exception as e:
            print(f"❌ Error loading catalog from {self.settings_file}: {e}")
            self.catalog_data = {}

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        # Handle GET requests for different endpoints
        if len(uri) == 0:
             return "IoT Catalog Service is Running..."
        
        cmd = uri[0]
        
        if cmd == "broker":
            return self.catalog_data.get("broker")
        elif cmd == "all":
            return self.catalog_data
        elif cmd == "rooms":
            # If requesting specific room: /rooms/room_id
            if len(uri) > 1:
                target_id = uri[1]
                
                # Check if requesting a sub-resource like /rooms/room_id/schedule
                sub_cmd = uri[2] if len(uri) > 2 else None

                rooms = self.catalog_data.get("rooms", [])
                found_room = None
                for room in rooms:
                    if room.get("room_id") == target_id:
                        found_room = room
                        break
                
                if not found_room:
                    cherrypy.response.status = 404
                    return {"error": "Room not found"}
                
                if sub_cmd == "schedule":
                    return found_room.get("schedule", [])
                elif sub_cmd == "thresholds":
                    return found_room.get("thresholds", {})
                
                return found_room

            # If requesting all rooms: /rooms
            return self.catalog_data.get("rooms", [])

        # Default fallback
        return {"error": "Invalid endpoint"}


if __name__ == '__main__':
    # Configuration for CherryPy
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    
    # Mount the application
    cherrypy.tree.mount(CatalogService('catalog.json'), '/', conf)

    # Configure the server
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0', # Listen on all interfaces
        'server.socket_port': 8080
    })

    # Start the engine
    cherrypy.engine.start()
    cherrypy.engine.block()
