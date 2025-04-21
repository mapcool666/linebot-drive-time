from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, LocationMessage, TextSendMessage
import googlemaps
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])
gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])

user_locations = {}

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
    user_id = event.source.user_id
    lat = event.message.latitude
    lng = event.message.longitude
    user_locations[user_id] = (lat, lng)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入目的地地址"))

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    if user_id not in user_locations:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請先傳送您的位置"))
        return
    origin = user_locations[user_id]
    destination = event.message.text
    try:
        directions = gmaps.directions(origin, destination, mode="driving")
        if directions:
            duration = directions[0]['legs'][0]['duration']['text']
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"開車約需 {duration}"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到路線"))
    except Exception as e:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="錯誤，請稍後再試"))

if __name__ == "__main__":
    app.run()