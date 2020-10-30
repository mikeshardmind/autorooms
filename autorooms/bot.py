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

import discord
from discord.ext import commands
from discord.voice_client import VoiceClient

VoiceClient.warn_nacl = False


class ARBot(commands.AutoShardedBot):
    """
    Autorooms bot
    """

    def __init__(self, *args, **kwargs):
        kwargs.update(
            command_prefix=commands.when_mentioned,
            acitivty=discord.Game(name='https://github.com/mikeshardmind/autorooms'),
            status=discord.Status.online,
            chunk_guilds_at_startup=False,
            max_messages=None,
            intents=discord.Intents(guilds=True, voice_states=True),
        )
        super().__init__(*args, **kwargs)

    async def on_connect(self):
        await self.wait_until_ready()
        self.load_extension("autorooms.extensions.autorooms")
        data = await self.application_info()
        perms = discord.Permissions(permissions=17825808)
        self.invite_link = discord.utils.oauth_url(data.id, permissions=perms)
        print(f"Use this link to add the bot to your server: {self.invite_link}")
