from dataclasses import dataclass
import os
from typing import Mapping, Optional
import tempfile
import subprocess
import datetime

import discord

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
PREFIX = os.getenv("DISCORD_ESPEAK_TOKEN", "tts")
TIMEOUT = int(os.getenv("DISCORD_ESPEAK_TIMEOUT", "300"))
PROG = os.getenv("DISCORD_ESPEAK_PROG", "espeak-ng")

voices = subprocess.run([PROG, "--voices"], capture_output=True).stdout.decode("utf-8")

async def ls(p):
    subprocess.run(["ls", "-al", p])

@dataclass
class TTSUserSettings:
    enabled: bool
    voice: str
    speed: int
    last_seen: datetime.datetime

class TTSClient(discord.Client):
    tts_users : Mapping[str, TTSUserSettings] = dict()
    voice_client: Optional[discord.VoiceClient] = None

    async def on_ready(self):
        print('Logged on as', self.user)

    def get_tts_user(self, user: str) -> TTSUserSettings:
        now = datetime.datetime.now()
        if user not in self.tts_users:
            self.tts_users[user] = TTSUserSettings(False, "en-us", 175, now)
        user = self.tts_users[user]
        timeout = datetime.timedelta(seconds=TIMEOUT)
        if user.last_seen + timeout < now:
            user.enabled = False
        user.last_seen = now
        return user

    async def on_message(self, message):
        user = self.get_tts_user(message.author)

        if message.author == self.user:
            return

        elif message.content == f"{PREFIX} enable":
            user.enabled = True
            await message.channel.send(
                f"TTS enabled for {message.author}. " +
                f"It will be automatically disabled after {TIMEOUT} seconds of inactivity.")

        elif message.content == f"{PREFIX} disable":
            user.enabled = False
            await message.channel.send(f"TTS disabled for {message.author}")

        elif message.content == f"{PREFIX} voices":
            lines = []
            for voice in voices.splitlines():
                lines.append(voice)
                if len(lines) >= 10:
                    await message.channel.send("```\n" + "\n".join(lines) + "```")
                    lines = []

        elif message.content == f"{PREFIX} disconnect":
            if self.voice_client is not None:
                await self.voice_client.disconnect()
                self.voice_client = None

        elif message.content.startswith(f"{PREFIX} voice "):
            user.voice = message.content.split(" ")[2]
            await message.channel.send(f"TTS voice set to {user.voice} for {message.author}")

        elif message.content.startswith(f"{PREFIX} speed "):
            try:
                speed = int(message.content.split(" ")[2])
                user.speed = speed
                await message.channel.send(f"TTS voice speed set to {user.speed} wpm for {message.author}")
            except ValueError:
                await message.channel.send(f"Invalid speed")

        elif user.enabled:
            with tempfile.TemporaryDirectory() as d:
                voice_txt = os.path.join(d, "voice.txt")
                with open(voice_txt, "w") as f:
                    f.write(message.content)
                voice_wav = os.path.join(d, "voice.wav")
                result = subprocess.run([PROG, "-v", user.voice, "-s", str(user.speed), "-w", voice_wav, "-f", voice_txt], capture_output=True)
                if result.returncode != 0:
                    await message.channel.send(result.stderr.decode("utf-8"))
                else:
                    if self.voice_client is None:
                        channel = message.author.voice.channel
                        if channel is not None:
                            self.voice_client = await channel.connect()
                    if self.voice_client is not None:
                        with open(voice_wav, "rb") as f:
                            source = discord.FFmpegPCMAudio(f, pipe=True)
                            self.voice_client.play(source)

client = TTSClient()
client.run(DISCORD_TOKEN)
