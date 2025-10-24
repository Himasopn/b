import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Environment variable se bot token lo
BOT_TOKEN = os.environ.get('BOT_TOKEN')
API_URL = "https://api.giftedtech.co.ke/downloader/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    welcome_msg = """
🎥 *YouTube Downloader Bot* 🎥

Mujhe koi bhi YouTube link bhejo aur main video download kar dunga!

*Commands:*
/start - Bot ko start karo
/help - Help message

*Kaise use karein:*
Bas YouTube link bhejo aur wait karo!
    """
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    help_text = """
*Kaise use karein:*

1️⃣ Koi bhi YouTube video ka link copy karo
2️⃣ Mujhe yaha paste kar do
3️⃣ Main video download kar dunga

*Example:*
`https://www.youtube.com/watch?v=xxxxx`
`https://youtu.be/xxxxx`

Bas itna hi! 😊
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """YouTube link process karo aur video download karo"""
    url = update.message.text.strip()
    
    # Check if it's a YouTube link
    if not ('youtube.com' in url or 'youtu.be' in url):
        await update.message.reply_text("❌ Please send a valid YouTube link!")
        return
    
    # Processing message
    processing_msg = await update.message.reply_text("⏳ Processing your request... Please wait!")
    
    try:
        # API call
        params = {'url': url}
        response = requests.get(API_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                result = data.get('result', {})
                title = result.get('title', 'Video')
                download_url = result.get('download_url')
                thumbnail = result.get('thumbnail')
                
                if download_url:
                    # Send thumbnail if available
                    if thumbnail:
                        try:
                            await update.message.reply_photo(
                                photo=thumbnail,
                                caption=f"📹 *{title}*\n\n⬇️ Downloading...",
                                parse_mode='Markdown'
                            )
                        except:
                            pass
                    
                    # Download video
                    await processing_msg.edit_text("⬇️ Downloading video...")
                    
                    video_response = requests.get(download_url, stream=True, timeout=120)
                    
                    if video_response.status_code == 200:
                        # Save temporarily
                        filename = f"{title[:50]}.mp4"
                        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                        
                        with open(filename, 'wb') as f:
                            for chunk in video_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        # Upload to Telegram
                        await processing_msg.edit_text("📤 Uploading to Telegram...")
                        
                        with open(filename, 'rb') as video_file:
                            await update.message.reply_video(
                                video=video_file,
                                caption=f"📹 *{title}*\n\n✅ Downloaded successfully!",
                                parse_mode='Markdown',
                                supports_streaming=True
                            )
                        
                        # Delete temp file
                        os.remove(filename)
                        await processing_msg.delete()
                    else:
                        await processing_msg.edit_text("❌ Failed to download video. Please try again!")
                else:
                    await processing_msg.edit_text("❌ Download URL not found!")
            else:
                error_msg = data.get('message', 'Unknown error occurred')
                await processing_msg.edit_text(f"❌ Error: {error_msg}")
        else:
            await processing_msg.edit_text("❌ API request failed. Please try again later!")
            
    except requests.Timeout:
        await processing_msg.edit_text("⏰ Request timeout! Video might be too large or slow connection.")
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error occurred: {str(e)}")

def main():
    """Bot ko start karo"""
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable not set!")
        return
    
    # Application create karo
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers add karo
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    # Bot start karo
    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
