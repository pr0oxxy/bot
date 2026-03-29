import os
import uuid
import time
import json
import asyncio
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

BTC_WALLET = os.getenv("BTC_WALLET", "BTC wallet not set")
LTC_WALLET = os.getenv("LTC_WALLET", "LTC wallet not set")
SOL_WALLET = os.getenv("SOL_WALLET", "SOL wallet not set")
ETH_WALLET = os.getenv("ETH_WALLET", "ETH wallet not set")

STAFF_NOTIFICATION_CHANNEL_ID = os.getenv("STAFF_NOTIFICATION_CHANNEL_ID")
ORDER_LOG_WEBHOOK_URL = os.getenv("ORDER_LOG_WEBHOOK_URL")
TICKET_CATEGORY_ID = os.getenv("TICKET_CATEGORY_ID")
STAFF_ROLE_ID = os.getenv("STAFF_ROLE_ID")
OWNER_USER_ID = os.getenv("OWNER_USER_ID")
VOUCH_CHANNEL_ID = os.getenv("VOUCH_CHANNEL_ID")

STAFF_NOTIFICATION_CHANNEL_ID = int(STAFF_NOTIFICATION_CHANNEL_ID) if STAFF_NOTIFICATION_CHANNEL_ID else None
TICKET_CATEGORY_ID = int(TICKET_CATEGORY_ID) if TICKET_CATEGORY_ID else None
STAFF_ROLE_ID = int(STAFF_ROLE_ID) if STAFF_ROLE_ID else None
OWNER_USER_ID = int(OWNER_USER_ID) if OWNER_USER_ID else None
VOUCH_CHANNEL_ID = int(VOUCH_CHANNEL_ID) if VOUCH_CHANNEL_ID else None

if not TOKEN:
    raise ValueError("DISCORD_TOKEN is missing in your .env file")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

FUNDS_SENT_COOLDOWNS = {}
ORDERS_FILE = "orders.json"
PRICES_FILE = "prices.json"

# =========================================================
# DEFAULT DATA
# =========================================================

ROBUX_TOPUP_OPTIONS = [
    ("26,400 Robux", "26,400 Robux"),
    ("12,100 Robux", "12,100 Robux"),
    ("5,800 Robux", "5,800 Robux"),
    ("2,200 Robux", "2,200 Robux"),
    ("1,100 Robux", "1,100 Robux"),
]

ROBUX_GIFTCARD_OPTIONS = [
    ("$100 Gift Card", "$100 Gift Card"),
    ("$50 Gift Card", "$50 Gift Card"),
    ("$25 Gift Card", "$25 Gift Card"),
    ("$10 Gift Card", "$10 Gift Card"),
]

APEX_OPTIONS = [
    ("11.5k Apex Coins", "11.5k Apex Coins"),
    ("6.7k Apex Coins", "6.7k Apex Coins"),
    ("4.35k Apex Coins", "4.35k Apex Coins"),
    ("2.15k Apex Coins", "2.15k Apex Coins"),
]

VALORANT_OPTIONS = [
    ("11000 VP", "11000 VP"),
    ("5350 VP", "5350 VP"),
]

DEFAULT_PRICES = {
    "robux_topup": {
        "26,400 Robux": "$168.00",
        "12,100 Robux": "$84.00",
        "5,800 Robux": "$43.00",
        "2,200 Robux": "$18.00",
        "1,100 Robux": "$9.00",
    },
    "robux_giftcard": {
        "$100 Gift Card": "$65.00",
        "$50 Gift Card": "$32.50",
        "$25 Gift Card": "$16.50",
        "$10 Gift Card": "$7.50",
    },
    "apex": {
        "11.5k Apex Coins": "$65.00",
        "6.7k Apex Coins": "$39.00",
        "4.35k Apex Coins": "$27.00",
        "2.15k Apex Coins": "$14.00",
    },
    "valorant": {
        "11000 VP": "$65.00",
        "5350 VP": "$35.00",
    }
}

CHEAP_SERVICES_LIST = [
    "discord nitro boost",
    "spotify lft",
    "netflix lft",
    "nitro tokens",
    "youtube premium lft / 3 month",
    "dazn lft",
    "prime video lft",
    "chatgpt+ lft",
    "moviestar+ lft",
    "nord vpn lft",
    "disney+ lft",
    "HBO max lft",
    "discord members",
    "UFC lft",
    "fivem freshie",
    "rockstar codes",
    "FA/LFT steams",
    "minecraft lft",
    "viki lft",
    "microsoft codes",
    "pureVPN lft",
    "gemini AI pro lft",
    "cyberghost lft",
    "3m nitro promo codes",
    "canva pro lft",
    "express vpn lft",
    "paramount+ lft",
    "NBA lft",
    "duolingo lft",
    "molotov lft",
    "filmora lft",
    "gamepass ult 1 month",
]

CATEGORY_LABELS = {
    "robux_topup": "Robux Top-Up",
    "robux_giftcard": "Robux Gift Card",
    "apex": "Apex Coins",
    "valorant": "Valorant Points",
}

# =========================================================
# FILE STORAGE
# =========================================================

def load_orders() -> dict:
    if not os.path.exists(ORDERS_FILE):
        return {}
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_orders(data: dict):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_order_record(
    order_id: str,
    user_id: int,
    product_name: str,
    selection: str,
    price: str,
    payment_method: str,
    status: str = "created"
):
    data = load_orders()
    data[order_id] = {
        "user_id": user_id,
        "product_name": product_name,
        "selection": selection,
        "price": price,
        "payment_method": payment_method,
        "status": status,
        "created_at": int(time.time())
    }
    save_orders(data)


def update_order_status(order_id: str, status: str, extra: dict | None = None):
    data = load_orders()
    if order_id not in data:
        return False
    data[order_id]["status"] = status
    data[order_id]["updated_at"] = int(time.time())
    if extra:
        data[order_id].update(extra)
    save_orders(data)
    return True


def get_order(order_id: str):
    data = load_orders()
    return data.get(order_id)


def load_prices() -> dict:
    if not os.path.exists(PRICES_FILE):
        with open(PRICES_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_PRICES, f, indent=2)
        return json.loads(json.dumps(DEFAULT_PRICES))

    try:
        with open(PRICES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = json.loads(json.dumps(DEFAULT_PRICES))

    for category, values in DEFAULT_PRICES.items():
        if category not in data:
            data[category] = values.copy()
        else:
            for item, price in values.items():
                if item not in data[category]:
                    data[category][item] = price

    with open(PRICES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return data


def save_prices(data: dict):
    with open(PRICES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


PRICES = load_prices()

# =========================================================
# HELPERS
# =========================================================

def get_wallet(method: str) -> str:
    return {
        "btc": BTC_WALLET,
        "ltc": LTC_WALLET,
        "sol": SOL_WALLET,
        "eth": ETH_WALLET,
    }.get(method, "Wallet not found")


def get_payment_name(method: str) -> str:
    return {
        "btc": "Bitcoin (BTC)",
        "ltc": "Litecoin (LTC)",
        "sol": "Solana (SOL)",
        "eth": "Ethereum (ETH)",
    }.get(method, method.upper())


def is_admin(member: discord.Member) -> bool:
    return member.guild_permissions.administrator


def is_owner_id(user_id: int) -> bool:
    return OWNER_USER_ID is not None and user_id == OWNER_USER_ID


def get_ticket_owner_id_from_channel(channel: discord.TextChannel) -> int | None:
    topic = channel.topic or ""
    if topic.startswith("ticket_owner_id:"):
        try:
            return int(topic.split(":", 1)[1].strip())
        except Exception:
            return None
    return None


def get_price(category: str, item: str) -> str:
    return PRICES.get(category, {}).get(item, "Unknown")


def normalize_price_input(value: str) -> str:
    value = value.strip()
    if not value.startswith("$"):
        value = f"${value}"
    if "." not in value:
        value = f"{value}.00"
    else:
        left, right = value.split(".", 1)
        right = (right + "00")[:2]
        value = f"{left}.{right}"
    return value


async def send_order_log(
    title: str,
    user: discord.abc.User | None,
    product_name: str,
    selection: str,
    price: str,
    payment_method: str,
    order_id: str,
    event_type: str
):
    if not ORDER_LOG_WEBHOOK_URL:
        return

    embed = discord.Embed(title=title, color=discord.Color.dark_grey())
    embed.add_field(name="Event", value=event_type, inline=False)
    embed.add_field(
        name="User",
        value=f"{user} (`{user.id}`)" if user else "Unknown user",
        inline=False
    )
    embed.add_field(name="Product", value=product_name, inline=False)
    embed.add_field(name="Selection", value=selection, inline=False)
    embed.add_field(name="Price", value=price, inline=True)
    embed.add_field(name="Payment Method", value=payment_method, inline=True)
    embed.add_field(name="Order ID", value=f"`{order_id}`", inline=False)
    embed.set_footer(text="Proxy Services Order Logs")

    try:
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(ORDER_LOG_WEBHOOK_URL, session=session)
            await webhook.send(embed=embed, username="Proxy Services Logs")
    except Exception as e:
        print(f"Webhook log error: {e}")


async def notify_staff_payment(
    interaction: discord.Interaction,
    product_name: str,
    selection: str,
    price: str,
    payment_method: str,
    order_id: str
):
    if not STAFF_NOTIFICATION_CHANNEL_ID:
        return False

    channel = bot.get_channel(STAFF_NOTIFICATION_CHANNEL_ID)
    if channel is None:
        return False

    embed = discord.Embed(
        title="Payment Sent Notification",
        description="A customer says they have sent the funds.",
        color=discord.Color.dark_grey()
    )
    embed.add_field(name="User", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
    embed.add_field(name="Product", value=product_name, inline=False)
    embed.add_field(name="Selection", value=selection, inline=False)
    embed.add_field(name="Price", value=price, inline=True)
    embed.add_field(name="Payment Method", value=payment_method, inline=True)
    embed.add_field(name="Order ID", value=f"`{order_id}`", inline=False)
    embed.set_footer(text="Proxy Services")

    try:
        await channel.send(embed=embed)
        return True
    except Exception as e:
        print(f"Staff notify error: {e}")
        return False


async def dm_order_complete_with_vouch(user: discord.User, product_text: str):
    vouch_channel_text = f"<#{VOUCH_CHANNEL_ID}>" if VOUCH_CHANNEL_ID else "the vouch channel"

    embed = discord.Embed(
        title="Order Completed",
        description=(
            "Your order has been completed successfully.\n\n"
            f"Please leave a vouch in {vouch_channel_text}.\n\n"
            "**Example vouch:**\n"
            f"`Vouch @proxy {product_text}`"
        ),
        color=discord.Color.dark_grey()
    )
    embed.set_footer(text="Proxy Services")

    try:
        await user.send(embed=embed)
        return True
    except discord.Forbidden:
        return False

# =========================================================
# TICKET DELETE BUTTON
# =========================================================

class DeleteTicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Delete Ticket",
            style=discord.ButtonStyle.danger,
            emoji="🗑️",
            custom_id="delete_ticket_button"
        )

    async def callback(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("This can only be used in a ticket channel.", ephemeral=True)
            return

        owner_id = get_ticket_owner_id_from_channel(channel)
        is_owner = owner_id == interaction.user.id
        is_staff = False

        if interaction.guild and STAFF_ROLE_ID:
            staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
            if staff_role and staff_role in interaction.user.roles:
                is_staff = True

        if not is_owner and not is_staff and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You are not allowed to delete this ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message("Deleting ticket in 3 seconds...", ephemeral=True)
        await asyncio.sleep(3)

        try:
            await channel.delete(reason=f"Ticket deleted by {interaction.user}")
        except Exception as e:
            print(f"Delete ticket error: {e}")


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DeleteTicketButton())

# =========================================================
# TICKET CREATION
# =========================================================

async def create_ticket_from_button(
    interaction: discord.Interaction,
    ticket_type: str,
    selection: str | None = None
):
    guild = interaction.guild
    user = interaction.user

    if guild is None:
        await interaction.response.send_message(
            "This can only be used in a server.",
            ephemeral=True
        )
        return

    safe_name = "".join(c.lower() for c in user.name if c.isalnum() or c in "-_")
    if not safe_name:
        safe_name = f"user-{user.id}"

    prefix = ticket_type.lower().replace(" ", "-")
    channel_name = f"{prefix}-{safe_name}"

    existing = discord.utils.get(guild.text_channels, name=channel_name)
    if existing:
        await interaction.response.send_message(
            f"You already have a ticket open: {existing.mention}",
            ephemeral=True
        )
        return

    me = guild.me or guild.get_member(bot.user.id)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True
        ),
    }

    if me:
        overwrites[me] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True
        )

    if STAFF_ROLE_ID:
        staff_role = guild.get_role(STAFF_ROLE_ID)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

    category = guild.get_channel(TICKET_CATEGORY_ID) if TICKET_CATEGORY_ID else None

    ticket_channel = await guild.create_text_channel(
        name=channel_name,
        overwrites=overwrites,
        category=category,
        topic=f"ticket_owner_id:{user.id}"
    )

    desc = f"{user.mention}, your **{ticket_type}** ticket has been created."
    if selection:
        desc += f"\n\n**Selection:** {selection}"

    if ticket_type == "Cheap Services":
        desc += (
            "\n\nPlease send:\n"
            "• The service you want\n"
            "• The plan / duration\n"
            "• Any extra notes"
        )

    embed = discord.Embed(
        title=f"{ticket_type} Ticket Created",
        description=desc,
        color=discord.Color.dark_grey()
    )
    embed.set_footer(text="Proxy Services")

    await ticket_channel.send(
        content=user.mention,
        embed=embed,
        view=TicketControlView()
    )

    await interaction.response.send_message(
        f"Your ticket has been created: {ticket_channel.mention}",
        ephemeral=True
    )

# =========================================================
# FUNDS SENT BUTTON
# =========================================================

class FundsSentButton(discord.ui.Button):
    def __init__(self, product_name: str, selection: str, price: str, payment_method: str, order_id: str):
        super().__init__(
            label="I've Sent The Funds",
            style=discord.ButtonStyle.secondary,
            emoji="✅"
        )
        self.product_name = product_name
        self.selection = selection
        self.price = price
        self.payment_method = payment_method
        self.order_id = order_id

    async def callback(self, interaction: discord.Interaction):
        cooldown_key = f"{interaction.user.id}:{self.order_id}"
        now = time.time()
        last_used = FUNDS_SENT_COOLDOWNS.get(cooldown_key, 0)
        remaining = 15 - (now - last_used)

        if remaining > 0:
            await interaction.response.send_message(
                f"Please wait {int(remaining) + 1} seconds before pressing that again.",
                ephemeral=True
            )
            return

        FUNDS_SENT_COOLDOWNS[cooldown_key] = now
        update_order_status(self.order_id, "payment_sent")

        await send_order_log(
            title="Payment Marked As Sent",
            user=interaction.user,
            product_name=self.product_name,
            selection=self.selection,
            price=self.price,
            payment_method=self.payment_method,
            order_id=self.order_id,
            event_type="payment_sent"
        )

        sent = await notify_staff_payment(
            interaction=interaction,
            product_name=self.product_name,
            selection=self.selection,
            price=self.price,
            payment_method=self.payment_method,
            order_id=self.order_id
        )

        if sent:
            await interaction.response.send_message(
                "Your payment notification has been sent to staff. Please wait for confirmation.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Your payment was logged, but I could not notify staff in the staff channel.",
                ephemeral=True
            )


class FundsSentView(discord.ui.View):
    def __init__(self, product_name: str, selection: str, price: str, payment_method: str, order_id: str):
        super().__init__(timeout=None)
        self.add_item(FundsSentButton(product_name, selection, price, payment_method, order_id))

# =========================================================
# PAYMENT FLOW
# =========================================================

class OrderPaymentSelect(discord.ui.Select):
    def __init__(self, product_name: str, selection: str, price: str):
        self.product_name = product_name
        self.selection = selection
        self.price = price

        options = [
            discord.SelectOption(label="Bitcoin (BTC)", value="btc", emoji="🟠"),
            discord.SelectOption(label="Litecoin (LTC)", value="ltc", emoji="💎"),
            discord.SelectOption(label="Solana (SOL)", value="sol", emoji="🟣"),
            discord.SelectOption(label="Ethereum (ETH)", value="eth", emoji="⚫"),
        ]

        super().__init__(
            placeholder="Choose payment method",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        method = self.values[0]
        wallet = get_wallet(method)
        payment_name = get_payment_name(method)
        order_id = str(uuid.uuid4())[:8].upper()

        embed = discord.Embed(
            title="Order Details",
            description="Please send payment to the wallet below, then press the button once you have sent the funds.",
            color=discord.Color.dark_grey()
        )
        embed.add_field(name="Product", value=self.product_name, inline=False)
        embed.add_field(name="Selection", value=self.selection, inline=False)
        embed.add_field(name="Price", value=self.price, inline=False)
        embed.add_field(name="Payment Method", value=payment_name, inline=False)
        embed.add_field(name="Wallet Address", value=f"`{wallet}`", inline=False)
        embed.add_field(name="Order ID", value=f"`{order_id}`", inline=False)
        embed.set_footer(text="Proxy Services")

        save_order_record(
            order_id=order_id,
            user_id=interaction.user.id,
            product_name=self.product_name,
            selection=self.selection,
            price=self.price,
            payment_method=payment_name,
            status="created"
        )

        await send_order_log(
            title="New Order Created",
            user=interaction.user,
            product_name=self.product_name,
            selection=self.selection,
            price=self.price,
            payment_method=payment_name,
            order_id=order_id,
            event_type="order_created"
        )

        view = FundsSentView(
            product_name=self.product_name,
            selection=self.selection,
            price=self.price,
            payment_method=payment_name,
            order_id=order_id
        )

        try:
            await interaction.user.send(embed=embed, view=view)
            await interaction.response.send_message(
                "I sent your order details in DMs.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )


class OrderPaymentView(discord.ui.View):
    def __init__(self, product_name: str, selection: str, price: str):
        super().__init__(timeout=180)
        self.add_item(OrderPaymentSelect(product_name, selection, price))

# =========================================================
# PRICE MANAGER PANEL
# =========================================================

class PriceChangeModal(discord.ui.Modal, title="Change Price"):
    def __init__(self, category: str, item_name: str):
        super().__init__()
        self.category = category
        self.item_name = item_name

        self.new_price = discord.ui.TextInput(
            label="New Price",
            placeholder="Example: 65 or $65 or 65.00",
            required=True,
            max_length=20
        )
        self.add_item(self.new_price)

    async def on_submit(self, interaction: discord.Interaction):
        global PRICES

        if not is_owner_id(interaction.user.id):
            await interaction.response.send_message("Only the owner can use this.", ephemeral=True)
            return

        formatted_price = normalize_price_input(str(self.new_price))
        PRICES[self.category][self.item_name] = formatted_price
        save_prices(PRICES)

        embed = discord.Embed(
            title="Price Updated",
            color=discord.Color.dark_grey()
        )
        embed.add_field(name="Category", value=CATEGORY_LABELS.get(self.category, self.category), inline=False)
        embed.add_field(name="Item", value=self.item_name, inline=False)
        embed.add_field(name="New Price", value=formatted_price, inline=False)
        embed.set_footer(text="Proxy Services")

        await interaction.response.send_message(embed=embed, ephemeral=True)


class PriceItemSelect(discord.ui.Select):
    def __init__(self, category: str):
        self.category = category
        options = [
            discord.SelectOption(label=item, value=item, description=f"Current: {price}")
            for item, price in PRICES[category].items()
        ]

        super().__init__(
            placeholder="Choose the item to edit",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if not is_owner_id(interaction.user.id):
            await interaction.response.send_message("Only the owner can use this.", ephemeral=True)
            return

        item_name = self.values[0]
        await interaction.response.send_modal(PriceChangeModal(self.category, item_name))


class PriceItemView(discord.ui.View):
    def __init__(self, category: str):
        super().__init__(timeout=180)
        self.add_item(PriceItemSelect(category))


class PriceCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Robux Top-Up", value="robux_topup"),
            discord.SelectOption(label="Robux Gift Card", value="robux_giftcard"),
            discord.SelectOption(label="Apex Coins", value="apex"),
            discord.SelectOption(label="Valorant Points", value="valorant"),
        ]

        super().__init__(
            placeholder="Choose a category",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if not is_owner_id(interaction.user.id):
            await interaction.response.send_message("Only the owner can use this.", ephemeral=True)
            return

        category = self.values[0]

        embed = discord.Embed(
            title="Choose Price Item",
            description=f"Category: **{CATEGORY_LABELS.get(category, category)}**",
            color=discord.Color.dark_grey()
        )
        embed.set_footer(text="Proxy Services")

        await interaction.response.send_message(
            embed=embed,
            view=PriceItemView(category),
            ephemeral=True
        )


class PriceCategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(PriceCategorySelect())

# =========================================================
# ROBUX FLOW
# =========================================================

class RobuxGiftCardAmountSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label, value=value)
            for label, value in ROBUX_GIFTCARD_OPTIONS
        ]
        super().__init__(
            placeholder="Select gift card amount",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        price = get_price("robux_giftcard", selection)

        embed = discord.Embed(
            title="Choose Payment Method",
            description=(
                f"**Product:** Robux Gift Card\n"
                f"**Selection:** {selection}\n"
                f"**Price:** {price}\n\n"
                "Choose your crypto payment method below."
            ),
            color=discord.Color.dark_grey()
        )

        await interaction.response.send_message(
            embed=embed,
            view=OrderPaymentView("Robux Gift Card", selection, price),
            ephemeral=True
        )


class RobuxGiftCardAmountView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(RobuxGiftCardAmountSelect())


class RobuxTopupAmountSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label, value=value)
            for label, value in ROBUX_TOPUP_OPTIONS
        ]
        super().__init__(
            placeholder="Select top-up amount",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        price = get_price("robux_topup", selection)

        embed = discord.Embed(
            title="Choose Payment Method",
            description=(
                f"**Product:** Robux Top-Up\n"
                f"**Selection:** {selection}\n"
                f"**Price:** {price}\n\n"
                "Choose your crypto payment method below."
            ),
            color=discord.Color.dark_grey()
        )

        await interaction.response.send_message(
            embed=embed,
            view=OrderPaymentView("Robux Top-Up", selection, price),
            ephemeral=True
        )


class RobuxTopupAmountView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(RobuxTopupAmountSelect())


class RobuxDeliverySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Gift Card", value="giftcard", emoji="🎁"),
            discord.SelectOption(label="Top-Up", value="topup", emoji="🔄"),
        ]
        super().__init__(
            placeholder="Choose delivery type",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        delivery = self.values[0]

        if delivery == "giftcard":
            embed = discord.Embed(
                title="Select Gift Card Amount",
                description="Choose the gift card amount you want below.",
                color=discord.Color.dark_grey()
            )
            await interaction.response.send_message(
                embed=embed,
                view=RobuxGiftCardAmountView(),
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Select Top-Up Amount",
            description="Choose the Robux top-up amount you want below.",
            color=discord.Color.dark_grey()
        )
        await interaction.response.send_message(
            embed=embed,
            view=RobuxTopupAmountView(),
            ephemeral=True
        )


class RobuxDeliveryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(RobuxDeliverySelect())


class RobuxPurchaseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Click To Purchase",
            style=discord.ButtonStyle.secondary,
            custom_id="robux_purchase_button",
            emoji="🛒"
        )

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Choose Delivery Type",
            description="Select whether you want Gift Card or Top-Up.",
            color=discord.Color.dark_grey()
        )
        await interaction.response.send_message(
            embed=embed,
            view=RobuxDeliveryView(),
            ephemeral=True
        )


class RobuxPurchaseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RobuxPurchaseButton())

# =========================================================
# APEX FLOW
# =========================================================

class ApexAmountSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label, value=value)
            for label, value in APEX_OPTIONS
        ]
        super().__init__(
            placeholder="Select Apex Coins amount",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        price = get_price("apex", selection)

        embed = discord.Embed(
            title="Choose Payment Method",
            description=(
                f"**Product:** Apex Coins\n"
                f"**Selection:** {selection}\n"
                f"**Price:** {price}\n\n"
                "Choose your crypto payment method below."
            ),
            color=discord.Color.dark_grey()
        )

        await interaction.response.send_message(
            embed=embed,
            view=OrderPaymentView("Apex Coins", selection, price),
            ephemeral=True
        )


class ApexAmountView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(ApexAmountSelect())


class ApexPurchaseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Click To Purchase",
            style=discord.ButtonStyle.secondary,
            custom_id="apex_purchase_button",
            emoji="🛒"
        )

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Select Apex Coins Amount",
            description="Choose the amount you want below.",
            color=discord.Color.dark_grey()
        )
        await interaction.response.send_message(
            embed=embed,
            view=ApexAmountView(),
            ephemeral=True
        )


class ApexPurchaseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ApexPurchaseButton())

# =========================================================
# VALORANT FLOW
# =========================================================

class ValorantAmountSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=label, value=value)
            for label, value in VALORANT_OPTIONS
        ]
        super().__init__(
            placeholder="Select Valorant Points amount",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        price = get_price("valorant", selection)

        embed = discord.Embed(
            title="Choose Payment Method",
            description=(
                f"**Product:** Valorant Points\n"
                f"**Selection:** {selection}\n"
                f"**Price:** {price}\n\n"
                "Choose your crypto payment method below."
            ),
            color=discord.Color.dark_grey()
        )

        await interaction.response.send_message(
            embed=embed,
            view=OrderPaymentView("Valorant Points", selection, price),
            ephemeral=True
        )


class ValorantAmountView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(ValorantAmountSelect())


class ValorantPurchaseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Click To Purchase",
            style=discord.ButtonStyle.secondary,
            custom_id="valorant_purchase_button",
            emoji="🛒"
        )

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Select Valorant Points Amount",
            description="Choose the amount you want below.",
            color=discord.Color.dark_grey()
        )
        await interaction.response.send_message(
            embed=embed,
            view=ValorantAmountView(),
            ephemeral=True
        )


class ValorantPurchaseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ValorantPurchaseButton())

# =========================================================
# CHEAP SERVICES FLOW
# =========================================================

class CheapServicesPurchaseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Click To Purchase",
            style=discord.ButtonStyle.secondary,
            custom_id="cheap_services_purchase_button",
            emoji="🛒"
        )

    async def callback(self, interaction: discord.Interaction):
        await create_ticket_from_button(interaction, "Cheap Services")


class CheapServicesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CheapServicesPurchaseButton())

# =========================================================
# PANEL SENDERS
# =========================================================

async def send_robux_panel(channel: discord.TextChannel):
    embed = discord.Embed(title="Robux Orders", color=discord.Color.dark_grey())
    embed.description = (
        "ℹ️ **Important Checkout Information**\n\n"
        "• Don't create a ticket unless you're ready to purchase\n"
        "• There is 0% ban risk when purchasing Robux from us\n"
        "• The lowest amount you can purchase is 1,100 Robux\n"
        "• Upon purchase your Robux will be delivered via a gift card or top-up\n\n"
        "💰 **Top-Up Prices**\n"
        f"• 26,400 Robux → {get_price('robux_topup', '26,400 Robux')}\n"
        f"• 12,100 Robux → {get_price('robux_topup', '12,100 Robux')}\n"
        f"• 5,800 Robux → {get_price('robux_topup', '5,800 Robux')}\n"
        f"• 2,200 Robux → {get_price('robux_topup', '2,200 Robux')}\n"
        f"• 1,100 Robux → {get_price('robux_topup', '1,100 Robux')}\n\n"
        "🎁 **Gift Card Prices**\n"
        f"• $100 Gift Card → {get_price('robux_giftcard', '$100 Gift Card')}\n"
        f"• $50 Gift Card → {get_price('robux_giftcard', '$50 Gift Card')}\n"
        f"• $25 Gift Card → {get_price('robux_giftcard', '$25 Gift Card')}\n"
        f"• $10 Gift Card → {get_price('robux_giftcard', '$10 Gift Card')}"
    )
    embed.set_footer(text="Proxy Services")
    await channel.send(embed=embed, view=RobuxPurchaseView())


async def send_apex_panel(channel: discord.TextChannel):
    embed = discord.Embed(title="Apex Coins Orders", color=discord.Color.dark_grey())
    embed.description = (
        "ℹ️ **Important Checkout Information**\n\n"
        "• Don't create a ticket unless you're ready to purchase\n"
        "• Delivery is done after payment is confirmed\n\n"
        "💰 **Apex Coins Prices**\n"
        f"• 11.5k → {get_price('apex', '11.5k Apex Coins')}\n"
        f"• 6.7k → {get_price('apex', '6.7k Apex Coins')}\n"
        f"• 4.35k → {get_price('apex', '4.35k Apex Coins')}\n"
        f"• 2.15k → {get_price('apex', '2.15k Apex Coins')}"
    )
    embed.set_footer(text="Proxy Services")
    await channel.send(embed=embed, view=ApexPurchaseView())


async def send_valorant_panel(channel: discord.TextChannel):
    embed = discord.Embed(title="Valorant Points Orders", color=discord.Color.dark_grey())
    embed.description = (
        "ℹ️ **Important Checkout Information**\n\n"
        "• Don't create a ticket unless you're ready to purchase\n"
        "• In order to buy it is required to have a microsoft account linked to your ingame account\n"
        "• Delivery is done after payment is confirmed\n\n"
        "💰 **Valorant Points Prices**\n"
        f"• 11000 VP → {get_price('valorant', '11000 VP')}\n"
        f"• 5350 VP → {get_price('valorant', '5350 VP')}"
    )
    embed.set_footer(text="Proxy Services")
    await channel.send(embed=embed, view=ValorantPurchaseView())


async def send_cheap_services_panel(channel: discord.TextChannel):
    embed = discord.Embed(title="Cheap Services", color=discord.Color.dark_grey())

    lines = [f"• {service}" for service in CHEAP_SERVICES_LIST]
    chunks = []
    current = ""
    for line in lines:
        if len(current) + len(line) + 1 > 900:
            chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}".strip()
    if current:
        chunks.append(current)

    embed.description = "ℹ️ **Available Cheap Services**\n\n" + chunks[0]

    for i, chunk in enumerate(chunks[1:], start=2):
        embed.add_field(name=f"More Services {i}", value=chunk, inline=False)

    embed.set_footer(text="Proxy Services")
    await channel.send(embed=embed, view=CheapServicesView())

# =========================================================
# EVENTS
# =========================================================

@bot.event
async def on_ready():
    try:
        bot.add_view(RobuxPurchaseView())
        bot.add_view(ApexPurchaseView())
        bot.add_view(ValorantPurchaseView())
        bot.add_view(CheapServicesView())
        bot.add_view(TicketControlView())

        print(f"Logged in as {bot.user}")
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Game("Proxy Services")
        )
    except Exception as e:
        print(f"on_ready error: {e}")

# =========================================================
# OWNER COMMANDS
# =========================================================

@bot.command(name="confirm_order")
async def confirm_order(ctx, order_id: str = None):
    if not is_owner_id(ctx.author.id):
        await ctx.send("Only the owner can use this command.")
        return

    if not order_id:
        await ctx.send("Usage: `!confirm_order ORDERID`")
        return

    order_id = order_id.upper()
    order = get_order(order_id)

    if not order:
        await ctx.send("Order ID not found.")
        return

    user = await bot.fetch_user(order["user_id"])
    update_order_status(order_id, "confirmed")

    await send_order_log(
        title="Order Confirmed",
        user=user,
        product_name=order["product_name"],
        selection=order["selection"],
        price=order["price"],
        payment_method=order["payment_method"],
        order_id=order_id,
        event_type="order_confirmed"
    )

    product_text = f'{order["selection"]} {order["product_name"]}'.replace("Robux Gift Card", "gift card").replace("Robux Top-Up", "top up")

    embed = discord.Embed(
        title="Order Confirmed",
        description="This order has been marked as completed.",
        color=discord.Color.dark_grey()
    )
    embed.add_field(name="Order ID", value=f"`{order_id}`", inline=False)
    embed.add_field(name="Customer", value=f"<@{order['user_id']}>", inline=False)
    embed.add_field(name="Order", value=product_text, inline=False)
    embed.set_footer(text="Proxy Services")

    await ctx.send(embed=embed)

    success = await dm_order_complete_with_vouch(user, product_text)
    if success:
        await ctx.send(f"Sent completion + vouch DM to <@{order['user_id']}>")
    else:
        await ctx.send("Could not DM the customer.")


@bot.command(name="cancel_order")
async def cancel_order(ctx, order_id: str = None, *, reason: str = None):
    if not is_owner_id(ctx.author.id):
        await ctx.send("Only the owner can use this command.")
        return

    if not order_id:
        await ctx.send("Usage: `!cancel_order ORDERID reason`")
        return

    order_id = order_id.upper()
    order = get_order(order_id)

    if not order:
        await ctx.send("Order ID not found.")
        return

    if not reason:
        reason = "No reason provided."

    user = await bot.fetch_user(order["user_id"])
    update_order_status(order_id, "cancelled", {"cancel_reason": reason})

    await send_order_log(
        title="Order Cancelled",
        user=user,
        product_name=order["product_name"],
        selection=order["selection"],
        price=order["price"],
        payment_method=order["payment_method"],
        order_id=order_id,
        event_type="order_cancelled"
    )

    embed = discord.Embed(
        title="Order Cancelled",
        description="This order has been cancelled.",
        color=discord.Color.dark_grey()
    )
    embed.add_field(name="Order ID", value=f"`{order_id}`", inline=False)
    embed.add_field(name="Customer", value=f"<@{order['user_id']}>", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(text="Proxy Services")

    await ctx.send(embed=embed)

    try:
        dm_embed = discord.Embed(
            title="Order Cancelled",
            description=f"Your order has been cancelled.\n\n**Reason:** {reason}",
            color=discord.Color.dark_grey()
        )
        dm_embed.set_footer(text="Proxy Services")
        await user.send(embed=dm_embed)
        await ctx.send(f"Sent cancellation DM to <@{order['user_id']}>")
    except Exception as e:
        await ctx.send(f"Could not DM the customer. Error: {e}")


@bot.command(name="change_prices")
async def change_prices(ctx):
    if not is_owner_id(ctx.author.id):
        await ctx.send("Only the owner can use this command.")
        return

    embed = discord.Embed(
        title="Price Manager",
        description="Choose a category below to change prices.",
        color=discord.Color.dark_grey()
    )
    embed.set_footer(text="Proxy Services")
    await ctx.send(embed=embed, view=PriceCategoryView())


@bot.command(name="set_price")
async def set_price(ctx, category: str = None, item: str = None, price: str = None):
    if not is_owner_id(ctx.author.id):
        await ctx.send("Only the owner can use this command.")
        return

    if not category or not item or not price:
        await ctx.send(
            "Usage: `!set_price category \"item name\" newprice`\n\n"
            "Or use: `!change_prices`"
        )
        return

    category = category.lower()

    if category not in PRICES:
        await ctx.send("Invalid category. Use `!change_prices` or `!price_categories`.")
        return

    if item not in PRICES[category]:
        valid_items = "\n".join([f"• {x}" for x in PRICES[category].keys()])
        await ctx.send(f"Invalid item for `{category}`.\n\nValid items:\n{valid_items}")
        return

    new_price = normalize_price_input(price)
    PRICES[category][item] = new_price
    save_prices(PRICES)

    embed = discord.Embed(title="Price Updated", color=discord.Color.dark_grey())
    embed.add_field(name="Category", value=category, inline=False)
    embed.add_field(name="Item", value=item, inline=False)
    embed.add_field(name="New Price", value=new_price, inline=False)
    embed.set_footer(text="Proxy Services")
    await ctx.send(embed=embed)


@bot.command(name="price_categories")
async def price_categories(ctx):
    if not is_owner_id(ctx.author.id):
        await ctx.send("Only the owner can use this command.")
        return

    embed = discord.Embed(
        title="Price Categories",
        description=(
            "These are the valid categories for price changes:\n\n"
            "• `robux_topup`\n"
            "• `robux_giftcard`\n"
            "• `apex`\n"
            "• `valorant`"
        ),
        color=discord.Color.dark_grey()
    )
    embed.set_footer(text="Proxy Services")
    await ctx.send(embed=embed)


@bot.command(name="price_items")
async def price_items(ctx, category: str = None):
    if not is_owner_id(ctx.author.id):
        await ctx.send("Only the owner can use this command.")
        return

    if not category:
        await ctx.send("Usage: `!price_items category`")
        return

    category = category.lower()

    if category not in PRICES:
        await ctx.send("Invalid category. Use `!price_categories` first.")
        return

    items_text = "\n".join([f"• `{item}` → {price}" for item, price in PRICES[category].items()])

    embed = discord.Embed(
        title=f"Items in {category}",
        description=items_text,
        color=discord.Color.dark_grey()
    )
    embed.set_footer(text="Proxy Services")
    await ctx.send(embed=embed)

# =========================================================
# PANEL COMMANDS
# =========================================================

@bot.command(name="robux_panel")
async def robux_panel_prefix(ctx):
    if not is_admin(ctx.author):
        await ctx.send("You need administrator permission to use this command.")
        return
    await send_robux_panel(ctx.channel)
    await ctx.send("Robux panel posted.")


@bot.command(name="apex_panel")
async def apex_panel_prefix(ctx):
    if not is_admin(ctx.author):
        await ctx.send("You need administrator permission to use this command.")
        return
    await send_apex_panel(ctx.channel)
    await ctx.send("Apex panel posted.")


@bot.command(name="valorant_panel")
async def valorant_panel_prefix(ctx):
    if not is_admin(ctx.author):
        await ctx.send("You need administrator permission to use this command.")
        return
    await send_valorant_panel(ctx.channel)
    await ctx.send("Valorant panel posted.")


@bot.command(name="cheap_services_panel")
async def cheap_services_panel_prefix(ctx):
    if not is_admin(ctx.author):
        await ctx.send("You need administrator permission to use this command.")
        return
    await send_cheap_services_panel(ctx.channel)
    await ctx.send("Cheap services panel posted.")

# =========================================================
# BASIC COMMANDS
# =========================================================

@bot.command(name="help")
async def help_prefix(ctx):
    embed = discord.Embed(
        title="Proxy Services Help",
        color=discord.Color.dark_grey()
    )
    embed.description = (
        "**Customer Commands**\n"
        "• `!help`\n"
        "• `!ping`\n\n"
        "**Owner Commands**\n"
        "• `!confirm_order ORDERID`\n"
        "• `!cancel_order ORDERID reason`\n"
        "• `!change_prices`\n"
        "• `!set_price category \"item\" price`\n"
        "• `!price_categories`\n"
        "• `!price_items category`\n\n"
        "**Admin Commands**\n"
        "• `!robux_panel`\n"
        "• `!apex_panel`\n"
        "• `!valorant_panel`\n"
        "• `!cheap_services_panel`"
    )
    embed.set_footer(text="Proxy Services")
    await ctx.send(embed=embed)


@bot.command(name="ping")
async def ping_prefix(ctx):
    await ctx.send("Pong. Bot is online.")


bot.run(TOKEN)