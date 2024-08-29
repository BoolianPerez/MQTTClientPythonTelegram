#!/usr/bin/env python3
import asyncio
import paho.mqtt.client as paho
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands, Update
from telegram.ext import ConversationHandler, CallbackQueryHandler, Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging

# Configura el registro de eventos
logging.basicConfig(level=logging.INFO)

# MQTT configuration
MQTT_BROKER = "172.16.4.251"
MQTT_PORT = 1883
MQTT_USERNAME = "beans"  # Añade tu nombre de usuario aquí
MQTT_PASSWORD = "rango"  # Añade tu contraseña aquí
mqtt_topic_subscribe = "hfeasy_8FB78C"
MQTT_TOPIC_PUBLISH = ""                                                                                                               

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
    logging.info(f"MQTT Message: {telegram_message}")

    for enchufe in enchufes:
        if enchufe.topico == msg.topic:
            enchufe.estado = msg.payload.decode('utf-8').strip() == "ON"
            break

# MQTT Client setup
mqtt_client = paho.Client()

# Establecer credenciales de autenticación
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.subscribe(mqtt_topic_subscribe, 0)

btn_menu = [InlineKeyboardButton("Menu principal", callback_data='menu')]

menu = [
    [InlineKeyboardButton("Elegir enchufe", callback_data='enchufes')],
    [InlineKeyboardButton("Agregar enchufe", callback_data='agregar')],
]
menu_markup = InlineKeyboardMarkup(menu)

# Function to handle Telegram /start command
async def start(update: Update, context: CallbackContext) -> None:
    print(3232)
    global chat_id
    chat_id = update.message.chat_id
    await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    await update.message.reply_text('Menu', reply_markup=menu_markup)

class Enchufe:
    def __init__(self, nombre, topico, estado=False) -> None:
        self.nombre = nombre
        self.topico = topico
        self.estado = estado

enchufes = [Enchufe("Solid", "cmnd/hfeasy_8FB78C/POWER", False)]

NAME, TOPIC = range(2)

async def agregar(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Por favor, ingresa el nombre del enchufe:", reply_markup=None)

    return NAME

async def agregar_nombre(update: Update, context: CallbackContext) -> int:
    context.user_data['nombre'] = update.message.text
    await update.message.reply_text("Ahora ingresa el tópico MQTT del enchufe:")

    return TOPIC

async def agregar_topico(update: Update, context: CallbackContext) -> int:
    nombre = context.user_data.get('nombre')
    topico = update.message.text

    enchufes.append(Enchufe(nombre, topico))

    await update.message.reply_text(f"Enchufe '{nombre}' con tópico '{topico}' ha sido agregado.", reply_markup=menu_markup)
    
    await update.message.reply_text('Menu', reply_markup=menu_markup)

    context.user_data['state'] = None
    return ConversationHandler.END

async def cancelar(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operación cancelada.", reply_markup=menu_markup)
    return ConversationHandler.END

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'enchufes':
        botones_enchufes = [[InlineKeyboardButton(enchufe.nombre, callback_data="enchufe " + enchufe.nombre + " " + enchufe.topico)] for enchufe in enchufes]
        botones_enchufes.append(btn_menu)
        botones_enchufes_markup = InlineKeyboardMarkup(botones_enchufes)
        await query.edit_message_text('Elegí un enchufe:', reply_markup=botones_enchufes_markup)
    elif query.data == "menu":
        await query.edit_message_text('Menu', reply_markup=menu_markup)
    elif query.data == "agregar":
        await agregar(update, context)
    elif query.data.startswith("enchufe"):
        nombre = query.data.split(' ')[1]
        topico = query.data.split(' ')[2]

        botones_estado = [
            [InlineKeyboardButton("Prender", callback_data='on ' + topico)],
            [InlineKeyboardButton("Apagar", callback_data='off ' + topico)],
            [InlineKeyboardButton("Ver estado", callback_data='state ' + topico)],
            btn_menu
        ]
        botones_estado_markup = InlineKeyboardMarkup(botones_estado)
        await query.edit_message_text("Nombre: " + nombre + '\n\nTopico: ' + topico, reply_markup=botones_estado_markup)
    elif query.data.startswith('on'):
        topico = query.data.split(' ')[1]
        mqtt_client.publish(topico, "ON")
        for enchufe in enchufes:
            if enchufe.topico == topico:
                enchufe.estado = True

    elif query.data.startswith('off'):
        topico = query.data.split(' ')[1]
        mqtt_client.publish(topico, "OFF")
        for enchufe in enchufes:
            if enchufe.topico == topico:
                enchufe.estado = False

    elif query.data.startswith('state'):
        topico = query.data.split(' ')[1]
        for enchufe in enchufes:
            if enchufe.topico == topico:
                if enchufe.estado == False: 
                    estado_texto = "Apagado" 
                else: 
                    estado_texto = "Prendido"
                await query.message.reply_text(f"El estado del enchufe es: {estado_texto}")
                break

        



# Function to handle Telegram /send command
async def send(update: Update, context: CallbackContext) -> None:
    if context.args:
        topic = context.args[0]
        message = context.args[1]
        print("Topico: " + topic)
        print("Mensaje" + message)
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
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(agregar, pattern='^agregar$')],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, agregar_nombre)],
        TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, agregar_topico)],
    },
    fallbacks=[CommandHandler("cancelar", cancelar)],
)

# Add the conversation handler to the application
application.add_handler(conv_handler)
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("send", send))
application.add_handler(CommandHandler("receive", receive))
application.add_handler(CommandHandler("chatid", chatid))
application.add_handler(CommandHandler("topic", topic))
application.add_handler(CommandHandler("subscribe", subscribe))
application.add_handler(CommandHandler("unsubscribe", unsubscribe))
application.add_handler(CallbackQueryHandler(button))

# Add a handler for all text messages
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Start the MQTT loop
mqtt_client.loop_start()

# Start the Telegram bot
application.run_polling()
