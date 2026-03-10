import discord
from discord.ui import View
import os
import sys
import time
from datetime import datetime
from huggingface_hub import InferenceClient

# 1. SETUP
TOKEN = os.getenv('DISCORD_TOKEN')
HF_TOKEN = os.getenv('HF_API_KEY')
DRAFT_ID_STR = os.getenv('DRAFT_CHANNEL_ID')

if not TOKEN or not HF_TOKEN or not DRAFT_ID_STR:
    print("❌ ERROR: Missing Secrets.")
    sys.exit(1)

# Using Zephyr 7B - Now calling the conversational task specifically
client = InferenceClient(model="HuggingFaceH4/zephyr-7b-beta", token=HF_TOKEN)

# 2. UI BUTTONS
class ApprovalView(View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Post Now", style=discord.ButtonStyle.green, emoji="🚀")
    async def post_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="✅ **Content Approved.**", view=None)

    @discord.ui.button(label="Discard", style=discord.ButtonStyle.red, emoji="🗑️")
    async def cancel_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="🗑️ **Draft Discarded.**", view=None)

# 3. CORE LOGIC
class SparkAIBridge(discord.Client):
    async def on_message(self, message):
        if message.author.bot or message.channel.id != int(DRAFT_ID_STR):
            return

        topic = message.content
        status = await message.channel.send(f"🌌 Requesting conversational AI for: **{topic}**...")

        # STEP 1: Conversational Generation (Fixes the task error)
        quote = ""
        messages = [
            {"role": "system", "content": "You are a luxury tech brand voice. Write one short, elite motivational quote."},
            {"role": "user", "content": f"Topic: {topic}. Generate one 1-sentence quote. No hashtags."}
        ]

        for attempt in range(3):
            try:
                # chat_completion is the only supported task for this model/provider combo
                response = client.chat_completion(
                    messages=messages,
                    max_tokens=50
                )
                quote = response.choices[0].message.content.strip()
                # Remove quotes if the AI added them
                quote = quote.replace('"', '')
                break
            except Exception as e:
                err_str = str(e)
                if "503" in err_str:
                    await status.edit(content=f"⏳ Server is warming up... (Attempt {attempt+1}/3)")
                    time.sleep(20)
                else:
                    await status.edit(content=f"❌ **HF Error:** {err_str[:100]}")
                    return

        # STEP 2: Image Generation
        image_url = f"https://image.pollinations.ai/prompt/futuristic%20luxury%20{topic.replace(' ', '%20')}%20neon%20cyan%20magenta%20black%20background?width=1024&height=1024&nologo=true"

        # STEP 3: Embed Delivery
        embed = discord.Embed(
            title=f"DailySpark | {topic.upper()}",
            description=f"*{quote}*",
            color=0x00FFFF,
            timestamp=datetime.now()
        )
        embed.set_image(url=image_url)
        embed.set_footer(text="TechSolute Intelligence | DailySparkVibes")

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
