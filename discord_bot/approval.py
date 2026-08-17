from discord_bot.client import client
from core.config import DISCORD_REVIEW_CHANNEL_ID
import discord


async def ask_approval(
    company: str,
    route: str,
    confidence,
    job_title,
    email,
    whatsapp,
    message_text,
    form_available: bool = False,
) -> bool:
    channel = client.get_channel(DISCORD_REVIEW_CHANNEL_ID)
    if channel is None:
        try:
            channel = await client.fetch_channel(DISCORD_REVIEW_CHANNEL_ID)
        except Exception as exc:
            raise RuntimeError(
                f"Discord review channel {DISCORD_REVIEW_CHANNEL_ID} não encontrado ou sem acesso: {exc}"
            ) from exc

    if channel is None:
        raise RuntimeError(
            f"Discord review channel {DISCORD_REVIEW_CHANNEL_ID} não está disponível. Verifique o ID e as permissões do bot."
        )

    embed = discord.Embed(title=f"Aprovação: {company}", color=0x2ecc71)
    embed.add_field(name="Rota", value=f"{route} (confiança: {confidence})", inline=False)
    embed.add_field(name="Vaga", value=job_title or "não identificada", inline=False)
    embed.add_field(name="Email", value=email or "não encontrado", inline=True)
    embed.add_field(name="WhatsApp", value=whatsapp or "não encontrado", inline=True)
    embed.add_field(
        name="Formulário",
        value="disponível para preenchimento local" if form_available else "não detectado",
        inline=False,
    )
    embed.add_field(name="Mensagem", value=message_text[:1000], inline=False)

    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return (
            reaction.message.id == msg.id
            and str(reaction.emoji) in ("✅", "❌")
            and not user.bot
        )

    reaction, _ = await client.wait_for("reaction_add", check=check)
    return str(reaction.emoji) == "✅"