import discord
from discord.ui import View
import os
import time
from datetime import datetime
from huggingface_hub import InferenceClient

# 1. Configuration (Loaded from GitHub Secrets)
TOKEN = os.getenv('DISCORD_TOKEN')
HF_TOKEN = os.getenv('HF_API_KEY') # Your Hugging Face Read Token
DRAFT_CHANNEL_ID = int(os.getenv('DRAFT_CHANNEL_ID', '0'))

# 2. Daily Aesthetic Settings
DAILY_TAGS = {
    0: "#MondayMotivation #DailySpark",
    1: "#TechTuesday #Innovation",
    2: "#WisdomWednesday #Growth",
    3: "#ThoughtfulThursday #Vision",
    4: "#FutureFriday #TechSolute",
    5: "#SuccessSaturday #Mindset",
    6: "#SundayReflect #Balance"
}

# Initialize Hugging Face Client (Using Llama 3.1 8B for speed & reliability)
hf_client = InferenceClient(model="meta-llama/Llama-3.1-8B-Instruct", token=HF_TOKEN)

class ApprovalView(View):
    def __init__(self, embed):
        super().__init__(timeout=None)
        self.embed = embed

    @discord.ui.button(label="Post Now", style=discord.ButtonStyle.green, emoji="🚀")
    async def post_callback(self, interaction: discord.Interaction):
        # In a real scenario, you'd send this to your public channel ID here
        await interaction.response.send_message("✅ Bridged to DailySparkVibes!", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Discard", style=discord.ButtonStyle.red, emoji="🗑️")
    async def cancel_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("🗑️ Draft deleted.", ephemeral=True)
        self.stop()

class SparkAIBridge(discord.Client):
    async def on_ready(self):
        print(f"--- DailySparkVibes AI Bridge Active ---")

    async def on_message(self, message):
        if message.author.bot or message.channel.id != DRAFT_CHANNEL_ID:
            return

        topic = message.content
        status = await message.channel.send(f"🌌 Processing **{topic}** through TechSolute AI...")

        try:
            # STEP 1: Generate Content via Hugging Face
            prompt = f"Write a luxury, minimalist motivational quote about {topic} for a tech CEO's blog. Keep it under 40 words."
            response = hf_client.text_generation(prompt, max_new_tokens=100)
            
            # STEP 2: Generate Image via Pollinations (Zero-Auth)
            # We encode the topic into a URL for the futuristic neon aesthetic
            encoded_topic = topic.replace(" ", "%20")
            image_url = f"https://image.pollinations.ai/prompt/futuristic%20luxury%20{encoded_topic}%20neon%20cyan%20magenta%20black%20background?width=1024&height=1024&nologo=true"

            # STEP 3: Build the Luxury Embed
            day = datetime.now().weekday()
            color = 0x00FFFF if day % 2 == 0 else 0xFF00FF # Cyan/Magenta toggle
            
            embed = discord.Embed(
                title=f"DailySpark | {topic.upper()}",
                description=f"\"{response.strip()}\"\n\n**Tags:**\n{DAILY_TAGS.get(day, '#DailySpark')}",
                color=color,
                timestamp=datetime.now()
            )
            embed.set_image(url=image_url)
            embed.set_footer(text="Nexus Intelligence Suite | DailySparkVibes")

            await message.channel.send(embed=embed, view=ApprovalView(embed))
            await status.delete()

        except Exception as e:
            await status.edit(content=f"❌ **AI Bridge Error:** {str(e)}")

async def main():
    intents = discord.Intents.default()
    intents.message_content = True
    client = SparkAIBridge(intents=intents)
    async with client:
        await client.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
