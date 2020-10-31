#   Copyright 2017-2020 Michael Hall
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

import logging
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord.voice_client import VoiceClient

VoiceClient.warn_nacl = False

AUTOROOM_STR = "\N{HOURGLASS}"
CLONEDROOM_STR = "\N{BLACK UNIVERSAL RECYCLING SYMBOL}"


class ARBot(commands.AutoShardedBot):
    """
    Autorooms bot
    """

    def __init__(self, *args, **kwargs):
        kwargs.update(
            command_prefix=commands.when_mentioned,
            acitivty=discord.Game(name="https://github.com/mikeshardmind/autorooms"),
            status=discord.Status.online,
            chunk_guilds_at_startup=False,
            max_messages=None,
            intents=discord.Intents(guilds=True, voice_states=True),
        )
        super().__init__(*args, **kwargs)

    async def on_connect(self):
        await self.wait_until_ready()
        data = await self.application_info()
        perms = discord.Permissions(permissions=17825808)
        self.invite_link = discord.utils.oauth_url(data.id, permissions=perms)
        print(f"Use this link to add the bot to your server: {self.invite_link}")

    async def on_voice_state_update(self, member, v_before, v_after):

        if v_before.channel == v_after.channel:
            return

        guild = v_before.channel.guild if v_before.channel else None
        if guild and guild.me.guild_permissions.value & 17825808 == 17825808:
            for channel in guild.voice_channels:
                if (
                    channel.name.startswith(CLONEDROOM_STR)
                    and not channel.members
                    and channel.created_at + timedelta(seconds=3) < datetime.utcnow()
                ):
                    await channel.delete(reason="Empty Autoroom")

        if v_after.channel is not None:
            guild = v_after.channel.guild
            if guild and guild.me.guild_permissions.value & 17825808 == 17825808:
                if v_after.channel.name.startswith(AUTOROOM_STR):
                    await self.make_auto_room(member, v_after.channel)

    async def make_auto_room(self, member, chan):

        category = chan.category

        overwrites = chan.overwrites

        if chan.guild.me in overwrites:
            overwrites[chan.guild.me].update(
                manage_channels=True, manage_roles=True, connect=True
            )
        else:
            overwrites.update(
                {
                    chan.guild.me: discord.PermissionOverwrite(
                        manage_channels=True, manage_roles=True, connect=True
                    )
                }
            )

        chan_name = f"{CLONEDROOM_STR}: {chan.name}".replace(AUTOROOM_STR, "")

        z = await chan.guild.create_voice_channel(
            chan_name,
            category=category,
            overwrites=overwrites,
            bitrate=chan.bitrate,
            user_limit=chan.user_limit,
        )
        await member.move_to(z, reason="autoroom")
