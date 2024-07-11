#   Copyright 2017-present Michael Hall
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import argparse
import getpass
import os
from datetime import timedelta

import discord
import keyring
from discord.utils import utcnow

try:
    import uvloop  # type: ignore
except ImportError:
    uvloop = None


__version__ = "5.0.3"

AUTOROOM_STR = "\N{HOURGLASS}"
CLONEDROOM_STR = "\N{BLACK UNIVERSAL RECYCLING SYMBOL}"


class ARBot(discord.AutoShardedClient):
    """
    Autorooms bot
    """

    def __init__(self):
        super().__init__(
            max_messages=None,
            acitivty=discord.Game(name="https://github.com/mikeshardmind/autorooms"),
            status=discord.Status.online,
            chunk_guilds_at_startup=False,
            intents=discord.Intents(guilds=True, voice_states=True),
        )

    async def on_connect(self):
        await self.wait_until_ready()
        data = await self.application_info()
        perms = discord.Permissions(permissions=17825808)
        self.invite_link = discord.utils.oauth_url(data.id, permissions=perms)

    async def on_voice_state_update(
        self,
        member: discord.Member,
        v_before: discord.VoiceState,
        v_after: discord.VoiceState,
    ):

        if v_before.channel and v_after.channel and v_before.channel == v_after.channel:
            return

        guild = v_before.channel.guild if v_before.channel else None
        if guild and guild.me.guild_permissions.value & 17825808 == 17825808:
            for channel in guild.voice_channels:
                if (
                    channel.name.startswith(CLONEDROOM_STR)
                    and not channel.members
                    and channel.created_at + timedelta(seconds=3) < utcnow()
                ):
                    await channel.delete(reason="Empty Autoroom")

        if v_after.channel is not None:
            guild = v_after.channel.guild
            if guild and guild.me.guild_permissions.value & 17825808 == 17825808:
                if v_after.channel.name.startswith(AUTOROOM_STR) and isinstance(v_after.channel, discord.VoiceChannel):
                    await self.make_auto_room(member, v_after.channel)

    async def make_auto_room(self, member: discord.Member, chan: discord.VoiceChannel):

        chan_name = f"{CLONEDROOM_STR}: {chan.name}".replace(AUTOROOM_STR, "")

        overwrites = chan.overwrites.copy()
        perm_kwargs = {"manage_channels": True, "manage_roles": True, "connect": True}

        for who in (chan.guild.me, member):
            if who in overwrites:
                overwrites[who].update(**perm_kwargs)
            elif (who_obj := discord.Object(who.id, type=discord.Member)) in overwrites:
                overwrites[who_obj].update(**perm_kwargs)
            else:
                overwrites[who] = discord.PermissionOverwrite(**perm_kwargs)

        z = await chan.guild.create_voice_channel(
            chan_name,
            category=chan.category,
            bitrate=chan.bitrate,
            user_limit=chan.user_limit,
            overwrites=overwrites,
        )
        await member.move_to(z, reason="autoroom")


def _get_keyring_creds() -> str | None:
    user = getpass.getuser()
    return keyring.get_password("discord-autorooms-token", user)


def _set_keyring_creds(token: str, /):
    user = getpass.getuser()
    keyring.set_password("discord-autorooms-token", user, token)


def _get_token() -> str:
    # TODO: alternative token stores: systemdcreds, etc
    token = os.getenv("AUTOROOMTOKEN") or _get_keyring_creds()
    if not token:
        msg = "NO TOKEN? (Use Environment `AUTOROOMTOKEN` or launch with `--setup` to go through interactive setup)"
        raise RuntimeError(msg) from None
    return token


def run_bot() -> None:
    if uvloop is not None:
        uvloop.install()  # type: ignore
    bot = ARBot()
    token = _get_token()
    bot.run(token)


def run_setup() -> None:
    prompt = (
        "Paste the discord token you'd like to use for this bot here (won't be visible) then press enter. "
        "This will be stored in the system keyring for later use >"
    )
    token = getpass.getpass(prompt)
    if not token:
        msg = "Not storing empty token"
        raise RuntimeError(msg)
    _set_keyring_creds(token)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A minimal configuration discord bot for automatic voice channels")
    excl = parser.add_mutually_exclusive_group()
    excl.add_argument("--setup", action="store_true", default=False, help="Run interactive setup.", dest="isetup")
    excl.add_argument(
        "--set-token-to",
        default=None,
        dest="token",
        help="Provide a token directly to be stored in the system keyring.",
    )
    args = parser.parse_args()
    if args.isetup:
        run_setup()
    elif args.token:
        _set_keyring_creds(args.token)
    else:
        run_bot()
