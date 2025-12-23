import cherrypy
import json
import time


class SchedulerService:
    exposed = True

    def __init__(self):
        # یک برنامه هفتگی ساده (شبیه‌سازی)
        # فرض می‌کنیم کلاس‌ها هر روز از ساعت ۸ صبح تا ۸ شب هستند
        self.schedule = {
            "start_hour": 8,
            "end_hour": 20
        }

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        # کنترلر این آدرس را صدا می‌زند: /check?room_id=Classroom_101
        if len(uri) > 0 and uri[0] == "check":
            room_id = params.get("room_id")

            # گرفتن ساعت فعلی سیستم
            current_hour = time.localtime().tm_hour

            # منطق: آیا الان در ساعت کاری هستیم؟
            is_booked = self.schedule["start_hour"] <= current_hour < self.schedule["end_hour"]

            # برای تست: همیشه می‌گوییم کلاس هست (True) تا سیستم کار کند
            # اگر خواستید سیستم خاموش شود، این را False کنید
            is_booked = True

            print(f"📅 Schedule Check for {room_id}: {'Booked' if is_booked else 'Free'}")
            return {"room_id": room_id, "booked": is_booked}

        return "Scheduler Service is Running..."


if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }

    # این سرویس روی پورت 8081 اجرا می‌شود (چون 8080 مال کاتالوگ است)
    cherrypy.config.update({
        'server.socket_host': '127.0.0.1',
        'server.socket_port': 8081
    })

    cherrypy.tree.mount(SchedulerService(), '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()