import discord
from discord.ui import View
import os
import sys
import time
from datetime import datetime
from huggingface_hub import InferenceClient

# 1. SECURITY & ENVIRONMENT CHECK
TOKEN = os.getenv('DISCORD_TOKEN')
HF_TOKEN = os.getenv('HF_API_KEY')
DRAFT_ID_STR = os.getenv('DRAFT_CHANNEL_ID')

if not TOKEN or not DRAFT_ID_STR:
    print("❌ ERROR: DISCORD_TOKEN or DRAFT_CHANNEL_ID missing in Secrets.")
    sys.exit(1)

DRAFT_CHANNEL_ID = int(DRAFT_ID_STR)

# Initialize Hugging Face Client (Mistral is highly reliable on Free Tier)
hf_client = InferenceClient(model="mistralai/Mistral-7B-v0.3", token=HF_TOKEN)

# 2. AESTHETICS & TAGS
DAILY_TAGS = {
    0: "#MondayMotivation #DailySpark",
    1: "#TechTuesday #Innovation",
    2: "#WisdomWednesday #Growth",
    3: "#ThoughtfulThursday #Vision",
    4: "#FutureFriday #TechSolute",
    5: "#SuccessSaturday #Mindset",
    6: "#SundayReflect #Balance"
}

# 3. INTERACTIVE BUTTONS
class ApprovalView(View):
    def __init__(self, embed):
        super().__init__(timeout=None)
        self.embed = embed

    @discord.ui.button(label="Post Now", style=discord.ButtonStyle.green, emoji="🚀")
    async def post_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Content bridged! Shutting down...", ephemeral=True)
        await interaction.client.close() # Closes GitHub Action to save minutes
        self.stop()

    @discord.ui.button(label="Discard", style=discord.ButtonStyle.red, emoji="🗑️")
    async def cancel_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("🗑️ Draft discarded.", ephemeral=True)
        self.stop()

# 4. BOT LOGIC
class SparkAIBridge(discord.Client):
    async def on_ready(self):
        print(f"--- DailySparkVibes AI Bridge Active as {self.user} ---")

    async def on_message(self, message):
        if message.author.bot or message.channel.id != DRAFT_CHANNEL_ID:
            return

        topic = message.content
        status = await message.channel.send(f"🌌 Processing **{topic}**...")

        # STEP 1: Text Generation with Automatic Retry for 503 (Model Loading)
        quote = ""
        for attempt in range(3):
            try:
                prompt = f"<s>[INST] Write one short, luxury motivational quote about {topic} for a tech blog. No hashtags. [/INST] "
                response = hf_client.text_generation(prompt, max_new_tokens=50)
                quote = response.strip().split('\n')[-1] # Get last line to avoid AI chatter
                break 
            except Exception as e:
                err_str = str(e)
                if "503" in err_str and attempt < 2:
                    await status.edit(content=f"⏳ Model is loading (Attempt {attempt+1}/3)...")
                    time.sleep(15) # Wait for model to "warm up"
                else:
                    await status.edit(content=f"❌ **AI Error:** {err_str[:100]}")
                    return

        # STEP 2: Image Generation (Pollinations - Zero Auth)
        encoded_topic = topic.replace(" ", "%20")
        image_url = f"https://image.pollinations.ai/prompt/futuristic%20luxury%20{encoded_topic}%20neon%20cyan%20magenta%20black%20background?width=1024&height=1024&nologo=true"

        # STEP 3: Formatting the Embed
        day = datetime.now().weekday()
        color = 0x00FFFF if day % 2 == 0 else 0xFF00FF 
        
        embed = discord.Embed(
            title=f"DailySpark | {topic.upper()}",
            description=f"*{quote}*\n\n**Tags:**\n{DAILY_TAGS.get(day, '#DailySpark')}",
            color=color,
            timestamp=datetime.now()
        )
        embed.set_image(url=image_url)
        embed.set_footer(text="TechSolute Intelligence | DailySparkVibes")

        await message.channel.send(embed=embed, view=ApprovalView(embed))
        await status.delete()

# 5. EXECUTION
async def main():
    intents = discord.Intents.default()
    intents.message_content = True # REQUIRES TOGGLE IN DISCORD DEV PORTAL
    client = SparkAIBridge(intents=intents)
    async with client:
        await client.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
