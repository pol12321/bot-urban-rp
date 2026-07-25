import os
import threading
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask

# Cargar variables de entorno (Secrets)
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("BOT_TOKEN")

# ─────────────────────────────────────────────
#  Servidor Web para Keep Alive
# ─────────────────────────────────────────────
app = Flask("")

@app.route("/")
def home():
    return "¡Bot en línea 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run_web_server)
    t.daemon = True
    t.start()


# ─────────────────────────────────────────────
#  IDs de Roles y Canales
# ─────────────────────────────────────────────
ID_DUENO = 1429580044375953470
ROL_APERTURA_ID = 1454135341547130901
ROL_ENCARGADO_ID = 1454135333150003354
ROL_CITACIONES_ID = 1455521984921337926
CANAL_VOZ_CITACIONES_ID = 1454132886633713822


# ─────────────────────────────────────────────
#  Vista interactiva para Solicitud de Robo
# ─────────────────────────────────────────────
class RoboButtonsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Aceptar",
        style=discord.ButtonStyle.green,
        custom_id="btn_aceptar_robo"
    )
    async def aceptar_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        role_encargado = interaction.guild.get_role(ROL_ENCARGADO_ID)
        if role_encargado not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ No tienes permiso para aceptar o denegar este robo.", 
                ephemeral=True
            )
            return

        for child in self.children:
            child.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.add_field(
            name="Estado", 
            value=f"✅ **Aceptado** por {interaction.user.mention}", 
            inline=False
        )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Denegar",
        style=discord.ButtonStyle.red,
        custom_id="btn_denegar_robo"
    )
    async def denegar_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        role_encargado = interaction.guild.get_role(ROL_ENCARGADO_ID)
        if role_encargado not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ No tienes permiso para aceptar o denegar este robo.", 
                ephemeral=True
            )
            return

        for child in self.children:
            child.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(
            name="Estado", 
            value=f"❌ **Denegado** por {interaction.user.mention}", 
            inline=False
        )

        await interaction.response.edit_message(embed=embed, view=self)


# ─────────────────────────────────────────────
#  Inicializar Bot
# ─────────────────────────────────────────────
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    bot.add_view(RoboButtonsView())

    print(f"\n{'═'*40}")
    print(f"  Bot conectado como: {bot.user}")
    print(f"  Servidores:         {len(bot.guilds)}")
    print(f"{'═'*40}\n")

    guild_ids = [g.id for g in bot.guilds]
    if guild_ids:
        await bot.sync_commands(guild_ids=guild_ids)
        print(f"  ✅ Comandos sincronizados en {len(guild_ids)} servidor(es)")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="el servidor 👀"
        )
    )


# ─────────────────────────────────────────────
#  Escuchar Respuestas Privadas (MD)
# ─────────────────────────────────────────────
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Si es un Mensaje Directo (Privado) enviado al Bot
    if getattr(message.channel, "type", None) == discord.ChannelType.private or isinstance(message.channel, discord.DMChannel):
        try:
            dueno = await bot.fetch_user(ID_DUENO)
            if dueno:
                embed = discord.Embed(
                    title="📬 Nuevo mensaje privado recibido",
                    description=message.content if message.content else "*[Archivo/Sin texto]*",
                    color=discord.Color.blue()
                )
                embed.set_author(name=f"{message.author.display_name} (@{message.author.name})", icon_url=message.author.display_avatar.url)
                embed.set_footer(text=f"ID Usuario: {message.author.id}")

                if message.attachments:
                    embed.set_image(url=message.attachments[0].url)

                await dueno.send(embed=embed)
        except Exception as e:
            print(f"Error al reenviar MD: {e}")


# ─────────────────────────────────────────────
#  1. COMANDO: Citaciones Reportes
# ─────────────────────────────────────────────
@bot.slash_command(
    name="citaciones",
    description="Emite una citación para un usuario."
)
async def citaciones(
    ctx: discord.ApplicationContext,
    usuario: discord.Option(discord.User, "Usuario al que se le hace la citación"),
    llamadas: discord.Option(str, "Número de llamadas (Ejemplo: 1 / 3, 2 / 3...)")
):
    role_citaciones = ctx.guild.get_role(ROL_CITACIONES_ID)
    if role_citaciones not in ctx.author.roles:
        await ctx.respond("❌ No tienes el rol necesario para emitir citaciones.", ephemeral=True)
        return

    canal_voz = ctx.guild.get_channel(CANAL_VOZ_CITACIONES_ID)
    mencion_canal = canal_voz.mention if canal_voz else "<#1454132886633713822>"

    embed = discord.Embed(
        title="🌆 / Citaciones Reportes",
        color=discord.Color.dark_theme()
    )

    embed.add_field(
        name="👤 Nombre del usuario:", 
        value=f"• {usuario.mention}", 
        inline=False
    )
    embed.add_field(
        name="🚨 Numeró de veces que se le a llamado:", 
        value=f"• {llamadas}", 
        inline=False
    )
    embed.add_field(
        name="🔊 Canal de voz requerido:", 
        value=f"↳ {mencion_canal}", 
        inline=False
    )

    await ctx.respond(content=usuario.mention, embed=embed)


# ─────────────────────────────────────────────
#  2. COMANDO: Solicitar Robo
# ─────────────────────────────────────────────
@bot.slash_command(
    name="solicitar_robo",
    description="Solicita un robo especificando usuario, dinero e imagen."
)
async def solicitar_robo(
    ctx: discord.ApplicationContext,
    usuario: discord.Option(discord.User, "Usuario al que vas a robar"),
    dinero: discord.Option(int, "Cantidad de dinero a robar"),
    imagen: discord.Option(discord.Attachment, "Prueba o imagen del robo")
):
    role_apertura = ctx.guild.get_role(ROL_APERTURA_ID)
    if role_apertura not in ctx.author.roles:
        await ctx.respond("❌ No tienes el rol necesario para solicitar un robo.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🚨 Solicitud de Robo 🚨",
        color=discord.Color.orange()
    )
    embed.add_field(name="Solicitante", value=ctx.author.mention, inline=True)
    embed.add_field(name="Víctima", value=usuario.mention, inline=True)
    embed.add_field(name="Dinero solicitado", value=f"${dinero:,}", inline=False)

    if imagen.content_type and imagen.content_type.startswith("image/"):
        embed.set_image(url=imagen.url)
    else:
        embed.add_field(name="Prueba", value=f"[Enlace al archivo adjunto]({imagen.url})", inline=False)

    role_encargado = ctx.guild.get_role(ROL_ENCARGADO_ID)
    mencion_encargado = role_encargado.mention if role_encargado else ""

    await ctx.respond(
        content=f"🔔 {mencion_encargado} ¡Nueva solicitud de robo pendiente de revisión!",
        embed=embed,
        view=RoboButtonsView()
    )


# ─────────────────────────────────────────────
#  3. COMANDO: Votación de Apertura
# ─────────────────────────────────────────────
@bot.slash_command(
    name="votacion",
    description="Crea una votación para la apertura especificando personas, hora e imagen."
)
async def votacion(
    ctx: discord.ApplicationContext,
    minimo_personas: discord.Option(int, "Mínimo de personas necesarias"),
    hora: discord.Option(str, "Hora prevista de apertura (ej: 20:00 UTC)"),
    imagen: discord.Option(discord.Attachment, "Imagen informativa para la votación", required=False)
):
    role_apertura = ctx.guild.get_role(ROL_APERTURA_ID)
    if role_apertura not in ctx.author.roles:
        await ctx.respond("❌ No tienes el rol necesario para iniciar una votación.", ephemeral=True)
        return

    embed = discord.Embed(
        title="📊 Votación de Apertura del Servidor",
        description="¡Reacciona si vas a estar presente en la apertura!",
        color=discord.Color.purple()
    )
    embed.add_field(name="👥 Mínimo Requerido", value=f"**{minimo_personas} personas**", inline=True)
    embed.add_field(name="⏰ Hora Prevista", value=f"**{hora}**", inline=True)
    embed.set_footer(text=f"Votación iniciada por {ctx.author.display_name}")

    if imagen and imagen.content_type and imagen.content_type.startswith("image/"):
        embed.set_image(url=imagen.url)

    interaction = await ctx.respond(content="@everyone", embed=embed)
    mensaje = await interaction.original_response()

    await mensaje.add_reaction("👍")
    await mensaje.add_reaction("👎")


# ─────────────────────────────────────────────
#  4. COMANDOS: Abrir y Cerrar Servidor
# ─────────────────────────────────────────────
@bot.slash_command(
    name="abrir_servidor",
    description="Anuncia la apertura del servidor."
)
async def abrir_servidor(
    ctx: discord.ApplicationContext,
    imagen: discord.Option(discord.Attachment, "Imagen para el aviso (opcional)", required=False)
):
    role_apertura = ctx.guild.get_role(ROL_APERTURA_ID)
    if role_apertura not in ctx.author.roles:
        await ctx.respond("❌ No tienes el rol necesario para abrir el servidor.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎉 ¡URBAN RP V2 ABIERTO! 🎉",
        description=(
            "✅ **El servidor ya se encuentra abierto oficialmente.**\n\n"
            "🚀 **Ya podéis entrar y comenzar vuestra aventura en Urban RP V2.**\n\n"
            "💙 **¡Os esperamos dentro, disfrutad de la experiencia!**"
        ),
        color=discord.Color.green()
    )

    if imagen and imagen.content_type and imagen.content_type.startswith("image/"):
        embed.set_image(url=imagen.url)

    await ctx.respond(content="@everyone", embed=embed)


@bot.slash_command(
    name="cerrar_servidor",
    description="Anuncia el cierre del servidor."
)
async def cerrar_servidor(
    ctx: discord.ApplicationContext,
    imagen: discord.Option(discord.Attachment, "Imagen para el aviso (opcional)", required=False)
):
    role_apertura = ctx.guild.get_role(ROL_APERTURA_ID)
    if role_apertura not in ctx.author.roles:
        await ctx.respond("❌ No tienes el rol necesario para cerrar el servidor.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🚨 SERVIDOR CERRADO",
        description=(
            "❌ **Urban RP V2 ha cerrado.**\n\n"
            "🔒 Se comenzarán a retirar todos los roles **lo antes posible.**\n\n"
            "**Gracias por haber formado parte de la comunidad.❤️**"
        ),
        color=discord.Color.red()
    )

    if imagen and imagen.content_type and imagen.content_type.startswith("image/"):
        embed.set_image(url=imagen.url)

    await ctx.respond(content="@everyone", embed=embed)


# ─────────────────────────────────────────────
#  5. COMANDO DE PERFIL: Enviar MD (Solo Tu ID)
# ─────────────────────────────────────────────
@bot.user_command(name="Enviar MD con el Bot")
async def enviar_md_perfil(ctx: discord.ApplicationContext, usuario: discord.Member):
    if ctx.author.id != ID_DUENO:
        await ctx.respond("❌ Solo el dueño del bot puede usar esta función.", ephemeral=True)
        return

    class MensajeModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title=f"Hablar con {usuario.display_name}")
            self.add_item(
                discord.ui.InputText(
                    label="Mensaje",
                    placeholder="Escribe aquí lo que dirá el bot...",
                    style=discord.InputTextStyle.long
                )
            )

        async def callback(self, interaction: discord.Interaction):
            texto = self.children[0].value
            try:
                await usuario.send(texto)
                await interaction.response.send_message(
                    f"✅ Mensaje enviado a **{usuario.display_name}**: {texto}", 
                    ephemeral=True
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    f"❌ **{usuario.display_name}** tiene los MD cerrados.", 
                    ephemeral=True
                )

    await ctx.send_modal(MensajeModal())


# ─────────────────────────────────────────────
#  ENCENDIDO DEL BOT
# ─────────────────────────────────────────────
keep_alive()

if BOT_TOKEN:
    bot.run(BOT_TOKEN)
