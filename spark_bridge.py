import discord
from discord.ui import View
import os
import sys
import requests
import json
from datetime import datetime

# 1. SETUP
TOKEN = os.getenv('DISCORD_TOKEN')
DRAFT_ID_STR = os.getenv('DRAFT_CHANNEL_ID')

if not TOKEN or not DRAFT_ID_STR:
    print("❌ ERROR: Missing Secrets.")
    sys.exit(1)

DRAFT_CHANNEL_ID = int(DRAFT_ID_STR)

DAILY_TAGS = {
    0: "#MondayMotivation #DailySpark", 1: "#TechTuesday #Innovation",
    2: "#WisdomWednesday #Growth", 3: "#ThoughtfulThursday #Vision",
    4: "#FutureFriday #TechSolute", 5: "#SuccessSaturday #Mindset",
    6: "#SundayReflect #Balance"
}

# 2. BUTTON LOGIC
class ApprovalView(View):
    def __init__(self):
        super().__init__(timeout=180) # View stays active for 3 minutes

    @discord.ui.button(label="Post Now", style=discord.ButtonStyle.green, emoji="🚀")
    async def post_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="✅ **Content Approved and Bridged.**", view=None)
        # In a real bridge, you'd send the embed to your public channel here
        # interaction.client.dispatch("bridge_post", interaction.message.embeds[0])

    @discord.ui.button(label="Discard", style=discord.ButtonStyle.red, emoji="🗑️")
    async def cancel_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="🗑️ **Draft Discarded.**", view=None)

# 3. BOT LOGIC
class SparkAIBridge(discord.Client):
    async def on_ready(self):
        print(f"--- DailySparkVibes Bridge Online ---")

    async def on_message(self, message):
        if message.author.bot or message.channel.id != DRAFT_CHANNEL_ID:
            return

        topic = message.content
        status = await message.channel.send(f"🌌 Synthesizing content for: **{topic}**...")

        try:
            # STEP 1: Improved Text Generation
            # Using a more reliable prompt structure for Pollinations
            prompt_payload = {
                "messages": [{"role": "user", "content": f"Write one unique, elite 1-sentence motivational quote about {topic} for a luxury tech brand. No hashtags."}],
                "model": "mistral"
            }
            text_req = requests.post("https://text.pollinations.ai/", json=prompt_payload)
            quote = text_req.text.strip() if text_req.status_code == 200 else "Innovation is the only path forward."

            # STEP 2: Image Generation
            image_url = f"https://image.pollinations.ai/prompt/futuristic%20luxury%20{topic.replace(' ', '%20')}%20neon%20cyan%20magenta%20black%20background?width=1024&height=1024&nologo=true"

            # STEP 3: Embed Creation
            day = datetime.now().weekday()
            embed = discord.Embed(
                title=f"DailySpark | {topic.upper()}",
                description=f"*{quote}*",
                color=0x00FFFF if day % 2 == 0 else 0xFF00FF,
                timestamp=datetime.now()
            )
            embed.add_field(name="Tags:", value=DAILY_TAGS.get(day, "#DailySpark"))
            embed.set_image(url=image_url)
            embed.set_footer(text="TechSolute Intelligence | DailySparkVibes")

            # Send embed with interactive buttons
            await message.channel.send(embed=embed, view=ApprovalView())
            await status.delete()

        except Exception as e:
            await status.edit(content=f"❌ **AI Bridge Error:** {str(e)[:50]}")

# 4. START
async def main():
    intents = discord.Intents.default()
    intents.message_content = True 
    client = SparkAIBridge(intents=intents)
    async with client:
        await client.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
