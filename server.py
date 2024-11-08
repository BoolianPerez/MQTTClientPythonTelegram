#!/usr/bin/env python3
import asyncio

from telegram.ext import ConversationHandler, CallbackQueryHandler, Application, CommandHandler, MessageHandler, filters
import logging
import tkinter as tk
from tkinter import messagebox
from config import cargar_configuracion, guardar_configuracion
from telegram_bot import start, button, send, receive, chatid, topic, subscribe, unsubscribe, handle_message, agregar, agregar_nombre, agregar_topico, editar_nombre_1, editar_nombre_2, editar_topico_1, editar_topico_2, cancelar, mqtt_client, on_message, mqtt_topic_subscribe

logging.basicConfig(level=logging.INFO)

# Global consts:
MQTT_PORT = 1883

# Global variables for mem allocation

chat_id = None
application = None
NAME, TOPIC, EDITNAME, EDITTOPIC = range(4)
topicos = []
MQTT_BROKER = ""
MQTT_USERNAME = ""
MQTT_PASSWORD = ""
TELEGRAM_BOT_TOKEN = ""

# Setup menu


# Async
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# GUI Function to get inputs
def start_gui():
    global MQTT_BROKER, MQTT_USERNAME, MQTT_PASSWORD, TELEGRAM_BOT_TOKEN
    global broker_entry

    # Create the main window
    root = tk.Tk()
    root.title("MQTT and Telegram Config")

    def start_bot():
        global loop 
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        global MQTT_BROKER, MQTT_USERNAME, MQTT_PASSWORD, TELEGRAM_BOT_TOKEN, application
        MQTT_BROKER = broker_entry.get()
        MQTT_USERNAME = username_entry.get()
        MQTT_PASSWORD = password_entry.get()
        TELEGRAM_BOT_TOKEN = token_entry.get()

        guardar_configuracion(MQTT_BROKER, MQTT_USERNAME, MQTT_PASSWORD, TELEGRAM_BOT_TOKEN)

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

        cancelar_handler = CommandHandler("cancelar", cancelar)
        
        agregar_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(agregar, pattern='^agregar$')],
            states={
                NAME: [MessageHandler(filters.ALL, agregar_nombre)],
                TOPIC: [MessageHandler(filters.ALL, agregar_topico)],
            },
            fallbacks=[cancelar_handler],
        )
        edit_nombre_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(editar_nombre_1, pattern='^editar_nombre\s.+')],
            states={
                EDITNAME: [MessageHandler(filters.ALL, editar_nombre_2)],
            },
            fallbacks=[cancelar_handler],
        )

        edit_topic_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(editar_topico_1, pattern='^editar_topico\s.+')],
            states={
                EDITTOPIC: [MessageHandler(filters.ALL, editar_topico_2)],
            },
            fallbacks=[cancelar_handler],
        )

        # Start MQTT loop and Telegram bot
        mqtt_client.loop_start()
        application.add_handler(agregar_handler)
        application.add_handler(edit_nombre_handler)
        application.add_handler(edit_topic_handler)
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
        application.run_polling()

    def start_bot_thread():
        # Start the bot in a new thread to avoid blocking the GUI
        start_bot()

    def stop_server():
        application.stop()
        mqtt_client.disconnect()
        mqtt_client.loop_stop()
        loop.stop()
        loop.close()

    config = cargar_configuracion()

    if config:
        MQTT_BROKER = config['broker']
        MQTT_USERNAME = config['username']
        MQTT_PASSWORD = config['password']
        TELEGRAM_BOT_TOKEN = config['bot_token']

    # Create labels and entries for user inputs
    tk.Label(root, text="MQTT Broker:").pack()
    broker_entry = tk.Entry(root)
    broker_entry.insert(0, MQTT_BROKER)  # Set the entry's value
    broker_entry.pack()

    tk.Label(root, text="MQTT Username:").pack()
    username_entry = tk.Entry(root)
    username_entry.insert(0, MQTT_USERNAME)  # Set the entry's value
    username_entry.pack()

    tk.Label(root, text="MQTT Password:").pack()
    password_entry = tk.Entry(root, show="*")
    password_entry.insert(0, MQTT_PASSWORD)  # Set the entry's value
    password_entry.pack()

    tk.Label(root, text="Telegram Bot Token:").pack()
    token_entry = tk.Entry(root)
    token_entry.insert(0, TELEGRAM_BOT_TOKEN)  # Set the entry's value
    token_entry.pack()

    # Start button
    start_button = tk.Button(root, text="Start Bot", command=start_bot_thread)
    start_button.pack()
    
    # Stop server button
    tk.Label(root, text="Detener el servidor en telegram").pack()

    root.mainloop()

    start_bot_thread()
start_gui()
