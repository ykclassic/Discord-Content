import discord
from discord.ui import View
import os
import sys
import time
from datetime import datetime
from huggingface_hub import InferenceClient

# 1. AUTH & CONFIG
TOKEN = os.getenv('DISCORD_TOKEN')
HF_TOKEN = os.getenv('HF_API_KEY')
DRAFT_ID_STR = os.getenv('DRAFT_CHANNEL_ID')

if not TOKEN or not HF_TOKEN or not DRAFT_ID_STR:
    print("❌ ERROR: Missing Secrets in GitHub.")
    sys.exit(1)

DRAFT_CHANNEL_ID = int(DRAFT_ID_STR)

# Model: Zephyr 7B is more reliable for text_generation than Mistral on free tier
client = InferenceClient(model="HuggingFaceH4/zephyr-7b-beta", token=HF_TOKEN)

# 2. INTERACTIVE BUTTONS
class ApprovalView(View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Post Now", style=discord.ButtonStyle.green, emoji="🚀")
    async def post_callback(self, interaction: discord.Interaction):
        # Acknowledge immediately to prevent "Interaction Failed"
        await interaction.response.edit_message(content="✅ **Success!** Content bridged.", view=None)

    @discord.ui.button(label="Discard", style=discord.ButtonStyle.red, emoji="🗑️")
    async def cancel_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="🗑️ **Discarded.**", view=None)

# 3. CORE LOGIC
class SparkAIBridge(discord.Client):
    async def on_ready(self):
        print(f"--- TechSolute AI Bridge Online ---")

    async def on_message(self, message):
        if message.author.bot or message.channel.id != DRAFT_CHANNEL_ID:
            return

        topic = message.content
        status = await message.channel.send(f"🌌 Processing topic: **{topic}**...")

        # STEP 1: Text Generation (Using stable text_generation method)
        quote = ""
        prompt = f"<|system|>\nYou are a luxury tech brand voice.</s>\n<|user|>\nWrite one short elite motivational quote about {topic}. No hashtags.</s>\n<|assistant|>\n"
        
        for attempt in range(3):
            try:
                # Citing: text_generation is the most stable free tier method
                output = client.text_generation(
                    prompt, 
                    max_new_tokens=40,
                    return_full_text=False,
                    stop_sequences=["</s>"]
                )
                quote = output.strip()
                break
            except Exception as e:
                err_str = str(e)
                if "503" in err_str:
                    await status.edit(content=f"⏳ Model is warming up... (Attempt {attempt+1}/3)")
                    time.sleep(20) # Citing: Wait for model load
                else:
                    await status.edit(content=f"❌ **HF Error:** {err_str[:150]}")
                    return

        if not quote:
            await status.edit(content="❌ AI failed to return text.")
            return

        # STEP 2: Image Generation (Pollinations)
        image_url = f"https://image.pollinations.ai/prompt/futuristic%20luxury%20{topic.replace(' ', '%20')}%20neon%20cyan%20magenta%20black%20background?width=1024&height=1024&nologo=true"

        # STEP 3: Embed Delivery
        day = datetime.now().weekday()
        embed = discord.Embed(
            title=f"DailySpark | {topic.upper()}",
            description=f"*{quote}*",
            color=0x00FFFF if day % 2 == 0 else 0xFF00FF,
            timestamp=datetime.now()
        )
        embed.set_image(url=image_url)
        embed.set_footer(text="TechSolute Intelligence | DailySparkVibes")

        await message.channel.send(embed=embed, view=ApprovalView())
        await status.delete()

# 4. START
async def main():
    intents = discord.Intents.default()
    intents.message_content = True 
    async with SparkAIBridge(intents=intents) as bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
