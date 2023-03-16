import os
import openai
import ssl
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile='/etc/letsencrypt/live/' + os.environ["DOMAIN"] + '/fullchain.pem',
                            keyfile='/etc/letsencrypt/live/' + os.environ["DOMAIN"] + '/privkey.pem')


app = Flask(__name__)

# 環境変数から API キーを読み込む
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])
openai.api_key = os.environ["OPENAI_API_KEY"]


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # ChatGPT に問い合わせる
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=user_message,
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.5,
    )

    chatgpt_reply = response.choices[0].text.strip()

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=chatgpt_reply)
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, ssl_context=ssl_context)
