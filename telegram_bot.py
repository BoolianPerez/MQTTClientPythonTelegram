import logging
import asyncio
import sys
import paho.mqtt.client as paho

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands, Update
from telegram.ext import ConversationHandler, CallbackContext

from enchufe import Enchufe
from enchufe import guardar_enchufes, cargar_enchufes

NAME, TOPIC, EDITNAME, EDITTOPIC = range(4)
enchufes = cargar_enchufes()

mqtt_client = paho.Client()
mqtt_topic_subscribe = "hfeasy_8FB78C"
btn_menu = [InlineKeyboardButton("Menu principal", callback_data='menu')]
menu = [
    [InlineKeyboardButton("Elegir enchufe", callback_data='enchufes')],
    [InlineKeyboardButton("Agregar enchufe", callback_data='agregar')],
    [InlineKeyboardButton("Frenar server", callback_data='stop_server')],
]
menu_markup = InlineKeyboardMarkup(menu)

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

# Function to handle Telegram /start command
async def start(update: Update, context: CallbackContext) -> None:
    global chat_id
    chat_id = update.message.chat_id

    #await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
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
    topico = formatTopic(update.message.text)

    enchufe = Enchufe(nombre, topico)
    enchufes.append(enchufe)
    guardar_enchufes(enchufes)

    await update.message.reply_text(f"Enchufe '{nombre}' con tópico '{topico}' ha sido agregado.", reply_markup=None)
    
    await update.message.reply_text('Menu', reply_markup=menu_markup)

    context.user_data['state'] = None
    return ConversationHandler.END

async def editar_nombre_1(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    nombre = query.data.split(' ')[1]
    context.user_data['nombre_selec'] = nombre
    
    await query.answer()
    await query.edit_message_text("Por favor, ingresa el nuevo nombre del enchufe:", reply_markup=None)

    return EDITNAME

async def editar_nombre_2(update: Update, context: CallbackContext) -> int:
    nombre = context.user_data['nombre_selec']
    nuevo_nombre = update.message.text
    
    for enchufe in enchufes:
        if enchufe.nombre == nombre:
            enchufe.nombre = nuevo_nombre
            break
    guardar_enchufes(enchufes)
    
    await update.message.reply_text(f"Nombre del enchufe '{nombre}' cambiado a '{nuevo_nombre}'.")
    
    #await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    await update.message.reply_text('Menu', reply_markup=menu_markup)
    return ConversationHandler.END

async def editar_topico_1(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Por favor, ingresa el nuevo topico del enchufe:", reply_markup=None)

    return EDITTOPIC

async def editar_topico_2(update: Update, context: CallbackContext) -> int:
    nombre = context.user_data['nombre_selec']
    nuevo_topico = formatTopic(update.message.text)
    
    for enchufe in enchufes:
        if enchufe.nombre == nombre:
            enchufe.topico = nuevo_topico
            break
    guardar_enchufes(enchufes)
    
    await update.message.reply_text(f"Tópico del enchufe '{nombre}' cambiado a '{nuevo_topico}'.")
    
    #await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    await update.message.reply_text('Menu', reply_markup=menu_markup)
    return ConversationHandler.END

async def cancelar(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operación cancelada.", reply_markup=menu_markup)
    return ConversationHandler.END

def formatTopic(topic):
    return "cmnd/" + topic + "/POWER"

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
    elif query.data == "eliminar":
        await eliminar(update, context)
    elif query.data.startswith("eliminar_enchufe"):
        nombre = query.data.split(' ')[1]
        enchufes = [enchufe for enchufe in enchufes if enchufe.nombre != nombre]
        guardar_enchufes(enchufes)
        await query.edit_message_text(f"Enchufe '{nombre}' eliminado.")
    elif query.data.startswith("enchufe"):
        nombre, topico = query.data.split(' ')[1:]
        context.user_data['nombre_selec'] = nombre
        
        botones_estado = [
            [InlineKeyboardButton("Prender", callback_data='on ' + topico)],
            [InlineKeyboardButton("Apagar", callback_data='off ' + topico)],
            [InlineKeyboardButton("Editar nombre", callback_data='editar_nombre ' + nombre)],
            [InlineKeyboardButton("Editar tópico", callback_data='editar_topico ' + nombre)],
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
    elif query.data.startswith('editar_nombre'):
        nombre = query.data.split(' ')[1]
        context.user_data['nombre_selec'] = nombre
        await editar_nombre_1(update, context)

    elif query.data.startswith('editar_topico'):
        nombre = query.data.split(' ')[1]
        context.user_data['nombre_selec'] = nombre
        await editar_topico_1(update, context)
    elif query.data == "stop_server":
        query.message.reply_text(f"Server stopped")
        await stop_server(update, context)

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

async def stop_server(update: Update, context: CallbackContext) -> None:
    global server_running

    sys.exit(0)