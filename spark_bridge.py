import discord
from discord.ui import View
import os
import sys
import time
from datetime import datetime
from huggingface_hub import InferenceClient

# 1. AUTH
TOKEN = os.getenv('DISCORD_TOKEN')
HF_TOKEN = os.getenv('HF_API_KEY')
DRAFT_ID_STR = os.getenv('DRAFT_CHANNEL_ID')

if not TOKEN or not HF_TOKEN:
    print("❌ ERROR: Secrets not loaded.")
    sys.exit(1)

# Using the Instruct model which is better for the Free API
client = InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.3", token=HF_TOKEN)

class ApprovalView(View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Post Now", style=discord.ButtonStyle.green, emoji="🚀")
    async def post_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="✅ **Success!** Bridged to DailySparkVibes.", view=None)

class SparkAIBridge(discord.Client):
    async def on_message(self, message):
        if message.author.bot or message.channel.id != int(DRAFT_ID_STR):
            return

        topic = message.content
        status = await message.channel.send(f"🌌 Hugging Face is generating for: **{topic}**...")

        # STEP 1: Text Generation (With 503 Retry)
        quote = ""
        for attempt in range(3):
            try:
                # Chat completion is the standard for Instruct models
                response = client.chat_completion(
                    messages=[{"role": "user", "content": f"Write a short luxury quote about {topic}."}],
                    max_tokens=40
                )
                quote = response.choices[0].message.content.strip()
                break
            except Exception as e:
                if "503" in str(e):
                    await status.edit(content=f"⏳ Loading model (Attempt {attempt+1}/3)...")
                    time.sleep(20)
                else:
                    await status.edit(content=f"❌ **API Error:** {str(e)[:100]}")
                    return

        # STEP 2: Image & Embed
        image_url = f"https://image.pollinations.ai/prompt/luxury%20{topic.replace(' ', '%20')}?nologo=true"
        embed = discord.Embed(title=f"DailySpark | {topic.upper()}", description=f"*{quote}*", color=0x00FFFF)
        embed.set_image(url=image_url)

        await message.channel.send(embed=embed, view=ApprovalView())
        await status.delete()

async def main():
    intents = discord.Intents.default()
    intents.message_content = True 
    async with SparkAIBridge(intents=intents) as bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
