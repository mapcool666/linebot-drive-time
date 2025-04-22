
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, LocationMessage, TextSendMessage
import googlemaps

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])
gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    user_location = (event.message.latitude, event.message.longitude)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="請輸入你要前往的地址：")
    )
    user_id = event.source.user_id
    app.user_locations[user_id] = user_location

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    if user_id in app.user_locations:
        origin = app.user_locations[user_id]
        destination = event.message.text

        try:
            directions_result = gmaps.directions(origin, destination, mode="driving")
            if directions_result:
                duration = directions_result[0]['legs'][0]['duration']['text']
                reply = f"從你的位置開車到「{destination}」大約需要：{duration}"
            else:
                reply = "找不到路線，請確認地址是否正確。"
        except Exception as e:
            reply = f"發生錯誤：{str(e)}"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )
        del app.user_locations[user_id]
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請先傳送你的位置。")
        )

app.user_locations = {}

if __name__ == "__main__":
    app.run()
