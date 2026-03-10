import discord
from discord.ui import View
import os
import sys
import time
from datetime import datetime
from huggingface_hub import InferenceClient

# 1. AUTHENTICATION (Citing)
TOKEN = os.getenv('DISCORD_TOKEN')
HF_TOKEN = os.getenv('HF_API_KEY')
DRAFT_ID_STR = os.getenv('DRAFT_CHANNEL_ID')

if not TOKEN or not HF_TOKEN or not DRAFT_ID_STR:
    print("❌ ERROR: Missing required GitHub Secrets.")
    sys.exit(1)

DRAFT_CHANNEL_ID = int(DRAFT_ID_STR)

# Recommended stable model for free-tier inference (Citing)
# NOTE: You MUST accept terms at huggingface.co/mistralai/Mistral-7B-v0.3
hf_client = InferenceClient(model="mistralai/Mistral-7B-v0.3", token=HF_TOKEN)

# 2. INTERACTIVE BUTTONS
class ApprovalView(View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Post Now", style=discord.ButtonStyle.green, emoji="🚀")
    async def post_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="✅ **Content Approved.** Bridge successful.", view=None)
        # Note: Bot stays alive to handle interaction

    @discord.ui.button(label="Discard", style=discord.ButtonStyle.red, emoji="🗑️")
    async def cancel_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="🗑️ **Draft Discarded.**", view=None)

# 3. CONTENT ENGINE
class SparkAIBridge(discord.Client):
    async def on_message(self, message):
        if message.author.bot or message.channel.id != DRAFT_CHANNEL_ID:
            return

        topic = message.content
        status = await message.channel.send(f"🌌 Hugging Face is analyzing **{topic}**...")

        # STEP 1: Text Generation with 503 Retry Logic (Citing)
        quote = ""
        for attempt in range(5): # Up to 5 retries for model spin-up
            try:
                # Chat completion is more robust for instruction following
                response = hf_client.chat_completion(
                    messages=[{"role": "user", "content": f"Write one unique, 1-sentence luxury motivational quote about {topic}. No hashtags."}],
                    max_tokens=50
                )
                quote = response.choices[0].message.content.strip()
                break
            except Exception as e:
                if "503" in str(e):
                    await status.edit(content=f"⏳ Model is spinning up... (Attempt {attempt+1}/5)")
                    time.sleep(20) # Official recommendation: wait for model to load
                else:
                    await status.edit(content=f"❌ **HF Error:** {str(e)[:100]}")
                    return

        # STEP 2: Image Generation
        image_url = f"https://image.pollinations.ai/prompt/futuristic%20luxury%20{topic.replace(' ', '%20')}%20neon%20cyan%20magenta%20black%20background?width=1024&height=1024&nologo=true"

        # STEP 3: Dispatch
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
    async with SparkAIBridge(intents=intents) as client:
        await client.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
