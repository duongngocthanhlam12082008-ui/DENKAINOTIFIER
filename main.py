"""
Discord Multi-System Bot  —  Components V2
Single File Edition  |  discord.py 2.4+

Install : pip install discord.py aiohttp
Run     : python c.py
Commands: /ticket  /welcome  /verify  /owner  /payment  /help
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import random
import string
import time
from datetime import datetime, timezone
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks


# ═══════════════════════════════════════════════════════════════════════════════
#  Credentials
# ═══════════════════════════════════════════════════════════════════════════════

TOKEN    = os.getenv("TOKEN", "")
OWNER_ID = 1498384419805986886
PREFIX   = "!"


# ═══════════════════════════════════════════════════════════════════════════════
#  Ticket Categories
# ═══════════════════════════════════════════════════════════════════════════════

TICKET_CATEGORIES = {
    "support": {
        "label":       "Technical Support",
        "description": "Technical Issues, Bugs, Installation",
    },
    "billing": {
        "label":       "Billing",
        "description": "Invoices, Transactions, Refunds",
    },
    "report": {
        "label":       "Report Violation",
        "description": "Report Users Or Content",
    },
    "general": {
        "label":       "General Inquiry",
        "description": "General Questions, Feedback",
    },
    "partner": {
        "label":       "Partnership",
        "description": "Collaboration Proposals, Advertising",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
#  Strings
# ═══════════════════════════════════════════════════════════════════════════════

S = {
    "panel_title":            "Support Center",
    "panel_categories_title": "### Available Categories",
    "panel_placeholder":      "Select A Ticket Category...",
    "modal_title":            "Create A Support Ticket",
    "modal_subject_label":    "Subject",
    "modal_subject_ph":       "Briefly Describe Your Issue...",
    "modal_detail_label":     "Detailed Description",
    "modal_detail_ph":        "Provide As Much Detail As Possible...",
    "ticket_header":          "Your Ticket Has Been Created. Our Support Team Will Respond As Soon As Possible.",
    "ticket_opened_by":       "Opened By",
    "ticket_subject":         "Subject",
    "ticket_created":         "Created",
    "ticket_issue":           "Issue Description",
    "btn_close":              "Close Ticket",
    "btn_claim":              "Claim Ticket",
    "close_confirm_q":        "Are You Sure You Want To Close This Ticket?",
    "close_cancelled":        "Close Request Cancelled.",
    "close_header":           "Ticket Closed",
    "close_body":             "If You Need Further Assistance, Please Open A New Ticket.",
    "close_closed_by":        "Closed By",
    "close_countdown":        "This Ticket Will Be Deleted In **10 Seconds**.",
    "claim_staff_only":       "Only Staff Members Can Claim Tickets.",
    "claim_already":          "This Ticket Is Already Claimed By",
    "claim_success_ch":       "Has Claimed This Ticket",
    "claim_success_note":     "All Further Support Will Be Handled By This Staff Member.",
    "claim_ack":              "You Have Successfully Claimed This Ticket.",
    "transcript_ok":          "Transcript Generated Successfully.",
    "err_not_ticket":         "This Channel Is Not A Ticket.",
    "err_no_setup":           "System Not Configured. Run /ticket Setup First.",
    "err_no_category":        "Category Not Found. Please Run /ticket Setup First.",
    "err_open_ticket":        "You Already Have An Open Ticket",
    "err_open_close_first":   "Please Close It Before Opening A New One.",
    "err_panel_sent":         "Panel Sent Successfully.",
    "user_added":             "Has Been Added To This Ticket.",
    "user_removed":           "Has Been Removed From This Ticket.",
    "setup_ok":               "Setup Complete",
    "setup_category":         "Category",
    "setup_role":             "Support Role",
    "setup_log":              "Log Channel",
    "setup_not_set":          "Not Set",
    "list_empty":             "No Open Tickets Found.",
    "list_title":             "Open Tickets",
    "list_unclaimed":         "Unclaimed",
    "cat_support_label":      "Technical Support",
    "cat_support_desc":       "Technical Issues, Bugs, Installation",
    "cat_billing_label":      "Billing",
    "cat_billing_desc":       "Invoices, Transactions, Refunds",
    "cat_report_label":       "Report Violation",
    "cat_report_desc":        "Report Users Or Content",
    "cat_general_label":      "General Inquiry",
    "cat_general_desc":       "General Questions, Feedback",
    "cat_partner_label":      "Partnership",
    "cat_partner_desc":       "Collaboration Proposals, Advertising",
}

def t(key: str) -> str:
    return S.get(key, key)

def _cat_label(key: str) -> str:
    return S.get(f"cat_{key}_label", key)

def _cat_desc(key: str) -> str:
    return S.get(f"cat_{key}_desc", key)


# ═══════════════════════════════════════════════════════════════════════════════
#  Logging
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("Bot")


# ═══════════════════════════════════════════════════════════════════════════════
#  Owner Check
# ═══════════════════════════════════════════════════════════════════════════════

def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "Access Denied. This Command Is Restricted To The Bot Owner.",
                ephemeral=True,
            )
            return False
        return True
    return app_commands.check(predicate)


# ═══════════════════════════════════════════════════════════════════════════════
#  Components V2 Helpers
# ═══════════════════════════════════════════════════════════════════════════════

V2_FLAG = 1 << 15

def _text(content: str) -> dict:
    return {"type": 10, "content": content}

def _separator(divider: bool = True, spacing: int = 1) -> dict:
    return {"type": 14, "divider": divider, "spacing": spacing}

def _select(custom_id: str, placeholder: str, options: list[dict]) -> dict:
    return {
        "type": 1,
        "components": [{
            "type":        3,
            "custom_id":   custom_id,
            "placeholder": placeholder,
            "min_values":  1,
            "max_values":  1,
            "options":     options,
        }],
    }

def _button(label: str, custom_id: str, style: int = 2) -> dict:
    return {"type": 2, "style": style, "label": label, "custom_id": custom_id}

def _action_row(*buttons) -> dict:
    return {"type": 1, "components": list(buttons)}

def _container(*components) -> dict:
    return {"type": 17, "components": list(components)}

def _section(text_content: str, thumbnail_url: str) -> dict:
    return {
        "type": 9,
        "components": [{"type": 10, "content": text_content}],
        "accessory":  {"type": 11, "media": {"url": thumbnail_url}},
    }

async def _v2_send(channel: discord.TextChannel, components: list[dict]) -> dict:
    url     = f"https://discord.com/api/v10/channels/{channel.id}/messages"
    headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
    payload = {"flags": V2_FLAG, "components": components}
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload, headers=headers) as r:
            data = await r.json()
            if r.status not in (200, 201):
                log.error("V2 Send Error %s: %s", r.status, data)
            return data

async def _v2_respond(
    interaction: discord.Interaction,
    components: list[dict],
    *,
    ephemeral: bool = True,
) -> None:
    flags   = V2_FLAG | (64 if ephemeral else 0)
    url     = f"https://discord.com/api/v10/interactions/{interaction.id}/{interaction.token}/callback"
    headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
    payload = {"type": 4, "data": {"flags": flags, "components": components}}
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload, headers=headers) as r:
            if r.status not in (200, 204):
                log.error("V2 Respond Error %s: %s", r.status, await r.json())

async def _v2_followup(
    interaction: discord.Interaction,
    components: list[dict],
    *,
    ephemeral: bool = True,
) -> None:
    flags   = V2_FLAG | (64 if ephemeral else 0)
    url     = f"https://discord.com/api/v10/webhooks/{interaction.application_id}/{interaction.token}"
    headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
    payload = {"flags": flags, "components": components}
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload, headers=headers) as r:
            if r.status not in (200, 201):
                log.error("V2 Followup Error %s: %s", r.status, await r.json())

async def _v2_edit_msg(channel_id: int, message_id: int, components: list[dict]) -> None:
    url     = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"
    headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
    payload = {"flags": V2_FLAG, "components": components}
    async with aiohttp.ClientSession() as s:
        async with s.patch(url, json=payload, headers=headers) as r:
            if r.status not in (200, 201):
                log.error("V2 Edit Error %s: %s", r.status, await r.json())


# ═══════════════════════════════════════════════════════════════════════════════
#  In-Memory Store
# ═══════════════════════════════════════════════════════════════════════════════

_STORE: dict[int, dict] = {}

def _gdata(guild_id: int) -> dict:
    return _STORE.setdefault(guild_id, {
        "ticket_category":  None,
        "log_channel":      None,
        "support_role":     None,
        "panel_channel":    None,
        "counter":          0,
        "tickets":          {},
        "welcome_channel":  None,
        "welcome_purchase": None,
        "welcome_rules":    None,
        "welcome_news":     None,
        "veri_enabled":     False,
        "veri_channel":     None,
        "veri_role_id":     None,
        "veri_grant_id":    None,
        # ── Payment ──────────────────────────────────────────────────────────
        "pay_bank_id":      "ICB",           # Vietinbank VietQR code
        "pay_account_no":   "0907617630",    # STK Vietinbank
        "pay_account_name": "NGUYEN VAN A",  # Doi thanh ten chu TK that
        "pay_casso_key":    None,             # Casso API key for auto-confirm
        "pay_log_channel":  None,             # Channel to log confirmed payments
        "pay_confirm_role": None,             # Role to ping on confirm (optional)
        "pay_timeout":      600,              # Seconds before payment expires (default 10 min)
        "payments":         {},               # { ref_code: payment_data }
    })

def _next_id(guild_id: int) -> str:
    d = _gdata(guild_id)
    d["counter"] += 1
    return f"{d['counter']:04d}"


# ═══════════════════════════════════════════════════════════════════════════════
#  VietQR Helper
# ═══════════════════════════════════════════════════════════════════════════════
#
#  VietQR public URL — no API key needed for QR image generation
#  Format: https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NO}-{TEMPLATE}.png
#            ?amount={AMOUNT}&addInfo={DESCRIPTION}&accountName={NAME}

VIETQR_BANKS = {
    "ACB":    "ACB",
    "BIDV":   "BIDV",
    "MB":     "MB",
    "MSB":    "MSB",
    "OCB":    "OCB",
    "SCB":    "SCB",
    "SHB":    "SHB",
    "TCB":    "TCB",       # Techcombank
    "TPB":    "TPB",       # TPBank
    "VCB":    "VCB",       # Vietcombank
    "VIB":    "VIB",
    "VPB":    "VPB",       # VPBank
    "VIETINBANK": "ICB",
    "AGRIBANK":   "VBA",
    "TPBANK":     "TPB",
    "SACOMBANK":  "STB",
    "HDBANK":     "HDB",
    "SEABANK":    "SEAB",
    "ABBANK":     "ABB",
    "BAOVIETBANK":"BVB",
}

def _vietqr_url(bank_id: str, account_no: str, account_name: str, amount: int, ref: str) -> str:
    """Generate VietQR image URL."""
    from urllib.parse import quote
    base  = f"https://img.vietqr.io/image/{bank_id}-{account_no}-compact2.png"
    query = (
        f"?amount={amount}"
        f"&addInfo={quote(ref)}"
        f"&accountName={quote(account_name)}"
    )
    return base + query

def _gen_ref(guild_id: int, user_id: int) -> str:
    """Generate a unique 8-char payment reference code."""
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(chars, k=6))
    return f"PAY{suffix}"


# ═══════════════════════════════════════════════════════════════════════════════
#  Casso Auto-Confirm Helper
# ═══════════════════════════════════════════════════════════════════════════════
#
#  Casso (casso.vn) — webhooks & polling API for Vietnamese bank transactions.
#  Docs: https://casso.vn/documentation
#  After linking your bank account on Casso, use the API key to poll transactions.

async def _casso_get_transactions(api_key: str, from_id: int = 0) -> list[dict]:
    """
    Poll recent transactions from Casso API.
    Returns list of transaction dicts with keys: id, amount, description, when
    """
    url     = "https://oauth.casso.vn/v2/transactions"
    headers = {"Authorization": f"Apikey {api_key}"}
    params  = {"page": 1, "pageSize": 20}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    log.warning("Casso API Error: %s", r.status)
                    return []
                data = await r.json()
                records = data.get("data", {}).get("records", [])
                return records
    except Exception as e:
        log.warning("Casso Poll Error: %s", e)
        return []


# ═══════════════════════════════════════════════════════════════════════════════
#  Payment Store Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _payment_create(guild_id: int, user_id: int, amount: int, description: str, channel_id: int, message_id: int) -> dict:
    d   = _gdata(guild_id)
    ref = _gen_ref(guild_id, user_id)
    # Ensure ref is unique
    while ref in d["payments"]:
        ref = _gen_ref(guild_id, user_id)
    payment = {
        "ref":         ref,
        "guild_id":    guild_id,
        "user_id":     user_id,
        "amount":      amount,
        "description": description,
        "channel_id":  channel_id,
        "message_id":  message_id,
        "status":      "pending",    # pending | confirmed | expired | cancelled
        "created_at":  time.time(),
        "confirmed_at": None,
        "confirmed_by_tx": None,
    }
    d["payments"][ref] = payment
    return payment

def _payment_get(guild_id: int, ref: str) -> dict | None:
    return _gdata(guild_id)["payments"].get(ref)

def _payment_confirm(guild_id: int, ref: str, tx_id: str) -> bool:
    p = _payment_get(guild_id, ref)
    if not p or p["status"] != "pending":
        return False
    p["status"]         = "confirmed"
    p["confirmed_at"]   = time.time()
    p["confirmed_by_tx"] = tx_id
    return True

def _payment_expire(guild_id: int, ref: str) -> bool:
    p = _payment_get(guild_id, ref)
    if not p or p["status"] != "pending":
        return False
    p["status"] = "expired"
    return True


# ═══════════════════════════════════════════════════════════════════════════════
#  UI — Ticket Category Select & Panel View
# ═══════════════════════════════════════════════════════════════════════════════

class CategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=v["label"], value=k, description=v["description"])
            for k, v in TICKET_CATEGORIES.items()
        ]
        super().__init__(
            placeholder="Select A Ticket Category...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket:category_select",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            CreateModal(self.values[0], interaction.guild_id)
        )


class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CategorySelect())


# ═══════════════════════════════════════════════════════════════════════════════
#  UI — Ticket Create Modal
# ═══════════════════════════════════════════════════════════════════════════════

class CreateModal(discord.ui.Modal, title="Create A Support Ticket"):
    def __init__(self, category_key: str, guild_id: int = 0):
        super().__init__(title=t("modal_title"))
        self.category_key = category_key
        self.guild_id     = guild_id
        self.subject = discord.ui.TextInput(
            label=t("modal_subject_label"),
            placeholder=t("modal_subject_ph"),
            max_length=100,
            required=True,
        )
        self.detail = discord.ui.TextInput(
            label=t("modal_detail_label"),
            placeholder=t("modal_detail_ph"),
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True,
        )
        self.add_item(self.subject)
        self.add_item(self.detail)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await _create_ticket(
            interaction=interaction,
            category_key=self.category_key,
            subject=self.subject.value,
            description=self.detail.value,
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  UI — Ticket Control & Confirm Close
# ═══════════════════════════════════════════════════════════════════════════════

class ControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="ticket:close",
        row=0,
    )
    async def close(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_message(
            t("close_confirm_q"),
            view=ConfirmCloseView(),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Claim Ticket",
        style=discord.ButtonStyle.success,
        custom_id="ticket:claim",
        row=0,
    )
    async def claim(self, interaction: discord.Interaction, _: discord.ui.Button):
        await _claim_ticket(interaction)


class ConfirmCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content=t("close_countdown"), view=None)
        await _do_close_ticket(interaction)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content=t("close_cancelled"), view=None)


# ═══════════════════════════════════════════════════════════════════════════════
#  UI — Payment Cancel Button
# ═══════════════════════════════════════════════════════════════════════════════

class PaymentView(discord.ui.View):
    def __init__(self, ref: str, guild_id: int):
        super().__init__(timeout=None)
        self.ref      = ref
        self.guild_id = guild_id

    @discord.ui.button(
        label="Cancel Payment",
        style=discord.ButtonStyle.danger,
        custom_id="payment:cancel",
    )
    async def cancel_payment(self, interaction: discord.Interaction, btn: discord.ui.Button):
        p = _payment_get(self.guild_id, self.ref)
        if not p:
            return await interaction.response.send_message("Payment Not Found.", ephemeral=True)
        if p["status"] != "pending":
            return await interaction.response.send_message(
                f"Payment Is Already **{p['status'].upper()}**.", ephemeral=True
            )
        if p["user_id"] != interaction.user.id and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(
                "Only The Payment Owner Can Cancel This.", ephemeral=True
            )
        _payment_expire(self.guild_id, self.ref)
        btn.disabled = True
        await interaction.response.edit_message(view=self)
        await _v2_edit_msg(p["channel_id"], p["message_id"], [
            _container(
                _text("## Payment Cancelled"),
                _separator(),
                _text(
                    f"**Reference:** `{self.ref}`\n"
                    f"**Status:** ❌ Cancelled\n"
                    f"-# Cancelled By {interaction.user.mention}"
                ),
            )
        ])
        log.info("Payment %s cancelled by %s", self.ref, interaction.user)


# ═══════════════════════════════════════════════════════════════════════════════
#  UI — Verification View
# ═══════════════════════════════════════════════════════════════════════════════

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.secondary,
        custom_id="verify:btn",
    )
    async def verify_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        d      = _gdata(interaction.guild_id)
        guild  = interaction.guild
        member: discord.Member = interaction.user  # type: ignore

        if not d.get("veri_enabled"):
            return await interaction.response.send_message(
                "The Verification System Is Currently Disabled.", ephemeral=True
            )

        unverified = guild.get_role(d.get("veri_role_id") or 0)
        if unverified and unverified not in member.roles:
            return await interaction.response.send_message(
                "You Are Already Verified!", ephemeral=True
            )

        grant_role = guild.get_role(d.get("veri_grant_id") or 0)
        if not grant_role:
            return await interaction.response.send_message(
                "Verified Role Not Found. Please Contact An Admin.", ephemeral=True
            )

        try:
            await member.add_roles(grant_role, reason="Verified Via Verification Panel")
            if unverified and unverified in member.roles:
                await member.remove_roles(unverified, reason="Member Verified Successfully")
        except discord.Forbidden:
            return await interaction.response.send_message(
                "Bot Lacks Permission To Assign Roles. Please Contact An Admin.",
                ephemeral=True,
            )

        await _v2_respond(interaction, [
            _container(
                _text("## Verification Complete"),
                _separator(),
                _text(
                    f"Welcome To The Server, {member.mention}!\n"
                    f"You Have Been Assigned The **{grant_role.name}** Role.\n"
                    "-# You Now Have Full Access To All Channels."
                ),
            )
        ])
        log.info("Verified %s - Assigned '%s' In '%s'", member, grant_role.name, guild.name)


# ═══════════════════════════════════════════════════════════════════════════════
#  Bot Setup
# ═══════════════════════════════════════════════════════════════════════════════

intents                 = discord.Intents.default()
intents.message_content = True
intents.members         = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


@bot.event
async def on_ready():
    bot.add_view(PanelView())
    bot.add_view(ControlView())
    bot.add_view(VerifyView())
    await bot.tree.sync()
    await bot.change_presence(status=discord.Status.online)
    # Start background tasks
    if not payment_checker.is_running():
        payment_checker.start()
    if not payment_expiry.is_running():
        payment_expiry.start()
    log.info(
        "Logged In As %s  |  Guilds: %d  |  Owner ID: %d",
        bot.user, len(bot.guilds), OWNER_ID,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Background Task — Payment Auto-Confirm (Casso Poll every 15s)
# ═══════════════════════════════════════════════════════════════════════════════

@tasks.loop(seconds=15)
async def payment_checker():
    """Poll Casso for new transactions and auto-confirm matching payments."""
    for guild_id, gd in list(_STORE.items()):
        casso_key = gd.get("pay_casso_key")
        if not casso_key:
            continue

        pending = {
            ref: p for ref, p in gd["payments"].items()
            if p["status"] == "pending"
        }
        if not pending:
            continue

        txs = await _casso_get_transactions(casso_key)
        for tx in txs:
            desc    = str(tx.get("description", "") or tx.get("memo", "")).upper()
            amount  = int(tx.get("amount", 0))
            tx_id   = str(tx.get("id", ""))

            for ref, p in list(pending.items()):
                if p["status"] != "pending":
                    continue
                if ref.upper() in desc and amount >= p["amount"]:
                    if _payment_confirm(guild_id, ref, tx_id):
                        await _notify_payment_confirmed(guild_id, ref)
                        pending.pop(ref, None)
                        break

@payment_checker.before_loop
async def before_checker():
    await bot.wait_until_ready()


# ═══════════════════════════════════════════════════════════════════════════════
#  Background Task — Payment Expiry Check (every 60s)
# ═══════════════════════════════════════════════════════════════════════════════

@tasks.loop(seconds=60)
async def payment_expiry():
    """Expire pending payments that have timed out."""
    now = time.time()
    for guild_id, gd in list(_STORE.items()):
        timeout = gd.get("pay_timeout", 600)
        for ref, p in list(gd["payments"].items()):
            if p["status"] != "pending":
                continue
            if now - p["created_at"] > timeout:
                if _payment_expire(guild_id, ref):
                    await _notify_payment_expired(guild_id, ref)

@payment_expiry.before_loop
async def before_expiry():
    await bot.wait_until_ready()


# ═══════════════════════════════════════════════════════════════════════════════
#  Payment Notifications
# ═══════════════════════════════════════════════════════════════════════════════

async def _notify_payment_confirmed(guild_id: int, ref: str):
    """Edit the QR message and send log when a payment is confirmed."""
    d       = _gdata(guild_id)
    p       = d["payments"].get(ref)
    if not p:
        return

    guild = bot.get_guild(guild_id)
    if not guild:
        return

    member = guild.get_member(p["user_id"])
    ts     = int(time.time())

    # Edit original QR message to show confirmed
    try:
        await _v2_edit_msg(p["channel_id"], p["message_id"], [
            _container(
                _text("## ✅ Payment Confirmed"),
                _separator(),
                _text(
                    f"**Reference:** `{ref}`\n"
                    f"**Amount:** `{p['amount']:,} VND`\n"
                    f"**Status:** ✅ Confirmed\n"
                    f"**Payer:** {member.mention if member else '<@' + str(p['user_id']) + '>'}\n"
                    f"-# Confirmed <t:{ts}:R>"
                ),
            )
        ])
    except Exception as e:
        log.warning("Could Not Edit Payment Message: %s", e)

    # Log to payment log channel
    log_ch_id = d.get("pay_log_channel")
    if log_ch_id:
        log_ch = guild.get_channel(log_ch_id)
        if log_ch:
            ping_role = d.get("pay_confirm_role")
            ping_txt  = f"<@&{ping_role}> " if ping_role else ""
            await _v2_send(log_ch, [  # type: ignore
                _container(
                    _text(f"## ✅ Payment Received"),
                    _separator(),
                    _section(
                        f"**Reference:** `{ref}`\n"
                        f"**Amount:** `{p['amount']:,} VND`\n"
                        f"**Description:** {p['description']}\n"
                        f"**Payer:** {member.mention if member else 'ID: ' + str(p['user_id'])}\n"
                        f"**TX ID:** `{p.get('confirmed_by_tx', 'N/A')}`",
                        member.display_avatar.with_size(256).url if member else "https://cdn.discordapp.com/embed/avatars/0.png",
                    ),
                    _separator(),
                    _text(f"{ping_txt}-# <t:{ts}:F>"),
                )
            ])

    log.info("Payment %s confirmed for user %s — %s VND", ref, p["user_id"], p["amount"])


async def _notify_payment_expired(guild_id: int, ref: str):
    """Edit the QR message to show expired."""
    d = _gdata(guild_id)
    p = d["payments"].get(ref)
    if not p:
        return
    try:
        await _v2_edit_msg(p["channel_id"], p["message_id"], [
            _container(
                _text("## ⏰ Payment Expired"),
                _separator(),
                _text(
                    f"**Reference:** `{ref}`\n"
                    f"**Amount:** `{p['amount']:,} VND`\n"
                    f"**Status:** ⏰ Expired — No Payment Received\n"
                    f"-# Please Run `/payment create` To Generate A New QR."
                ),
            )
        ])
    except Exception as e:
        log.warning("Could Not Edit Expired Payment Message: %s", e)
    log.info("Payment %s expired", ref)


# ═══════════════════════════════════════════════════════════════════════════════
#  Event — Member Join
# ═══════════════════════════════════════════════════════════════════════════════

@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild
    d     = _gdata(guild.id)

    if d.get("veri_enabled"):
        unverified = guild.get_role(d.get("veri_role_id") or 0)
        if unverified:
            try:
                await member.add_roles(unverified, reason="Auto-Assigned Unverified Role On Join")
                log.info("Auto-Assigned Unverified To %s In '%s'", member, guild.name)
            except discord.Forbidden:
                log.warning("Cannot Auto-Assign Unverified To %s - Missing Permissions", member)

    wch = guild.get_channel(d.get("welcome_channel") or 0)
    if not wch:
        return

    def _ref(ch_id) -> str:
        return f"<#{ch_id}>" if ch_id else "`Not Set`"

    ts         = int(datetime.now(timezone.utc).timestamp())
    avatar_url = member.display_avatar.with_size(256).url

    await _v2_send(wch, [  # type: ignore
        _container(
            _text(f"## Welcome To {guild.name}!"),
            _separator(),
            _section(
                f"**Welcome {member.mention}!**\n"
                f"> Purchase At {_ref(d.get('welcome_purchase'))}\n"
                f"> Rules In {_ref(d.get('welcome_rules'))}\n"
                f"> News In {_ref(d.get('welcome_news'))}",
                avatar_url,
            ),
            _separator(),
            _text(f"-# Member #{guild.member_count}  ·  <t:{ts}:F>"),
        )
    ])
    log.info("Welcome Sent For %s In '%s' (Member #%d)", member, guild.name, guild.member_count)


# ═══════════════════════════════════════════════════════════════════════════════
#  Ticket Logic
# ═══════════════════════════════════════════════════════════════════════════════

async def _create_ticket(
    interaction: discord.Interaction,
    category_key: str,
    subject: str,
    description: str,
):
    guild: discord.Guild = interaction.guild  # type: ignore
    d = _gdata(guild.id)

    stale = [
        cid for cid, td in d["tickets"].items()
        if td.get("open") and guild.get_channel(cid) is None
    ]
    for cid in stale:
        d["tickets"].pop(cid, None)

    for ch_id, td in d["tickets"].items():
        if td.get("author_id") == interaction.user.id and td.get("open"):
            ch     = guild.get_channel(ch_id)
            ch_ref = ch.mention if ch else f"<#{ch_id}>"
            return await interaction.followup.send(
                f"{t('err_open_ticket')}: {ch_ref}\n{t('err_open_close_first')}",
                ephemeral=True,
            )

    cat_ch = guild.get_channel(d["ticket_category"])
    if cat_ch is None:
        return await interaction.followup.send(t("err_no_category"), ephemeral=True)

    support_role = guild.get_role(d["support_role"]) if d["support_role"] else None
    cat_info     = TICKET_CATEGORIES[category_key]
    ticket_id    = _next_id(guild.id)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user:   discord.PermissionOverwrite(
            read_messages=True, send_messages=True,
            attach_files=True, embed_links=True,
        ),
        guild.me: discord.PermissionOverwrite(
            read_messages=True, send_messages=True,
            manage_channels=True, manage_messages=True,
        ),
    }
    if support_role:
        overwrites[support_role] = discord.PermissionOverwrite(
            read_messages=True, send_messages=True, attach_files=True,
        )

    channel: discord.TextChannel = await guild.create_text_channel(
        name=f"ticket-{ticket_id}-{interaction.user.name[:10]}",
        category=cat_ch,  # type: ignore
        overwrites=overwrites,
        topic=f"[{cat_info['label']}] {subject} | {interaction.user}",
    )

    ts = int(datetime.now(timezone.utc).timestamp())
    d["tickets"][channel.id] = {
        "id":           ticket_id,
        "author_id":    interaction.user.id,
        "author_name":  str(interaction.user),
        "category":     cat_info["label"],
        "category_key": category_key,
        "subject":      subject,
        "description":  description,
        "open":         True,
        "claimed_by":   None,
        "created_at":   datetime.now(timezone.utc).isoformat(),
    }

    ping = interaction.user.mention + (f" {support_role.mention}" if support_role else "")
    await channel.send(content=ping)

    await _v2_send(channel, [
        _container(
            _text(f"## Ticket #{ticket_id}  —  {_cat_label(category_key)}"),
            _separator(),
            _text(t("ticket_header")),
            _separator(),
            _section(
                f"**{t('ticket_opened_by')}:** {interaction.user.mention} (`{interaction.user}`)\n"
                f"**{t('ticket_subject')}:** {subject}\n"
                f"**{t('ticket_created')}:** <t:{ts}:F>",
                interaction.user.display_avatar.with_size(256).url,
            ),
            _separator(),
            _text(f"**{t('ticket_issue')}:**\n>>> {description}"),
            _separator(),
            _action_row(
                _button(t("btn_close"), "ticket:close", style=4),
                _button(t("btn_claim"), "ticket:claim", style=3),
            ),
        )
    ])

    await interaction.followup.send(
        f"Ticket Created Successfully: {channel.mention}", ephemeral=True
    )
    await _log_event(guild, "CREATE", channel.id, interaction.user, subject)
    log.info("Ticket #%s Created By %s", ticket_id, interaction.user)


async def _do_close_ticket(interaction: discord.Interaction):
    guild: discord.Guild = interaction.guild  # type: ignore
    d  = _gdata(guild.id)
    td = d["tickets"].get(interaction.channel_id)
    if not td:
        return

    td["open"] = False
    channel: discord.TextChannel = interaction.channel  # type: ignore

    author = guild.get_member(td["author_id"])
    if author:
        await channel.set_permissions(author, send_messages=False)

    ts = int(datetime.now(timezone.utc).timestamp())
    await _v2_send(channel, [
        _container(
            _text(f"## {t('close_header')}"),
            _separator(),
            _text(t("close_body")),
            _separator(),
            _text(f"-# {t('close_closed_by')} {interaction.user.mention}  —  <t:{ts}:F>"),
        )
    ])

    author = guild.get_member(td["author_id"])
    try:
        buf, fname = await _build_transcript(channel, td, str(interaction.user))
        dm_body = (
            f"**Ticket #{td.get('id', '????')} — {td.get('category', '')}**\n"
            f"Your Ticket In **{guild.name}** Has Been Closed.\n"
            f"A Transcript Of The Conversation Is Attached Below."
        )
        if author:
            await author.send(content=dm_body, file=discord.File(buf, filename=fname))
        log_ch_id = d.get("log_channel")
        if log_ch_id:
            lch = guild.get_channel(log_ch_id)
            if lch:
                buf.seek(0)
                await lch.send(
                    content=f"Transcript — Ticket `#{td.get('id', '????')}` Closed By {interaction.user.mention}",
                    file=discord.File(buf, filename=fname),
                )
    except discord.Forbidden:
        log.warning("Could Not DM Transcript To %s (DMs Disabled)", author)
    except Exception as e:
        log.error("Transcript DM Error: %s", e)

    await asyncio.sleep(10)
    subject = td.get("subject", "")
    await channel.delete(reason=f"Ticket Closed By {interaction.user}")
    d["tickets"].pop(interaction.channel_id, None)
    await _log_event(guild, "CLOSE", interaction.channel_id, interaction.user, subject)


async def _claim_ticket(interaction: discord.Interaction):
    d  = _gdata(interaction.guild_id)
    td = d["tickets"].get(interaction.channel_id)

    if not td:
        return await interaction.response.send_message("Ticket Data Not Found.", ephemeral=True)

    support_role_id = d.get("support_role")
    support_role    = interaction.guild.get_role(support_role_id) if support_role_id else None
    if support_role and support_role not in interaction.user.roles:  # type: ignore
        return await interaction.response.send_message(t("claim_staff_only"), ephemeral=True)

    if td.get("claimed_by"):
        claimer = interaction.guild.get_member(td["claimed_by"])
        return await interaction.response.send_message(
            f"{t('claim_already')} {claimer.mention if claimer else 'A Staff Member'}.",
            ephemeral=True,
        )

    td["claimed_by"] = interaction.user.id
    ts = int(datetime.now(timezone.utc).timestamp())

    await _v2_send(interaction.channel, [  # type: ignore
        _container(
            _text("## Ticket Claimed"),
            _separator(),
            _text(
                f"**{interaction.user.mention}** {t('claim_success_ch')}  —  <t:{ts}:R>\n"
                f"{t('claim_success_note')}"
            ),
        )
    ])
    await interaction.response.send_message(t("claim_ack"), ephemeral=True)


async def _build_transcript(
    channel: discord.TextChannel, td: dict, exported_by: str
) -> tuple[io.BytesIO, str]:
    lines = [
        "=" * 56,
        f"  Ticket Transcript  —  #{td.get('id', '????')}",
        "=" * 56,
        f"  Category   : {td.get('category',    'N/A')}",
        f"  Subject    : {td.get('subject',     'N/A')}",
        f"  Opened By  : {td.get('author_name', 'N/A')}",
        f"  Exported By: {exported_by}",
        f"  Timestamp  : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "=" * 56 + "\n",
    ]
    async for msg in channel.history(limit=500, oldest_first=True):
        ts_str = msg.created_at.strftime("%Y-%m-%d %H:%M")
        lines.append(f"[{ts_str}] {msg.author}: {msg.content or '[No Text Content]'}")
        for att in msg.attachments:
            lines.append(f"[{ts_str}] {msg.author}: [Attachment] {att.url}")
    buf   = io.BytesIO("\n".join(lines).encode("utf-8"))
    fname = f"ticket-{td.get('id', '0000')}-transcript.txt"
    return buf, fname


async def _log_event(
    guild: discord.Guild,
    event: str,
    channel_id: int,
    actor: discord.Member,
    subject: str,
):
    d   = _gdata(guild.id)
    lch = guild.get_channel(d["log_channel"]) if d.get("log_channel") else None
    if not lch:
        return

    ts    = int(datetime.now(timezone.utc).timestamp())
    tags  = {"CREATE": "Ticket Created", "CLOSE": "Ticket Closed", "CLAIM": "Ticket Claimed"}
    label = tags.get(event, event.title())

    await _v2_send(lch, [  # type: ignore
        _container(
            _text(f"## {label}"),
            _separator(),
            _section(
                f"**Channel:** <#{channel_id}>\n"
                f"**Actor:** {actor.mention}  (`{actor}` — ID: `{actor.id}`)\n"
                f"**Subject:** {subject[:100]}",
                actor.display_avatar.with_size(256).url,
            ),
            _separator(),
            _text(f"-# <t:{ts}:F>"),
        )
    ])


# ═══════════════════════════════════════════════════════════════════════════════
#  /ticket Commands
# ═══════════════════════════════════════════════════════════════════════════════

ticket_grp = app_commands.Group(
    name="ticket",
    description="Ticket Support System",
    default_permissions=discord.Permissions(0),
)


@ticket_grp.command(name="setup", description="Configure The Ticket System")
@app_commands.describe(
    category="Category Channel To Contain Ticket Channels",
    support_role="Role That Can View And Respond To Tickets",
    log_channel="Channel For Ticket Event Logs (Optional)",
)
@is_owner()
async def ticket_setup(
    interaction:  discord.Interaction,
    category:     discord.CategoryChannel,
    support_role: discord.Role,
    log_channel:  Optional[discord.TextChannel] = None,
):
    d = _gdata(interaction.guild_id)
    d["ticket_category"] = category.id
    d["support_role"]    = support_role.id
    d["log_channel"]     = log_channel.id if log_channel else None

    lc = log_channel.mention if log_channel else t("setup_not_set")
    await _v2_respond(interaction, [
        _container(
            _text(f"## {t('setup_ok')}"),
            _separator(),
            _text(
                f"**{t('setup_category')}:** {category.mention}\n"
                f"**{t('setup_role')}:** {support_role.mention}\n"
                f"**{t('setup_log')}:** {lc}"
            ),
        )
    ])


@ticket_grp.command(name="panel", description="Send The Ticket Panel To This Channel")
@is_owner()
async def ticket_panel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    d = _gdata(interaction.guild_id)

    if not d.get("ticket_category"):
        return await interaction.followup.send(t("err_no_setup"), ephemeral=True)

    channel: discord.TextChannel = interaction.channel  # type: ignore
    select_options = [
        {"label": _cat_label(k), "value": k, "description": _cat_desc(k)}
        for k in TICKET_CATEGORIES
    ]
    icon_url = (
        interaction.guild.icon.with_size(256).url
        if interaction.guild.icon
        else "https://cdn.discordapp.com/embed/avatars/0.png"
    )

    await _v2_send(channel, [
        _container(
            _section(
                f"## {t('panel_title')}\n"
                f"Need help? Open a ticket and our support team will assist you as soon as possible.",
                icon_url,
            ),
            _separator(),
            _text(
                "**Technical Support**\n"
                "-# Technical Issues, Bugs, Installation\n\n"
                "**Billing**\n"
                "-# Invoices, Transactions, Refunds\n\n"
                "**Report Violation**\n"
                "-# Report Users Or Content\n\n"
                "**General Inquiry**\n"
                "-# General Questions, Feedback\n\n"
                "**Partnership**\n"
                "-# Collaboration Proposals, Advertising"
            ),
            _separator(),
            _select(
                custom_id="ticket:category_select",
                placeholder=t("panel_placeholder"),
                options=select_options,
            ),
        )
    ])

    d["panel_channel"] = channel.id
    await interaction.followup.send(t("err_panel_sent"), ephemeral=True)


@ticket_grp.command(name="add", description="Add A User To This Ticket")
@app_commands.describe(user="Member To Add To This Ticket Channel")
@is_owner()
async def ticket_add(interaction: discord.Interaction, user: discord.Member):
    d = _gdata(interaction.guild_id)
    if interaction.channel_id not in d["tickets"]:
        return await interaction.response.send_message(t("err_not_ticket"), ephemeral=True)
    await interaction.channel.set_permissions(user, read_messages=True, send_messages=True)  # type: ignore
    await _v2_respond(interaction, [
        _container(
            _text("## User Added"),
            _separator(),
            _text(f"{user.mention} {t('user_added')}"),
        )
    ])


@ticket_grp.command(name="remove", description="Remove A User From This Ticket")
@app_commands.describe(user="Member To Remove From This Ticket Channel")
@is_owner()
async def ticket_remove(interaction: discord.Interaction, user: discord.Member):
    d = _gdata(interaction.guild_id)
    if interaction.channel_id not in d["tickets"]:
        return await interaction.response.send_message(t("err_not_ticket"), ephemeral=True)
    await interaction.channel.set_permissions(user, overwrite=None)  # type: ignore
    await _v2_respond(interaction, [
        _container(
            _text("## User Removed"),
            _separator(),
            _text(f"{user.mention} {t('user_removed')}"),
        )
    ])


@ticket_grp.command(name="list", description="View All Currently Open Tickets")
@is_owner()
async def ticket_list(interaction: discord.Interaction):
    d      = _gdata(interaction.guild_id)
    open_t = {cid: td for cid, td in d["tickets"].items() if td.get("open")}

    if not open_t:
        return await interaction.response.send_message(t("list_empty"), ephemeral=True)

    rows = []
    for ch_id, td in list(open_t.items())[:20]:
        claimed = f"<@{td['claimed_by']}>" if td.get("claimed_by") else t("list_unclaimed")
        rows.append(f"**#{td['id']}** <#{ch_id}>  —  {td['category']}  —  {claimed}")

    await _v2_respond(interaction, [
        _container(
            _text(f"## {t('list_title')}  ({len(open_t)})"),
            _separator(),
            _text("\n".join(rows)),
        )
    ])


@ticket_grp.command(name="delete", description="Force Delete A Ticket Channel")
@app_commands.describe(channel="The Ticket Channel To Delete")
@is_owner()
async def ticket_delete(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.defer(ephemeral=True, thinking=True)
    d  = _gdata(interaction.guild_id)
    td = d["tickets"].get(channel.id)

    if not td:
        return await interaction.followup.send(
            f"{channel.mention} Is Not A Tracked Ticket Channel.", ephemeral=True
        )

    guild: discord.Guild = interaction.guild  # type: ignore
    author = guild.get_member(td["author_id"])
    try:
        buf, fname = await _build_transcript(channel, td, str(interaction.user))
        dm_body = (
            f"**Ticket #{td.get('id', '????')} — {td.get('category', '')}**\n"
            f"Your Ticket In **{guild.name}** Was Deleted By {interaction.user}.\n"
            f"Transcript Attached Below."
        )
        if author:
            await author.send(content=dm_body, file=discord.File(buf, filename=fname))
        log_ch_id = d.get("log_channel")
        if log_ch_id:
            lch = guild.get_channel(log_ch_id)
            if lch:
                buf.seek(0)
                await lch.send(
                    content=f"Transcript — Ticket `#{td.get('id', '????')}` Deleted By {interaction.user.mention}",
                    file=discord.File(buf, filename=fname),
                )
    except discord.Forbidden:
        log.warning("Could Not DM Transcript To %s", author)
    except Exception as e:
        log.error("Transcript DM Error On Delete: %s", e)

    ts = int(datetime.now(timezone.utc).timestamp())
    await _v2_send(channel, [
        _container(
            _text("## Ticket Deleted"),
            _separator(),
            _text("Transcript Has Been Sent To The Ticket Author Via DM."),
            _separator(),
            _text(f"-# Deleted By {interaction.user.mention}  —  <t:{ts}:F>"),
        )
    ])
    await asyncio.sleep(3)
    await channel.delete(reason=f"Ticket Deleted By {interaction.user}")
    d["tickets"].pop(channel.id, None)
    await _log_event(guild, "CLOSE", channel.id, interaction.user, td.get("subject", ""))
    await interaction.followup.send(
        f"Ticket `#{td.get('id', '????')}` Has Been Deleted.", ephemeral=True
    )
    log.info("Ticket #%s Deleted By %s", td.get("id"), interaction.user)


bot.tree.add_command(ticket_grp)


# ═══════════════════════════════════════════════════════════════════════════════
#  /welcome Commands
# ═══════════════════════════════════════════════════════════════════════════════

welcome_grp = app_commands.Group(
    name="welcome",
    description="Welcome Message System",
    default_permissions=discord.Permissions(0),
)


@welcome_grp.command(name="setup", description="Configure The Welcome Message System")
@app_commands.describe(
    channel="Channel To Send Welcome Messages In",
    purchase="Purchase / Shop Channel To Link",
    rules="Rules Channel To Link",
    news="Announcements / News Channel To Link",
)
@is_owner()
async def welcome_setup(
    interaction: discord.Interaction,
    channel:     discord.TextChannel,
    purchase:    Optional[discord.TextChannel] = None,
    rules:       Optional[discord.TextChannel] = None,
    news:        Optional[discord.TextChannel] = None,
):
    d = _gdata(interaction.guild_id)
    d["welcome_channel"]  = channel.id
    d["welcome_purchase"] = purchase.id if purchase else None
    d["welcome_rules"]    = rules.id    if rules    else None
    d["welcome_news"]     = news.id     if news     else None

    def _ref(ch: Optional[discord.TextChannel]) -> str:
        return ch.mention if ch else "`Not Set`"

    await _v2_respond(interaction, [
        _container(
            _text("## Welcome System Configured"),
            _separator(),
            _text(
                f"**Welcome Channel:** {channel.mention}\n"
                f"**Purchase Channel:** {_ref(purchase)}\n"
                f"**Rules Channel:** {_ref(rules)}\n"
                f"**News Channel:** {_ref(news)}"
            ),
            _separator(),
            _text("Members Will Now Receive A Welcome Message When They Join."),
        )
    ])
    log.info("Welcome Setup By %s In '%s'", interaction.user, interaction.guild.name)


bot.tree.add_command(welcome_grp)


# ═══════════════════════════════════════════════════════════════════════════════
#  /verify Commands
# ═══════════════════════════════════════════════════════════════════════════════

verify_grp = app_commands.Group(
    name="verify",
    description="Member Verification System",
    default_permissions=discord.Permissions(0),
)


@verify_grp.command(name="setup", description="Set The Verification Channel")
@app_commands.describe(channel="Channel Where The Verify Panel Will Be Sent")
@is_owner()
async def verify_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    d = _gdata(interaction.guild_id)
    d["veri_channel"] = channel.id
    await _v2_respond(interaction, [
        _container(
            _text("## Verification Channel Set"),
            _separator(),
            _text(
                f"**Verify Channel:** {channel.mention}\n\n"
                "**Next Steps:**\n"
                "> Run `/verify enable` To Activate The System And Lock Channels.\n"
                "> Run `/verify panel` To Send The Verify Button."
            ),
        )
    ])


@verify_grp.command(
    name="enable",
    description="Enable Verification: Create Unverified Role & Lock All Channels Except Verify Channel",
)
@app_commands.describe(grant_role="Role To Grant Members After They Verify")
@is_owner()
async def verify_enable(interaction: discord.Interaction, grant_role: discord.Role):
    await interaction.response.defer(ephemeral=True, thinking=True)
    guild = interaction.guild  # type: ignore
    d     = _gdata(guild.id)

    if not d.get("veri_channel"):
        return await _v2_followup(interaction, [
            _container(
                _text("## Setup Required"),
                _separator(),
                _text("Please Run `/verify setup` First To Set The Verification Channel."),
            )
        ])

    veri_ch = guild.get_channel(d["veri_channel"])
    if not veri_ch:
        return await _v2_followup(interaction, [
            _container(
                _text("## Channel Not Found"),
                _separator(),
                _text("Verification Channel Not Found. Please Run `/verify setup` Again."),
            )
        ])

    d["veri_grant_id"] = grant_role.id

    unverified = discord.utils.get(guild.roles, name="Unverified")
    if not unverified:
        unverified = await guild.create_role(
            name="Unverified",
            color=discord.Color.from_str("#747F8D"),
            reason="Verification System: Auto-Created Unverified Role",
        )
    try:
        await guild.edit_role_positions(
            positions={unverified: 1},
            reason="Unverified Role Placed At Bottom Of Hierarchy",
        )
    except Exception as e:
        log.warning("Could Not Reposition Unverified Role: %s", e)

    d["veri_role_id"] = unverified.id
    d["veri_enabled"] = True

    locked  = 0
    skipped = 0
    for ch in guild.channels:
        if not isinstance(ch, (
            discord.TextChannel, discord.VoiceChannel,
            discord.ForumChannel, discord.StageChannel,
        )):
            continue
        try:
            if ch.id == veri_ch.id:
                await ch.set_permissions(
                    unverified, view_channel=True, send_messages=False,
                    reason="Verify Channel — Unverified Read-Only Access",
                )
            else:
                await ch.set_permissions(
                    unverified, view_channel=False,
                    reason="Verification System: Block Unverified Members",
                )
            locked += 1
        except Exception as e:
            log.warning("Could Not Set Perms For #%s: %s", ch.name, e)
            skipped += 1

    await _v2_followup(interaction, [
        _container(
            _text("## Verification Enabled"),
            _separator(),
            _text(
                f"**Unverified Role:** {unverified.mention}  *(Placed At Bottom Of Role List)*\n"
                f"**Verified Role:** {grant_role.mention}\n"
                f"**Verify Channel:** {veri_ch.mention}\n"
                f"**Channels Locked:** {locked}  |  **Skipped:** {skipped}"
            ),
            _separator(),
            _text(
                "**How It Works:**\n"
                "> New Member Joins  →  Auto-Assigned **Unverified** Role\n"
                "> Unverified Members  →  Can Only See The Verify Channel\n"
                "> Member Clicks Verify  →  Role Assigned & Unverified Removed\n\n"
                f"Run `/verify panel` To Send The Verify Button To {veri_ch.mention}."
            ),
        )
    ])
    log.info("Verification Enabled In '%s' By %s — Grant: %s", guild.name, interaction.user, grant_role.name)


@verify_grp.command(name="panel", description="Send The Verification Panel To The Verify Channel")
@is_owner()
async def verify_panel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild  # type: ignore
    d     = _gdata(guild.id)

    if not d.get("veri_enabled"):
        return await _v2_followup(interaction, [
            _container(
                _text("## Not Enabled"),
                _separator(),
                _text("Verification System Is Not Enabled. Run `/verify enable` First."),
            )
        ])

    veri_ch = guild.get_channel(d.get("veri_channel") or 0)
    if not veri_ch:
        return await _v2_followup(interaction, [
            _container(
                _text("## Channel Not Found"),
                _separator(),
                _text("Verification Channel Not Found. Run `/verify setup` First."),
            )
        ])

    grant_role = guild.get_role(d.get("veri_grant_id") or 0)
    icon_url   = (
        guild.icon.with_size(256).url if guild.icon
        else "https://cdn.discordapp.com/embed/avatars/0.png"
    )
    role_line = f"**Role Granted After Verification:** {grant_role.mention}\n" if grant_role else ""

    await _v2_send(veri_ch, [  # type: ignore
        _container(
            _section(
                f"## Verification Required\n"
                f"Welcome To **{guild.name}**!\n"
                f"To Gain Full Access To The Server, You Must First Verify Yourself.",
                icon_url,
            ),
            _separator(),
            _text(
                "**How To Verify:**\n"
                "> Step 1  —  Click The **Verify** Button Below\n"
                "> Step 2  —  You Will Receive Full Access Instantly\n\n"
                + role_line
            ),
            _separator(),
            _action_row(_button("Verify", "verify:btn", style=2)),
        )
    ])

    await _v2_followup(interaction, [
        _container(
            _text("## Verify Panel Sent"),
            _separator(),
            _text(f"The Verification Panel Has Been Sent To {veri_ch.mention}."),
        )
    ])


@verify_grp.command(name="disable", description="Disable Verification & Remove All Channel Locks")
@is_owner()
async def verify_disable(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=True)
    guild = interaction.guild  # type: ignore
    d     = _gdata(guild.id)
    d["veri_enabled"] = False

    unverified = guild.get_role(d.get("veri_role_id") or 0)
    removed    = 0
    if unverified:
        for ch in guild.channels:
            if isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel, discord.StageChannel)):
                try:
                    await ch.set_permissions(unverified, overwrite=None, reason="Verification System Disabled")
                    removed += 1
                except Exception:
                    pass

    await _v2_followup(interaction, [
        _container(
            _text("## Verification Disabled"),
            _separator(),
            _text(
                f"Removed Locks From **{removed}** Channels.\n"
                "The Unverified Role Is Still Present — Delete It Manually If No Longer Needed."
            ),
        )
    ])
    log.info("Verification Disabled In '%s' By %s", guild.name, interaction.user)


@verify_grp.command(
    name="update",
    description="Re-Apply Channel Locks To All Channels (Run After Adding New Channels)",
)
@is_owner()
async def verify_update(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=True)
    guild = interaction.guild  # type: ignore
    d     = _gdata(guild.id)

    if not d.get("veri_enabled"):
        return await _v2_followup(interaction, [_container(_text("## Not Enabled"), _separator(), _text("Run `/verify enable` First."))])

    unverified = guild.get_role(d.get("veri_role_id") or 0)
    if not unverified:
        return await _v2_followup(interaction, [_container(_text("## Unverified Role Not Found"), _separator(), _text("The Unverified Role Was Deleted. Please Run `/verify enable` Again."))])

    veri_ch = guild.get_channel(d.get("veri_channel") or 0)
    if not veri_ch:
        return await _v2_followup(interaction, [_container(_text("## Verify Channel Not Found"), _separator(), _text("The Verify Channel Was Deleted. Please Run `/verify setup` Again."))])

    updated = 0
    skipped = 0
    for ch in guild.channels:
        if not isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel, discord.StageChannel)):
            continue
        try:
            if ch.id == veri_ch.id:
                await ch.set_permissions(unverified, view_channel=True, send_messages=False, reason="Verify Update")
            else:
                await ch.set_permissions(unverified, view_channel=False, reason="Verify Update")
            updated += 1
        except Exception as e:
            log.warning("Could Not Update Perms For #%s: %s", ch.name, e)
            skipped += 1

    await _v2_followup(interaction, [
        _container(
            _text("## Verification Updated"),
            _separator(),
            _text(
                f"**Unverified Role:** {unverified.mention}\n"
                f"**Verify Channel:** {veri_ch.mention}\n"
                f"**Channels Updated:** {updated}  |  **Skipped:** {skipped}"
            ),
            _separator(),
            _text("All Channels Have Been Re-Locked For The Unverified Role."),
        )
    ])


bot.tree.add_command(verify_grp)


# ═══════════════════════════════════════════════════════════════════════════════
#  /payment Commands
# ═══════════════════════════════════════════════════════════════════════════════

payment_grp = app_commands.Group(
    name="payment",
    description="VietQR Payment System",
    default_permissions=discord.Permissions(0),
)


@payment_grp.command(name="setup", description="Configure The VietQR AutoBank Payment System")
@app_commands.describe(
    bank_id="VietQR Bank Code (e.g. MB, VCB, TCB, VPB, TPB, ACB)",
    account_no="Bank Account Number",
    account_name="Account Holder Name (Shown On QR)",
    casso_key="Casso API Key For Auto-Confirm (Get From casso.vn)",
    log_channel="Channel To Log Confirmed Payments",
    confirm_role="Role To Ping On Payment Confirmed (Optional)",
    timeout="Payment Expiry In Minutes (Default: 10)",
)
@is_owner()
async def payment_setup(
    interaction:   discord.Interaction,
    bank_id:       str,
    account_no:    str,
    account_name:  str,
    casso_key:     str,
    log_channel:   discord.TextChannel,
    confirm_role:  Optional[discord.Role] = None,
    timeout:       int = 10,
):
    d = _gdata(interaction.guild_id)
    bank_id_upper = bank_id.strip().upper()

    d["pay_bank_id"]      = bank_id_upper
    d["pay_account_no"]   = account_no.strip()
    d["pay_account_name"] = account_name.strip()
    d["pay_casso_key"]    = casso_key.strip()
    d["pay_log_channel"]  = log_channel.id
    d["pay_confirm_role"] = confirm_role.id if confirm_role else None
    d["pay_timeout"]      = max(1, timeout) * 60

    await _v2_respond(interaction, [
        _container(
            _text("## ✅ Payment System Configured"),
            _separator(),
            _text(
                f"**Bank:** `{bank_id_upper}`\n"
                f"**Account No:** `{account_no}`\n"
                f"**Account Name:** `{account_name}`\n"
                f"**Log Channel:** {log_channel.mention}\n"
                f"**Ping Role:** {confirm_role.mention if confirm_role else '`None`'}\n"
                f"**Casso API Key:** `{'*' * min(len(casso_key), 8)}...` *(Hidden)*\n"
                f"**Payment Timeout:** `{timeout} Minutes`\n\n"
                f"Auto-Confirm: Bot Will Poll Casso Every 15s And Confirm Matching Payments.\n"
                f"Run `/payment create` To Generate A QR Code."
            ),
        )
    ])
    log.info("Payment Setup By %s In '%s' — Bank: %s Account: %s", interaction.user, interaction.guild.name, bank_id_upper, account_no)


@payment_grp.command(name="create", description="Generate A VietQR Payment QR Code")
@app_commands.describe(
    amount="Amount In VND (e.g. 50000)",
    description="Payment Description / Note",
    user="Who Is Paying (Optional, Defaults To You)",
)
async def payment_create(
    interaction: discord.Interaction,
    amount:      int,
    description: str,
    user:        Optional[discord.Member] = None,
):
    await interaction.response.defer(ephemeral=False, thinking=True)
    d = _gdata(interaction.guild_id)

    if not d.get("pay_bank_id") or not d.get("pay_account_no"):
        return await interaction.followup.send(
            "Payment System Not Configured. Ask An Admin To Run `/payment setup` First.",
            ephemeral=True,
        )

    if amount < 1000:
        return await interaction.followup.send(
            "Minimum Amount Is `1,000 VND`.", ephemeral=True
        )

    payer      = user or interaction.user
    bank_id    = d["pay_bank_id"]
    account_no = d["pay_account_no"]
    acc_name   = d["pay_account_name"]
    ref        = _gen_ref(interaction.guild_id, payer.id)
    # Ensure unique ref
    while ref in d["payments"]:
        ref = _gen_ref(interaction.guild_id, payer.id)

    qr_url = _vietqr_url(bank_id, account_no, acc_name, amount, ref)
    ts     = int(time.time())
    expire = ts + d.get("pay_timeout", 600)

    # Send the QR message first (we need the message ID)
    channel: discord.TextChannel = interaction.channel  # type: ignore
    msg_data = await _v2_send(channel, [
        _container(
            _text(f"## 🏦 Payment Request"),
            _separator(),
            _section(
                f"**Payer:** {payer.mention}\n"
                f"**Amount:** `{amount:,} VND`\n"
                f"**Bank:** `{bank_id}` — `{account_no}`\n"
                f"**Account Name:** `{acc_name}`\n"
                f"**Description / Nội dung CK:** `{ref}`\n"
                f"**Note:** {description}\n\n"
                f"⏰ Expires <t:{expire}:R>",
                qr_url,
            ),
            _separator(),
            _text(
                "**Hướng dẫn / Instructions:**\n"
                "> 1️⃣  Mở app ngân hàng / Open banking app\n"
                "> 2️⃣  Quét QR bên phải / Scan QR on the right\n"
                f"> 3️⃣  Nhập đúng nội dung: **`{ref}`** — bắt buộc!\n"
                "> 4️⃣  Bot tự xác nhận trong vài giây / Bot auto-confirms shortly\n\n"
                "-# Do not change the transfer description or payment will not be detected."
            ),
            _separator(),
            _action_row(_button("❌ Cancel Payment", f"payment:cancel:{ref}", style=4)),
        )
    ])

    msg_id = int(msg_data.get("id", 0))
    _payment_create(interaction.guild_id, payer.id, amount, description, channel.id, msg_id)

    # Delete the thinking followup (it was already sent via _v2_send)
    try:
        await interaction.delete_original_response()
    except Exception:
        pass

    log.info(
        "Payment %s created — %s VND — Payer: %s — Bank: %s %s",
        ref, amount, payer, bank_id, account_no,
    )


@payment_grp.command(name="check", description="Manually Check A Payment Status By Reference Code")
@app_commands.describe(ref="Payment Reference Code (e.g. PAYAB1234)")
async def payment_check(interaction: discord.Interaction, ref: str):
    d = _gdata(interaction.guild_id)
    p = d["payments"].get(ref.upper())
    if not p:
        return await interaction.response.send_message(
            f"Payment `{ref}` Not Found.", ephemeral=True
        )

    status_icon = {"pending": "⏳", "confirmed": "✅", "expired": "⏰", "cancelled": "❌"}.get(p["status"], "❓")
    payer = interaction.guild.get_member(p["user_id"])
    ts    = int(p["created_at"])

    await _v2_respond(interaction, [
        _container(
            _text(f"## {status_icon} Payment Status"),
            _separator(),
            _text(
                f"**Reference:** `{ref}`\n"
                f"**Status:** {status_icon} {p['status'].upper()}\n"
                f"**Amount:** `{p['amount']:,} VND`\n"
                f"**Payer:** {payer.mention if payer else 'ID: ' + str(p['user_id'])}\n"
                f"**Description:** {p['description']}\n"
                f"**Created:** <t:{ts}:F>\n"
                + (f"**TX ID:** `{p['confirmed_by_tx']}`" if p.get("confirmed_by_tx") else "")
            ),
        )
    ])


@payment_grp.command(name="confirm", description="Manually Confirm A Payment (Owner Only)")
@app_commands.describe(ref="Payment Reference Code To Confirm")
@is_owner()
async def payment_confirm(interaction: discord.Interaction, ref: str):
    d = _gdata(interaction.guild_id)
    p = d["payments"].get(ref.upper())
    if not p:
        return await interaction.response.send_message(f"Payment `{ref}` Not Found.", ephemeral=True)
    if p["status"] != "pending":
        return await interaction.response.send_message(
            f"Payment Is Already **{p['status'].upper()}**.", ephemeral=True
        )
    _payment_confirm(interaction.guild_id, ref.upper(), "MANUAL")
    await _notify_payment_confirmed(interaction.guild_id, ref.upper())
    await interaction.response.send_message(f"Payment `{ref}` Confirmed Manually.", ephemeral=True)


@payment_grp.command(name="cancel", description="Cancel A Pending Payment (Owner Only)")
@app_commands.describe(ref="Payment Reference Code To Cancel")
@is_owner()
async def payment_cancel(interaction: discord.Interaction, ref: str):
    d = _gdata(interaction.guild_id)
    p = d["payments"].get(ref.upper())
    if not p:
        return await interaction.response.send_message(f"Payment `{ref}` Not Found.", ephemeral=True)
    if p["status"] != "pending":
        return await interaction.response.send_message(
            f"Payment Is Already **{p['status'].upper()}**.", ephemeral=True
        )
    _payment_expire(interaction.guild_id, ref.upper())
    await _notify_payment_expired(interaction.guild_id, ref.upper())
    await interaction.response.send_message(f"Payment `{ref}` Cancelled.", ephemeral=True)


@payment_grp.command(name="list", description="List All Payments (Owner Only)")
@app_commands.describe(status="Filter By Status")
@app_commands.choices(status=[
    app_commands.Choice(name="All",       value="all"),
    app_commands.Choice(name="Pending",   value="pending"),
    app_commands.Choice(name="Confirmed", value="confirmed"),
    app_commands.Choice(name="Expired",   value="expired"),
    app_commands.Choice(name="Cancelled", value="cancelled"),
])
@is_owner()
async def payment_list(interaction: discord.Interaction, status: str = "all"):
    d        = _gdata(interaction.guild_id)
    payments = d["payments"]

    filtered = {
        ref: p for ref, p in payments.items()
        if status == "all" or p["status"] == status
    }

    if not filtered:
        return await interaction.response.send_message(
            f"No Payments Found With Status: `{status}`.", ephemeral=True
        )

    icon_map = {"pending": "⏳", "confirmed": "✅", "expired": "⏰", "cancelled": "❌"}
    rows     = []
    for ref, p in list(filtered.items())[-20:]:
        icon   = icon_map.get(p["status"], "❓")
        payer  = interaction.guild.get_member(p["user_id"])
        p_name = payer.display_name if payer else f"ID:{p['user_id']}"
        rows.append(f"{icon} `{ref}` — `{p['amount']:,}₫` — {p_name} — **{p['status']}**")

    total     = len(filtered)
    confirmed = sum(1 for p in filtered.values() if p["status"] == "confirmed")
    total_vnd = sum(p["amount"] for p in filtered.values() if p["status"] == "confirmed")

    await _v2_respond(interaction, [
        _container(
            _text(f"## 💳 Payment List — `{status.upper()}`"),
            _separator(),
            _text(
                f"**Total:** {total}  •  **Confirmed:** {confirmed}  •  **Revenue:** `{total_vnd:,} VND`\n\n"
                + "\n".join(rows)
            ),
        )
    ])


@payment_grp.command(name="info", description="Show Current Payment System Configuration")
@is_owner()
async def payment_info(interaction: discord.Interaction):
    d = _gdata(interaction.guild_id)
    if not d.get("pay_bank_id"):
        return await interaction.response.send_message(
            "Payment System Not Configured. Run `/payment setup` First.", ephemeral=True
        )

    log_ch    = interaction.guild.get_channel(d.get("pay_log_channel") or 0)
    conf_role = interaction.guild.get_role(d.get("pay_confirm_role") or 0)
    timeout_m = d.get("pay_timeout", 600) // 60

    pending   = sum(1 for p in d["payments"].values() if p["status"] == "pending")
    confirmed = sum(1 for p in d["payments"].values() if p["status"] == "confirmed")
    revenue   = sum(p["amount"] for p in d["payments"].values() if p["status"] == "confirmed")

    await _v2_respond(interaction, [
        _container(
            _text("## 🏦 Payment System Info"),
            _separator(),
            _text(
                f"**Bank:** `{d['pay_bank_id']}`\n"
                f"**Account No:** `{d['pay_account_no']}`\n"
                f"**Account Name:** `{d['pay_account_name']}`\n"
                f"**Log Channel:** {log_ch.mention if log_ch else '`Not Set`'}\n"
                f"**Ping Role:** {conf_role.mention if conf_role else '`None`'}\n"
                f"**Timeout:** `{timeout_m} Minutes`\n"
                f"**Casso Key:** `{'Configured ✅' if d.get('pay_casso_key') else 'Not Set ❌'}`"
            ),
            _separator(),
            _text(
                f"**Stats:**\n"
                f"> Pending: `{pending}`\n"
                f"> Confirmed: `{confirmed}`\n"
                f"> Total Revenue: `{revenue:,} VND`"
            ),
        )
    ])


bot.tree.add_command(payment_grp)


# ═══════════════════════════════════════════════════════════════════════════════
#  /owner Commands
# ═══════════════════════════════════════════════════════════════════════════════

owner_grp = app_commands.Group(
    name="owner",
    description="Owner Only Commands",
    default_permissions=discord.Permissions(0),
)


@owner_grp.command(name="status", description="View Full Bot Statistics")
@is_owner()
async def owner_status(interaction: discord.Interaction):
    total_open = sum(
        1 for d in _STORE.values()
        for td in d["tickets"].values() if td.get("open")
    )
    total_all    = sum(len(d["tickets"]) for d in _STORE.values())
    total_pay    = sum(len(d.get("payments", {})) for d in _STORE.values())
    total_revenue = sum(
        p["amount"] for d in _STORE.values()
        for p in d.get("payments", {}).values() if p["status"] == "confirmed"
    )
    ts = int(datetime.now(timezone.utc).timestamp())

    await _v2_respond(interaction, [
        _container(
            _text("## Bot Statistics"),
            _separator(),
            _text(
                f"**Guilds:** {len(bot.guilds)}\n"
                f"**Open Tickets:** {total_open}\n"
                f"**Total Tickets:** {total_all}\n"
                f"**Total Payments:** {total_pay}\n"
                f"**Total Revenue:** `{total_revenue:,} VND`\n"
                f"**Latency:** {bot.latency * 1000:.1f}ms\n"
                f"**Owner ID:** `{OWNER_ID}`"
            ),
            _separator(),
            _text(f"-# <t:{ts}:F>"),
        )
    ])


@owner_grp.command(name="guilds", description="List All Servers Using This Bot")
@is_owner()
async def owner_guilds(interaction: discord.Interaction):
    lines = [
        f"`{g.id}`  **{g.name}**  —  {g.member_count} Members"
        for g in bot.guilds[:20]
    ]
    ts = int(datetime.now(timezone.utc).timestamp())
    await _v2_respond(interaction, [
        _container(
            _text(f"## Guilds  ({len(bot.guilds)})"),
            _separator(),
            _text("\n".join(lines) or "None"),
            _separator(),
            _text(f"-# <t:{ts}:F>"),
        )
    ])


@owner_grp.command(name="broadcast", description="Send An Announcement To All Panel Channels")
@app_commands.describe(message="Announcement Content")
@is_owner()
async def owner_broadcast(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True, thinking=True)
    sent, failed = 0, 0
    ts = int(datetime.now(timezone.utc).timestamp())
    for guild in bot.guilds:
        d = _STORE.get(guild.id)
        if not d or not d.get("panel_channel"):
            continue
        ch = guild.get_channel(d["panel_channel"])
        if not ch:
            continue
        try:
            await _v2_send(ch, [  # type: ignore
                _container(
                    _text("## Announcement"),
                    _separator(),
                    _text(message),
                    _separator(),
                    _text(f"-# <t:{ts}:F>"),
                )
            ])
            sent += 1
        except Exception as e:
            log.warning("Broadcast Failed For %s: %s", guild.name, e)
            failed += 1
    await interaction.followup.send(
        f"Sent To **{sent}** Servers. Failed: **{failed}**", ephemeral=True
    )


@owner_grp.command(name="reset_guild", description="Delete All Data For A Server")
@app_commands.describe(guild_id="The Server ID To Reset")
@is_owner()
async def owner_reset_guild(interaction: discord.Interaction, guild_id: str):
    gid = int(guild_id)
    if gid in _STORE:
        _STORE.pop(gid)
        await interaction.response.send_message(
            f"Data For Guild `{guild_id}` Has Been Reset.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"No Data Found For Guild `{guild_id}`.", ephemeral=True
        )


@owner_grp.command(name="close_all", description="Force Close All Open Tickets In This Server")
@is_owner()
async def owner_close_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True, thinking=True)
    guild: discord.Guild = interaction.guild  # type: ignore
    d            = _gdata(guild.id)
    open_tickets = {cid: td for cid, td in d["tickets"].items() if td.get("open")}
    if not open_tickets:
        return await interaction.followup.send("No Open Tickets Found.", ephemeral=True)
    closed = 0
    for ch_id in list(open_tickets.keys()):
        ch = guild.get_channel(ch_id)
        if ch:
            try:
                await ch.delete(reason="Owner: Force Close All")
            except Exception:
                pass
        d["tickets"].pop(ch_id, None)
        closed += 1
    await interaction.followup.send(f"Closed **{closed}** Tickets.", ephemeral=True)


bot.tree.add_command(owner_grp)


# ═══════════════════════════════════════════════════════════════════════════════
#  Error Handler
# ═══════════════════════════════════════════════════════════════════════════════

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.MissingPermissions):
        msg = "You Do Not Have Permission To Use This Command."
    elif isinstance(error, app_commands.CheckFailure):
        msg = "Access Denied. You Are Not Authorized To Use This Command."
    else:
        msg = "An Error Occurred. Please Try Again."
    try:
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
#  Prefix Commands
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="sync")
async def cmd_sync(ctx: commands.Context):
    if ctx.author.id != OWNER_ID:
        return await ctx.reply("Access Denied. Only The Bot Owner Can Use This Command.")
    msg    = await ctx.reply("Syncing Commands...")
    synced = await bot.tree.sync()
    await msg.edit(content=f"Synced **{len(synced)}** Slash Commands Successfully.")
    log.info("!sync Called By %s — %d Commands Synced", ctx.author, len(synced))


# ═══════════════════════════════════════════════════════════════════════════════
#  Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info("Starting Bot  |  Owner ID: %d", OWNER_ID)
    bot.run(TOKEN, log_handler=None)
