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

# List of highly available conversational models (2026 Free Tier)
# We rotate these if one fails
MODEL_POOL = [
    "HuggingFaceH4/zephyr-7b-beta",
    "Qwen/Qwen2.5-7B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3"
]

# 2. UI BUTTONS
class ApprovalView(View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Post Now", style=discord.ButtonStyle.green, emoji="🚀")
    async def post_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="✅ **Content Approved and Bridged.**", view=None)

    @discord.ui.button(label="Discard", style=discord.ButtonStyle.red, emoji="🗑️")
    async def cancel_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="🗑️ **Draft Discarded.**", view=None)

# 3. CORE LOGIC
class SparkAIBridge(discord.Client):
    async def on_message(self, message):
        if message.author.bot or message.channel.id != int(DRAFT_ID_STR):
            return

        topic = message.content
        status = await message.channel.send(f"🌌 Launching AI Bridge for: **{topic}**...")

        # STEP 1: Multi-Model Generation Loop
        quote = ""
        messages = [
            {"role": "system", "content": "You are a luxury tech brand voice. Write one short, elite 1-sentence motivational quote."},
            {"role": "user", "content": f"Topic: {topic}. No hashtags, no intro."}
        ]

        # Try different models if one fails (Citing for multi-model logic)
        for model_id in MODEL_POOL:
            try:
                client = InferenceClient(model=model_id, token=HF_TOKEN)
                response = client.chat_completion(messages=messages, max_tokens=45)
                quote = response.choices[0].message.content.strip().replace('"', '')
                if quote: 
                    print(f"✅ Success with model: {model_id}")
                    break
            except Exception as e:
                print(f"⚠️ {model_id} failed: {str(e)[:50]}")
                continue 

        # FINAL FALLBACK (If all AI models fail)
        if not quote:
            quote = f"The future of {topic} belongs to those who build it today."
            await message.channel.send("⚠️ **Notice:** AI servers busy. Using high-end fallback quote.")

        # STEP 2: Image Generation (Pollinations)
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
