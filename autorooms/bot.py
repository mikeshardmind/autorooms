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

from datetime import timedelta

import discord
from discord.ext import commands
from discord.utils import utcnow
from discord.voice_client import VoiceClient

VoiceClient.warn_nacl = False

AUTOROOM_STR = "\N{HOURGLASS}"
CLONEDROOM_STR = "\N{BLACK UNIVERSAL RECYCLING SYMBOL}"


class ARBot(commands.AutoShardedClient):
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
                if v_after.channel.name.startswith(AUTOROOM_STR):
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
