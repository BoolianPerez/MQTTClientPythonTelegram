#!/usr/bin/env python3
import asyncio
import paho.mqtt.client as paho
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands, Update
from telegram.ext import ConversationHandler, CallbackQueryHandler, Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging
import tkinter as tk
from tkinter import simpledialog, messagebox
import json

logging.basicConfig(level=logging.INFO)

class Enchufe:
    def __init__(self, nombre, topico, estado=False):
        self.nombre = nombre
        self.topico = topico
        self.estado = estado

# Global consts:
MQTT_PORT = 1883

# Global variables for mem allocation
mqtt_topic_subscribe = "hfeasy_8FB78C"
chat_id = None
application = None
enchufes = []
NAME, TOPIC, EDITNAME, EDITTOPIC, DELETE = range(5)
topicos = []
MQTT_BROKER = ""
MQTT_USERNAME = ""
MQTT_PASSWORD = ""
TELEGRAM_BOT_TOKEN = ""

# Setup menu
btn_menu = [InlineKeyboardButton("Menu principal", callback_data='menu')]
menu = [
    [InlineKeyboardButton("Elegir enchufe", callback_data='enchufes')],
    [InlineKeyboardButton("Agregar enchufe", callback_data='agregar')],
    [InlineKeyboardButton("Editar enchufe", callback_data='editar')],
    [InlineKeyboardButton("Eliminar enchufe", callback_data='eliminar')],
]
menu_markup = InlineKeyboardMarkup(menu)

# Async
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

mqtt_client = paho.Client()

def guardar_enchufes(enchufes, filename='enchufes.json'):
    with open(filename, 'w') as f:
        json.dump([enchufe.__dict__ for enchufe in enchufes], f)

def cargar_enchufes(filename='enchufes.json'):
    try:
        with open(filename, 'r') as f:
            enchufes_data = json.load(f)
            return [Enchufe(**data) for data in enchufes_data]
    except FileNotFoundError:
        return []
    
enchufes = cargar_enchufes()

async def mostrar_enchufes(update: Update, context: CallbackContext) -> int:
    keyboard = [[InlineKeyboardButton(enchufe.nombre, callback_data=enchufe.nombre)] for enchufe in enchufes]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("Selecciona el enchufe que deseas editar:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text("Selecciona el enchufe que deseas editar:", reply_markup=reply_markup)
    
    return EDITNAME
    
async def seleccionar_enchufe(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['nombre'] = query.data
    await query.edit_message_text(f"Enchufe seleccionado: {query.data}. Ahora ingresa el nuevo tópico MQTT del enchufe:")
    return EDITTOPIC


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

# Function to handle Telegram /start command
async def start(update: Update, context: CallbackContext) -> None:
    global chat_id
    chat_id = update.message.chat_id
    print(menu_markup)
    await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    await update.message.reply_text('Menu', reply_markup=menu_markup)

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
    topico = "cmnd/" + update.message.text + "/POWER"

    enchufe = Enchufe(nombre, topico)
    enchufes.append(enchufe)
    guardar_enchufes(enchufes)

    await update.message.reply_text(f"Enchufe '{nombre}' con tópico '{topico}' ha sido agregado.", reply_markup=menu_markup)
    
    await update.message.reply_text('Menu', reply_markup=menu_markup)

    context.user_data['state'] = None
    return ConversationHandler.END

async def editar(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    await mostrar_enchufes(update, context)
    return EDITNAME

async def editar_nombre(update: Update, context: CallbackContext) -> int:
    context.user_data['nombre'] = update.message.text
    await update.message.reply_text("Ahora ingresa el tópico MQTT del enchufe:")

    return EDITTOPIC

async def editar_topico(update: Update, context: CallbackContext) -> int:
    nombre = context.user_data.get('nombre')
    topico = "cmnd/" + update.message.text + "/POWER"

    # Buscar el enchufe existente y actualizarlo
    for enchufe in enchufes:
        if enchufe.nombre == nombre:
            enchufe.topico = topico
            break
    else:
        # Si no se encuentra, agregar uno nuevo
        enchufe = Enchufe(nombre, topico)
        enchufes.append(enchufe)

    guardar_enchufes(enchufes)

    await update.message.reply_text(f"Enchufe '{nombre}' con tópico '{topico}' ha sido actualizado.", reply_markup=menu_markup)
    
    await update.message.reply_text('Menu', reply_markup=menu_markup)

    context.user_data['state'] = None
    return ConversationHandler.END

async def cancelar(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operación cancelada.", reply_markup=menu_markup)
    return ConversationHandler.END

async def button(update: Update, context: CallbackContext) -> None:
    global enchufes
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
    elif query.data == "editar":
        botones_enchufes = [[InlineKeyboardButton(enchufe.nombre, callback_data="editar_enchufe " + enchufe.nombre)] for enchufe in enchufes]
        botones_enchufes.append(btn_menu)
        botones_enchufes_markup = InlineKeyboardMarkup(botones_enchufes)
        await query.edit_message_text('Selecciona el enchufe a editar:', reply_markup=botones_enchufes_markup)
    elif query.data == "eliminar":
        await eliminar(update, context)
    elif query.data.startswith("eliminar_enchufe"):
        nombre = query.data.split(' ')[1]
        enchufes = [enchufe for enchufe in enchufes if enchufe.nombre != nombre]
        guardar_enchufes(enchufes)
        await query.edit_message_text(f"Enchufe '{nombre}' eliminado.")
    elif query.data.startswith("editar_enchufe"):
        nombre = query.data.split(' ')[1]
        context.user_data['nombre_a_editar'] = nombre
        await query.edit_message_text(f"Ingrese el nuevo nombre para el enchufe '{nombre}':")
        return EDITNAME
    elif query.data.startswith("enchufe"):
        nombre, topico = query.data.split(' ')[1:]
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
        guardar_enchufes(enchufes)
    elif query.data.startswith('off'):
        topico = query.data.split(' ')[1]
        mqtt_client.publish(topico, "OFF")
        for enchufe in enchufes:
            if enchufe.topico == topico:
                enchufe.estado = False
        guardar_enchufes(enchufes)
    elif query.data.startswith('state'):
        topico = query.data.split(' ')[1]
        for enchufe in enchufes:
            if enchufe.topico == topico:
                estado_texto = "Prendido" if enchufe.estado else "Apagado"
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

async def delete(update: Update, context: CallbackContext) -> int:
    enchufe_a_eliminar = update.message.text
    global enchufes
    enchufes = [enchufe for enchufe in enchufes if enchufe.nombre != enchufe_a_eliminar]
    guardar_enchufes(enchufes)
    await update.message.reply_text(f"Enchufe '{enchufe_a_eliminar}' eliminado.")
    return ConversationHandler.END

async def eliminar(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    botones_enchufes = [[InlineKeyboardButton(enchufe.nombre, callback_data="eliminar_enchufe " + enchufe.nombre)] for enchufe in enchufes]
    botones_enchufes.append(btn_menu)
    botones_enchufes_markup = InlineKeyboardMarkup(botones_enchufes)
    await query.edit_message_text('Selecciona el enchufe a eliminar:', reply_markup=botones_enchufes_markup)


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

# GUI Function to get inputs
def start_gui():
    global MQTT_BROKER, MQTT_USERNAME, MQTT_PASSWORD, TELEGRAM_BOT_TOKEN
    global broker_entry

    # Create the main window
    root = tk.Tk()
    root.title("MQTT and Telegram Config")

    def start_bot():
        global MQTT_BROKER, MQTT_USERNAME, MQTT_PASSWORD, TELEGRAM_BOT_TOKEN, application
        MQTT_BROKER = broker_entry.get()
        MQTT_USERNAME = username_entry.get()
        MQTT_PASSWORD = password_entry.get()
        TELEGRAM_BOT_TOKEN = token_entry.get()
        config = {
            "MQTT_BROKER": MQTT_BROKER,
            "MQTT_USERNAME": MQTT_USERNAME,
            "MQTT_PASSWORD": MQTT_PASSWORD,
            "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN
        }
        with open('config.json', 'w') as f:
            json.dump(config, f)
        root.destroy()
        # Check for empty inputs
        if not all([MQTT_BROKER, MQTT_USERNAME, MQTT_PASSWORD, TELEGRAM_BOT_TOKEN]):
            messagebox.showerror("Input Error", "Please fill all fields.")
            return
        # Setup MQTT Client
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        mqtt_client.on_message = on_message
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.subscribe(mqtt_topic_subscribe, 0)
        # Create Telegram bot application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        agregar_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(agregar, pattern='^agregar$')],
            states={
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, agregar_nombre)],
                TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, agregar_topico)],
            },
            fallbacks=[CommandHandler("cancelar", cancelar)],
        )
        edit_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(editar, pattern='^editar$')],
            states={
                EDITNAME: [CallbackQueryHandler(seleccionar_enchufe)],
                EDITTOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_topico)],
            },
            fallbacks=[CommandHandler('cancelar', cancelar)],
        )

        # Start MQTT loop and Telegram bot
        mqtt_client.loop_start()
        application.add_handler(agregar_handler)
        application.add_handler(edit_handler)
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(CommandHandler("send", send))
        application.add_handler(CommandHandler("receive", receive))
        application.add_handler(CommandHandler("chatid", chatid))
        application.add_handler(CommandHandler("topic", topic))
        application.add_handler(CommandHandler("subscribe", subscribe))
        application.add_handler(CommandHandler("unsubscribe", unsubscribe))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        # Ensure the application is running
        loop.run_until_complete(application.run_polling())
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            MQTT_BROKER = config.get("MQTT_BROKER", "")
            MQTT_USERNAME = config.get("MQTT_USERNAME", "")
            MQTT_PASSWORD = config.get("MQTT_PASSWORD", "")
            TELEGRAM_BOT_TOKEN = config.get("TELEGRAM_BOT_TOKEN", "")
    except FileNotFoundError:
        pass

    # Create labels and entries for user inputs
    tk.Label(root, text="MQTT Broker:").pack()
    broker_entry = tk.Entry(root)
    broker_entry.pack()

    tk.Label(root, text="MQTT Username:").pack()
    username_entry = tk.Entry(root)
    username_entry.pack()

    tk.Label(root, text="MQTT Password:").pack()
    password_entry = tk.Entry(root, show="*")
    password_entry.pack()

    tk.Label(root, text="Telegram Bot Token:").pack()
    token_entry = tk.Entry(root)
    token_entry.pack()

    # Start button
    start_button = tk.Button(root, text="Start Bot", command=start_bot)
    start_button.pack()

    root.mainloop()
    start_bot()
start_gui()
