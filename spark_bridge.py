import discord
from discord.ui import View
import os
import sys
import time
from datetime import datetime
from huggingface_hub import InferenceClient

# 1. ENVIRONMENT SETUP
TOKEN = os.getenv('DISCORD_TOKEN')
HF_TOKEN = os.getenv('HF_API_KEY')
DRAFT_ID_STR = os.getenv('DRAFT_CHANNEL_ID')

if not TOKEN or not HF_TOKEN or not DRAFT_ID_STR:
    print("❌ ERROR: Missing DISCORD_TOKEN, HF_API_KEY, or DRAFT_CHANNEL_ID in Secrets.")
    sys.exit(1)

DRAFT_CHANNEL_ID = int(DRAFT_ID_STR)

# Initialize Client with your specific Mistral model
# NOTE: Ensure you have "Accepted Terms" on the model page first!
hf_client = InferenceClient(model="mistralai/Mistral-7B-v0.3", token=HF_TOKEN)

# 2. INTERACTIVE UI
class ApprovalView(View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Post Now", style=discord.ButtonStyle.green, emoji="🚀")
    async def post_callback(self, interaction: discord.Interaction):
        # This keeps the bot responsive so you don't get "Interaction Failed"
        await interaction.response.edit_message(content="✅ **Approved.** Content bridged to DailySparkVibes.", view=None)

    @discord.ui.button(label="Discard", style=discord.ButtonStyle.red, emoji="🗑️")
    async def cancel_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="🗑️ **Discarded.**", view=None)

# 3. CORE BOT LOGIC
class SparkAIBridge(discord.Client):
    async def on_ready(self):
        print(f"--- TechSolute AI Bridge Online as {self.user} ---")

    async def on_message(self, message):
        if message.author.bot or message.channel.id != DRAFT_CHANNEL_ID:
            return

        topic = message.content
        status = await message.channel.send(f"🌌 Requesting AI generation for: **{topic}**...")

        # STEP 1: Text Generation (Mistral-7B-v0.3)
        quote = ""
        # Retry loop to handle 503 "Model Loading" errors
        for attempt in range(4):
            try:
                # Using the chat_completion method for better instruction following
                response = hf_client.chat_completion(
                    messages=[{"role": "user", "content": f"Write one short, luxury motivational quote about {topic} for a tech brand. No hashtags."}],
                    max_tokens=50
                )
                quote = response.choices[0].message.content.strip()
                break
            except Exception as e:
                error_msg = str(e)
                if "503" in error_msg:
                    await status.edit(content=f"⏳ Hugging Face is loading the model (Attempt {attempt+1}/4)...")
                    time.sleep(20) 
                else:
                    await status.edit(content=f"❌ **HF Error:** {error_msg[:100]}")
                    return

        if not quote:
            await status.edit(content="❌ Failed to generate quote after retries.")
            return

        # STEP 2: Image Generation (Pollinations)
        image_url = f"https://image.pollinations.ai/prompt/futuristic%20luxury%20{topic.replace(' ', '%20')}%20neon%20cyan%20magenta%20black%20background?width=1024&height=1024&nologo=true"

        # STEP 3: Embed & UI
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

# 4. RUNNER
async def main():
    intents = discord.Intents.default()
    intents.message_content = True 
    client = SparkAIBridge(intents=intents)
    async with client:
        await client.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
