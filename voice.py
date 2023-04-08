import discord

guild_to_voice_client = dict()

def context_to_voice_channel(ctx):
    return ctx.user.voice.channel if ctx.user.voide else None

async def get_or_create_voice_client(ctx):
    joined = False
    if ctx.guild.id in guild_to_voice_client:
        voice_client, last_user = guild_to_voice_client[ctx.guild.id]
    
    else:
        voice_channel = context_to_voice_channel(ctx)
        if voice_channel is None:
            voice_client = None
        else:
            voice_client = await voice_channel.connect()
            joined = True
    
    return (voice_client, joined)
    