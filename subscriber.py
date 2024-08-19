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
mqtt_topic_subscribe = "longa"
MQTT_TOPIC_PUBLISH = "Suscribtopr3"

# Telegram Bot token
TELEGRAM_BOT_TOKEN = ""

# Global variables
chat_id = None
application = None

# Create an event loop for async operations
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

topicos = []

# Function to handle incoming MQTT messages
def on_message(client, userdata, msg):
    print(msg.topic)
    print(msg.payload.decode('utf-8'))
    global application, chat_id
    telegram_message = f"Topic: {msg.topic}\nMessage: {msg.payload.decode('utf-8')}"
    if chat_id:
        asyncio.run_coroutine_threadsafe(application.bot.send_message(chat_id=chat_id, text=telegram_message), loop)
    logging.info(f"MQTT Message: {telegram_message}")

# MQTT Client setup
mqtt_client = paho.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.subscribe(mqtt_topic_subscribe, 0)

# Function to handle Telegram /start command
async def start(update: Update, context: CallbackContext) -> None:
    print(3232)
    global chat_id
    chat_id = update.message.chat_id
    await update.message.reply_text('Hi! I am your MQTT bot. Your chat ID has been set.')

# Function to handle Telegram /send command
async def send(update: Update, context: CallbackContext) -> None:
    if context.args:
        topic = context.args[0]
        message = context.args[1]
        mqtt_client.publish(topic, message)
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

async def topic(update: Update, context: CallbackContext) -> None:
    if chat_id: 
        await update.message.reply_text(f"Your topic is: {mqtt_topic_subscribe}")
    else:
        await update.message.reply_text("Chat ID not set. Please start the bot first.")

async def subscribe(update: Update, context: CallbackContext) -> None:
    global topicos
    if chat_id:
        message = ' '.join(context.args)
        print(message)
        mqtt_client.subscribe(message, 0)
        topicos.append(message)
        print(topicos)
        await update.message.reply_text(f"subscribed to topic: {message}")
    else:
        await update.message.reply_text("Chat ID not set. Please start the bot first.")

async def unsubscribe(update: Update, context: CallbackContext) -> None:
    global topicos
    if chat_id:
        message = context.args
        mqtt_client.unsubscribe(message)
        topicos.remove(message)
        await update.message.reply_text(f"subscribed to topic: {message}")
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
application.add_handler(CommandHandler("topic", topic))
application.add_handler(CommandHandler("subscribe", subscribe))
application.add_handler(CommandHandler("unsubscribe", unsubscribe))

# Add a handler for all text messages
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Start the MQTT loop
mqtt_client.loop_start()

# Start the Telegram bot
application.run_polling()
