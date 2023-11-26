import json
import os
from linebot.v3 import (WebhookHandler)
from linebot.v3.messaging import (Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage)
from linebot.v3.exceptions import (InvalidSignatureError)
from linebot.v3.webhooks import (MessageEvent, TextMessageContent)

from langchain.chains import ConversationChain
from langchain.chat_models import BedrockChat
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

#環境変数の呼び出し
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(channel_secret=LINE_CHANNEL_SECRET)

prompt_template = PromptTemplate(
    input_variables=['history', 'input'],
    template='''The foolowing is a friendlyconversation between a human and an AI.
    The AI is talkative and provides lots of specific details from its context.
    If the AI does not know the answer to a question, it truthfully says it does not know.

Current conversation:
<history>
{history}
</history>
{input}'''
)

llm = BedrockChat(model_id="anthropic.claude-instant-v1", 
                region_name="us-east-1")

def conversation(input: str, session_id: str):
    memory = ConversationBufferMemory(
        human_prefix="H",
        ai_prefix="A")

    chain =ConversationChain(
        llm=llm,
        memory=memory,
        verbose=True,
    )

    return chain.predict(input=input)

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    user_id = event.source.user_id
    text = event.message.text

    with ApiClient(line_configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        response = conversation(input=text, session_id=user_id)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response)]
            )
        )

def lambda_handler(event, context):
    signature = event['headers']['x-line-signature']
    body =event['body']
    line_handler.handle(body, signature)

    return{
        'statusCode': 200,
        'body': 'OK'
    }
