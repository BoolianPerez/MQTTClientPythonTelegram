#!/usr/bin/env python3
import asyncio
import paho.mqtt.client as paho
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging

# Configura el registro de eventos
logging.basicConfig(level=logging.INFO)

# MQTT configuration
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC_SUBSCRIBE = "kids/yolo"
MQTT_TOPIC_PUBLISH = "pong"

# Telegram Bot token
TELEGRAM_BOT_TOKEN = "7484892111:AAFJoYCk66dzNE7gB-l0QQEXTXS1z6R5o28"

# Global variables
chat_id = None
application = None

# Create an event loop for async operations
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Function to handle incoming MQTT messages
def on_message(client, userdata, msg):
    global application, chat_id
    telegram_message = f"Topic: {msg.topic}\nMessage: {msg.payload.decode('utf-8')}"
    if chat_id:
        asyncio.run_coroutine_threadsafe(application.bot.send_message(chat_id=chat_id, text=telegram_message), loop)
    logging.info(f"MQTT Message: {telegram_message}")

# MQTT Client setup
mqtt_client = paho.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.subscribe(MQTT_TOPIC_SUBSCRIBE, 0)

# Function to handle Telegram /start command
async def start(update: Update, context: CallbackContext) -> None:
    global chat_id
    chat_id = update.message.chat_id
    await update.message.reply_text('Hi! I am your MQTT bot. Your chat ID has been set.')

# Function to handle Telegram /send command
async def send(update: Update, context: CallbackContext) -> None:
    if context.args:
        message = ' '.join(context.args)
        mqtt_client.publish(MQTT_TOPIC_PUBLISH, message)
        await update.message.reply_text(f"Message sent to MQTT: {message}")
        logging.info(f"Sent message to MQTT: {message}")
    else:
        await update.message.reply_text("Usage: /send <message>")

# Function to handle Telegram /receive command
async def receive(update: Update, context: CallbackContext) -> None:
    if chat_id:
        message = ' '.join(context.args)
        await context.bot.send_message(chat_id=chat_id, text=message)
    else:
        await update.message.reply_text("Chat ID not set. Please start the bot first.")

# Function to handle Telegram /chatid command
async def chatid(update: Update, context: CallbackContext) -> None:
    if chat_id:
        await update.message.reply_text(f"Your chat ID is: {chat_id}")
    else:
        await update.message.reply_text("Chat ID not set. Please start the bot first.")

# Function to handle any text message
async def handle_message(update: Update, context: CallbackContext) -> None:
    message = update.message.text
    logging.info(f"Received message: {message}")

# Set up the Telegram bot
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Add command handlers to the application
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("send", send))
application.add_handler(CommandHandler("receive", receive))
application.add_handler(CommandHandler("chatid", chatid))

# Add a handler for all text messages
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Start the MQTT loop
mqtt_client.loop_start()

# Start the Telegram bot
application.run_polling()
