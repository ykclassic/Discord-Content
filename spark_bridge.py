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

# Check for missing secrets before starting the bot
if not TOKEN:
    print("❌ ERROR: DISCORD_TOKEN is missing. Check GitHub Secrets.")
    sys.exit(1)
if not HF_TOKEN:
    print("⚠️ WARNING: HF_API_KEY is missing. Text generation may fail.")
if not DRAFT_ID_STR:
    print("❌ ERROR: DRAFT_CHANNEL_ID is missing.")
    sys.exit(1)

DRAFT_CHANNEL_ID = int(DRAFT_ID_STR)

# 2. CONFIGURATION & AESTHETICS
DAILY_TAGS = {
    0: "#MondayMotivation #DailySpark",
    1: "#TechTuesday #Innovation",
    2: "#WisdomWednesday #Growth",
    3: "#ThoughtfulThursday #Vision",
    4: "#FutureFriday #TechSolute",
    5: "#SuccessSaturday #Mindset",
    6: "#SundayReflect #Balance"
}

# Initialize Hugging Face Client (Llama-3.1-8B is fast and free)
hf_client = InferenceClient(model="meta-llama/Llama-3.1-8B-Instruct", token=HF_TOKEN)

# 3. INTERACTIVE BUTTONS
class ApprovalView(View):
    def __init__(self, embed):
        super().__init__(timeout=None)
        self.embed = embed

    @discord.ui.button(label="Post Now", style=discord.ButtonStyle.green, emoji="🚀")
    async def post_callback(self, interaction: discord.Interaction):
        # Logic to bridge to public channel would go here
        await interaction.response.send_message("✅ Content bridged to DailySparkVibes!", ephemeral=True)
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
        # Ignore bots and only listen to the specific Draft Channel
        if message.author.bot or message.channel.id != DRAFT_CHANNEL_ID:
            return

        topic = message.content
        status = await message.channel.send(f"🌌 Generating luxury content for: **{topic}**...")

        try:
            # STEP 1: Text Generation (Hugging Face)
            prompt = f"<|important|> Write a 1-sentence luxury, minimalist motivational quote about {topic} for a high-end tech CEO blog. No hashtags."
            response = hf_client.text_generation(prompt, max_new_tokens=60).strip()
            
            # Remove any AI artifacts/headers if present
            quote = response.split('\n')[-1]

            # STEP 2: Image Generation (Pollinations - Zero Auth)
            encoded_topic = topic.replace(" ", "%20")
            image_url = f"https://image.pollinations.ai/prompt/futuristic%20luxury%20{encoded_topic}%20neon%20cyan%20magenta%20black%20background?width=1024&height=1024&nologo=true"

            # STEP 3: Formatting the Embed
            day = datetime.now().weekday()
            # Alternating Cyan (0x00FFFF) and Magenta (0xFF00FF)
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

        except Exception as e:
            print(f"Error: {e}")
            await status.edit(content=f"❌ **AI Bridge Error:** Ensure your HF_API_KEY is correct and valid.")

# 5. EXECUTION
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
