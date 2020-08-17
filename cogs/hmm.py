import re
import discord
import json
import os 
import discord
from discord.ext import commands

class Word():
    def __init__(self, word, re, emoji=None, file_extensions=None):
        self.word = word
        self.re = re
        self.rolename = word.capitalize() + " lvl "
        self.emoji = emoji if emoji else word
        self.file_extensions = file_extensions
    
    def __repr__(self):
        return self.word

class Hmm(commands.Cog):
    words = [
        Word("hmm", r"\bh+(r+)?m+"),
        Word("mmh", r"\bm+(r+)?h+"),
        Word("perhaps", r"\b(per|may)haps"),
        Word("aaaahhhh", r"\ba+((r+)?g+)?h+\b", emoji="aaahhh"),
        Word("ok", r"\bo+k+((a+y+)|(ie+)|(ey))?\b"),
        Word("yes", r"\by+e+s+\b"),
        Word("haha", r"(\b(b+a+|a+)?((h+a+)+))"),
        Word("lmao", r"lm(f?)ao+"),
        Word("rofl", r"ro(t?)fl+", emoji="🤣"),
        Word("lol", r"\bl((o|e|u)+l+)+\b"),
        Word("no", r"\b(no+(p(e+)?)?)+(n)?\b"),
        Word("cade", r"\b(ca(de|t))(s)?|kitt(en|y|ie(s)?)|meow|nya(n)?\b"),
        Word("choon", r"\bhttps://clyp.it/", file_extensions=["mp3", "wav", "ogg", "flac"]),
    ]

    def __init__(self, bot):
        self.bot = bot
        print("loaded hmm")

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.command()
    async def stats(self, ctx):
        author = ctx.message.author
        self.refresh_stats(author)
        for mention in ctx.message.mentions:
            author = mention
        user = self.load_user_stats(author)
        stats = []
        if user:
            stats = sorted(
                    [key for key in user.keys() if user[key] > 0],
                    key=lambda x: user[x],
                    reverse=True
            )
        level = self.get_level(user)
        print(level)

        embed = discord.Embed(
                title="{0} [Level {1}]".format(author.name, level),
                color=self.choose_level_color(level)
        )
        for stat in stats:
            embed.add_field(name=stat, value="lv. {}".format(user[stat]), inline=True,)
        # await ctx.channel.send("Stats for {0.mention}:\n{1}"
        #       .format(ctx.message.author, stats_string))
        await ctx.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):   
        if message.author == self.bot.user:
            return         

        for word in self.words:
            if self.word_matches_message(word, message):
                await self.bot.wait_until_ready()
                print("sending")
                print ("** leveling user {0} for:  \"{1}\"".format(message.author.name, message.content))
                await self.level_user_for_word(word, message)
                print("** done. \n")


    def word_matches_message(self, word, message):
        text = message.content
        if (re.search(word.re, text, re.IGNORECASE)):
            return True
        if word.file_extensions and message.attachments:
            for attachment in message.attachments:
                for extension in word.file_extensions:
                    if re.search(extension, attachment.filename, re.IGNORECASE):
                        return True
        return False

    async def level_user_for_word(self, word, message):
        print(word.word)
        author = message.author
        await self.level_up(author, word, message.channel)

        emoji = discord.utils.get(message.guild.emojis, name=(word.emoji))
        if emoji:
            print(emoji)
            await message.add_reaction(emoji)
        else:
            await message.add_reaction(word.emoji)
            
    def choose_level_color(self, lvl):
        if lvl >= 1000:
            return discord.Color.purple()
        if lvl >= 500:
            return discord.Color.dark_blue()
        if lvl >= 200:
            return discord.Color.gold()
        if lvl >= 175:
            return discord.Color.dark_gold()
        if lvl >= 150:
            return discord.Color.blue()
        if lvl >= 100:
            return discord.Color.red()
        if lvl >= 50:
            return discord.Color.teal()
        if lvl >= 25:
            return discord.Color.dark_red()
        if lvl >= 1:
            return discord.Color.dark_magenta()
        return discord.Color.default()
    
    def get_level(self, user):
        stats = [user[stat] for stat in user.keys()]
        if len(stats) > 0:
            overall_level = sum(stats)
        else:
            overall_level = 0
        return overall_level

    async def level_up(self, member, word, channel):
        user = self.load_user_stats(member)
        lvl = user[word.word] + 1
        user[word.word] = lvl
        print(user)

        overall_level = self.get_level(user)

        if lvl % 25 == 0 and lvl > 0 and (lvl % 50 == 0 or lvl < 100) or lvl == 10:
            await channel.send("Congrats, {0.mention}, you have advanced to {1} level {2}!".format(member, word.word, lvl))

        if overall_level % 50 == 0 and overall_level > 0:
            await channel.send("Congrats, {0.mention}, you have reached an overall power level of {2}!!".format(member, word.word, overall_level))

        self.save_user(member, user)

    def save_user(self, member, user_stats):
        for word in self.words:
            if word.word not in user_stats:
                user_stats[word.word] = 0
            else:
                user_stats[word.word] = int(user_stats[word.word])

        guild_id = str(member.guild.id)
        member_id = str(member.id)
        if not os.path.exists("cogs/hmm/roles/" + guild_id):
            os.mkdir("cogs/hmm/roles/" + guild_id)

        filename = "cogs/hmm/roles/" + guild_id + "/" + member_id + ".json"

        structure = { 
                "name" : member.name,
                "stats" : user_stats
        }
        data = json.dumps(structure)
        # print(data)
        with open(filename, "w") as f:
            data = json.loads(data)
            json.dump(data, f, indent=2, separators=(',', ': '))

    def load_user_stats(self, member):
        guild_id = str(member.guild.id)
        member_id = str(member.id)
        filename = "cogs/hmm/roles/" + guild_id + "/" + member_id + ".json"
        if os.path.exists(filename):
            with open(filename, "r") as f:
                js = f.read()
                js = json.loads(js)
                print(js)
                if "stats" in js:
                    return js["stats"]
        else:
            self.save_user(member, {})
            self.load_user_stats(member)

    def refresh_stats(self, member):
        user = self.load_user_stats(member)
        self.save_user(member, user)
        

def setup(bot):
    bot.add_cog(Hmm(bot))
