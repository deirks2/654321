import os
import discord
from discord.ext import commands
import google.generativeai as genai
from google.generativeai import types
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

# ─── 환경 변수 ───────────────────────────────────────
BOT_NAME       = os.getenv("BOT_NAME", "지피")
DISCORD_TOKEN  = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MAX_HISTORY    = int(os.getenv("MAX_HISTORY", "30"))
SYSTEM_PROMPT  = os.getenv(
    "SYSTEM_PROMPT",
    f"너는 {BOT_NAME}라는 이름의 만능 AI 어시스턴트야. "
    "코딩, 정보 검색, 글쓰기, 번역, 요약, 분석 등 다양한 요청을 잘 처리해. "
    "한국어로 자연스럽게 대화하고, 친근하게 말해. "
    "여러 사람이 채널에서 대화할 수 있어. "
    "메시지에 '[유저명]:' 형태로 누가 말했는지 표시돼 있어. "
    "코드 블록은 ```언어 형식으로 작성해."
)

# ─── Discord & Gemini 초기화 ─────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

genai.configure(api_key=GEMINI_API_KEY)
MODEL  = "gemini-2.0-flash"

# ─── 상태 저장 ───────────────────────────────────────
# {channel_id: [types.Content, ...]}
conversation_history: dict[int, list] = defaultdict(list)
allowed_channels: set[int] = set()   # 비어있으면 → 모든 채널에서 동작


# ─── 유틸 함수 ───────────────────────────────────────
def trim_history(channel_id: int):
    h = conversation_history[channel_id]
    if len(h) > MAX_HISTORY:
        conversation_history[channel_id] = h[-MAX_HISTORY:]


async def ask_ai(channel_id: int, user_name: str, prompt: str) -> str:
    """대화 기록을 유지하며 Gemini에 질문"""
    user_text = f"[{user_name}]: {prompt}"

    # 히스토리에 유저 메시지 추가
    conversation_history[channel_id].append(
        types.Content(role="user", parts=[types.Part(text=user_text)])
    )
    trim_history(channel_id)

    response = client.models.generate_content(
        model=MODEL,
        contents=conversation_history[channel_id],
        config=genai.GenerationConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=2000,
        ),
    )
    reply = response.text

    # 히스토리에 모델 응답 추가
    conversation_history[channel_id].append(
        types.Content(role="model", parts=[types.Part(text=reply)])
    )
    return reply


async def send_long(message: discord.Message, text: str):
    """Discord 2000자 제한 → 분할 전송"""
    chunks = [text[i:i+1900] for i in range(0, len(text), 1900)]
    for idx, chunk in enumerate(chunks):
        if idx == 0:
            await message.reply(chunk)
        else:
            await message.channel.send(chunk)


# ─── 이벤트 ─────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ {bot.user} ({bot.user.id}) 로그인 완료")
    await bot.change_presence(
        activity=discord.Game(name=f"{BOT_NAME}야 안녕! | !도움말")
    )


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    # 채널 제한 확인
    if allowed_channels and message.channel.id not in allowed_channels:
        return

    content = message.content.strip()
    prompt  = None

    # 1) @멘션으로 호출
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        prompt = (
            content
            .replace(f"<@{bot.user.id}>", "")
            .replace(f"<@!{bot.user.id}>", "")
            .strip()
        )

    # 2) "봇이름야" / "봇이름아" 로 호출
    if prompt is None:
        for suffix in ["야", "아"]:
            call = BOT_NAME + suffix
            if content.startswith(call):
                prompt = content[len(call):].strip()
                break

    if not prompt:
        return

    async with message.channel.typing():
        try:
            reply = await ask_ai(
                message.channel.id,
                message.author.display_name,
                prompt,
            )
            await send_long(message, reply)
        except Exception as e:
            await message.reply(f"❌ 오류가 발생했어요: `{e}`")


# ─── 관리자 전용 명령어 ──────────────────────────────
@bot.command(name="채널등록")
@commands.has_permissions(administrator=True)
async def add_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    allowed_channels.add(ch.id)
    await ctx.send(
        f"✅ {ch.mention} 채널 등록 완료!\n"
        f"이제 여기서 `{BOT_NAME}야 ...` 또는 @멘션으로 대화할 수 있어요."
    )


@bot.command(name="채널해제")
@commands.has_permissions(administrator=True)
async def remove_channel(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    allowed_channels.discard(ch.id)
    status = "허용 채널이 없어서 다시 **모든 채널**에서 동작해요." if not allowed_channels else f"남은 허용 채널: {len(allowed_channels)}개"
    await ctx.send(f"✅ {ch.mention} 해제 완료. {status}")


@bot.command(name="채널목록")
@commands.has_permissions(administrator=True)
async def list_channels(ctx):
    if not allowed_channels:
        await ctx.send("📋 채널 제한 없음 — **모든 채널**에서 동작 중이에요.")
    else:
        ch_list = "\n".join(f"• <#{cid}>" for cid in allowed_channels)
        await ctx.send(f"📋 **허용된 채널 목록**\n{ch_list}")


@bot.command(name="초기화")
async def clear_history(ctx):
    conversation_history.pop(ctx.channel.id, None)
    await ctx.send("🔄 이 채널의 대화 기록을 초기화했어요!")


@bot.command(name="기록확인")
@commands.has_permissions(administrator=True)
async def check_history(ctx):
    count = len(conversation_history.get(ctx.channel.id, []))
    await ctx.send(f"📊 현재 채널 대화 기록: **{count}개** / 최대 {MAX_HISTORY}개")


@bot.command(name="도움말")
async def help_cmd(ctx):
    embed = discord.Embed(
        title=f"📖 {BOT_NAME} 사용 가이드",
        description=f"안녕하세요! 저는 **{BOT_NAME}**이에요. 뭐든 물어보세요!",
        color=0x5865F2,
    )
    embed.add_field(
        name="💬 대화하기",
        value=(
            f"`{BOT_NAME}야 [질문이나 요청]`\n"
            f"`@{BOT_NAME} [질문이나 요청]`\n"
            f"예) `{BOT_NAME}야 파이썬으로 피보나치 짜줘`"
        ),
        inline=False,
    )
    embed.add_field(
        name="🔄 대화 초기화",
        value="`!초기화` — 현재 채널 대화 기록 삭제",
        inline=False,
    )
    embed.add_field(
        name="🔧 관리자 전용",
        value=(
            "`!채널등록 [#채널]` — 봇 사용 채널 추가\n"
            "`!채널해제 [#채널]` — 봇 사용 채널 제거\n"
            "`!채널목록` — 허용된 채널 확인\n"
            "`!기록확인` — 대화 기록 개수 확인"
        ),
        inline=False,
    )
    embed.set_footer(text="채널 지정 없이 !채널등록 하면 현재 채널에 등록돼요.")
    await ctx.send(embed=embed)


# ─── 에러 핸들러 ─────────────────────────────────────
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ 이 명령어는 **관리자**만 사용할 수 있어요!")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ 채널을 찾을 수 없어요. `#채널이름` 형태로 입력해주세요.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"❌ 예상치 못한 오류: `{error}`")


# ─── 실행 ────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN 환경 변수가 설정되지 않았어요!")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았어요!")
    bot.run(DISCORD_TOKEN)
