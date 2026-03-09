import discord
from discord.ui import View
import os
import sys
import requests
from datetime import datetime

# 1. SECURITY & ENVIRONMENT CHECK
TOKEN = os.getenv('DISCORD_TOKEN')
DRAFT_ID_STR = os.getenv('DRAFT_CHANNEL_ID')

if not TOKEN or not DRAFT_ID_STR:
    print("❌ ERROR: DISCORD_TOKEN or DRAFT_CHANNEL_ID missing.")
    sys.exit(1)

DRAFT_CHANNEL_ID = int(DRAFT_ID_STR)

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
        await interaction.client.close() 
        self.stop()

    @discord.ui.button(label="Discard", style=discord.ButtonStyle.red, emoji="🗑️")
    async def cancel_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("🗑️ Draft discarded.", ephemeral=True)
        self.stop()

# 4. BOT LOGIC
class SparkAIBridge(discord.Client):
    async def on_ready(self):
        print(f"--- DailySparkVibes AI Bridge (Pollinations Mode) Active ---")

    async def on_message(self, message):
        if message.author.bot or message.channel.id != DRAFT_CHANNEL_ID:
            return

        topic = message.content
        status = await message.channel.send(f"🌌 Crafting luxury content for: **{topic}**...")

        try:
            # STEP 1: Text Generation via Pollinations (Text API)
            # We use a clean prompt to get a high-end quote
            text_prompt = f"Write one short, elite motivational quote about {topic} for a tech CEO. No hashtags, no intro."
            text_url = f"https://text.pollinations.ai/{text_prompt.replace(' ', '%20')}?model=mistral"
            
            text_response = requests.get(text_url)
            quote = text_response.text.strip() if text_response.status_code == 200 else "Drive the future."

            # STEP 2: Image Generation (Pollinations Image API)
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

        except Exception as e:
            await status.edit(content=f"❌ **Bridge Error:** {str(e)[:100]}")

# 5. EXECUTION
async def main():
    intents = discord.Intents.default()
    intents.message_content = True 
    client = SparkAIBridge(intents=intents)
    async with client:
        await client.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
