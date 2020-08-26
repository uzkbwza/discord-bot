import re
import os 
import discord
import random
import sqlite3
from discord.ext import commands

futureworld = 699465129145925673

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
        Word("haha", r"(\b(b+a+|a+)?((h+a+)+))\b"),
        Word("rofl", r"ro(t?)fl+", emoji="🤣"),
        Word("no", r"\b(no+(p(e+)?)?)+(n)?\b"),
        Word("cade", r"\b(ca(de|t))(s)?|kitt(en|y|ie(s)?)|meow|nya(n)?\b"),
        Word("afx", r"aphex|\bafx", emoji="licker"),
        Word("cringe", r"\bcri+nge"),
        Word("creep", r"\bcreep"),
        Word("bruh", r"\bbru+h+\b"),
        Word("reee", r"\br+e+\b"),
        Word("choon", r"\bhttps://clyp.it/|https://soundcloud.com/", file_extensions=["mp3", "wav", "ogg", "flac"]),
    ]

    def __init__(self, bot):
        self.bot = bot
        open('hmm.db', 'a+').close()
        self.conn = sqlite3.connect('hmm.db', detect_types=sqlite3.PARSE_COLNAMES)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        self.create_user_table()
        self.max_the_game_cooldown = 100
        self.the_game_cooldowns = {}
        self.init_servrers = []
        print("loaded hmm")

    def create_user_table(self):
            words = self.words
            parameters = []
            self.c.execute(
                "CREATE TABLE IF NOT EXISTS hmm_stats ( name text, id text, guild text )"
            )
            for word in words:
                sql = "ALTER TABLE hmm_stats ADD COLUMN {0} integer default 0".format(word.word)
                try:
                    self.c.execute(sql)
                    print("added column {0}".format(word.word))
                except Exception as e:
                    print(e)
            self.conn.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        print("joined " + guild.name)
        for user in guild.users:
            self.load_user_stats(user)

    @commands.Cog.listener()
    async def on_message(self, message):   
        if message.author == self.bot.user:
            return         
        
        # print("{}: {}".format(message.author.name, message.content))
        await self.the_game(message)

        for word in self.words:
            if self.word_matches_message(word, message):
                await self.bot.wait_until_ready()
                print("sending")
                print ("** leveling user {0} for:  \"{1}\"".format(message.author.name, message.content))
                await self.level_user_for_word(word, message)
                print("** done. \n")

    async def the_game(self, message):
        """ semi-randomly announce the game """
        guild = message.guild.id
        if guild not in self.the_game_cooldowns:
            self.the_game_cooldowns[guild] = self.max_the_game_cooldown

        p = random.randrange(3)
        self.the_game_cooldowns[guild] = self.the_game_cooldowns[guild] - p

        if self.the_game_cooldowns[guild] <= 0:
            await message.channel.send("**the game**")
            self.the_game_cooldowns[guild] = self.max_the_game_cooldown

    @commands.command()
    async def invite(self, ctx):
        image=ctx.guild.me.avatar_url
        embed=discord.Embed(
                title="Invite me to your server!", 
                description="""**[🔵 Admin](https://discord.com/api/oauth2/authorize?client_id=714976319921717268&permissions=8&scope=bot)
                [🔴 Non-admin](https://discord.com/api/oauth2/authorize?client_id=714976319921717268&permissions=134205376&scope=bot)** (potentially fewer features)""",
                )
        embed.set_thumbnail(url=image)

        await ctx.channel.send(embed=embed)

    @commands.command()
    async def stats(self, ctx):
        author = ctx.message.author
        # refresh user
        self.load_user_stats(author)
        for mention in ctx.message.mentions:
            author = mention
        user = self.load_user_stats(author)
        stats = []
        if user:
            stats = sorted(
                    [key for key in user.keys() if key in [word.word for word in self.words] and int(user[key]) > 0],
                    key=lambda word: user[word],
                    reverse=True
            )
            print(stats)
        level = self.get_level(user)
        print(level)

        description = []
        for stat in stats:
            rank = "**{0}** - lv. {1}".format(stat, user[stat])
            description.append(rank)

        description = "\n".join(description)

        embed = discord.Embed(
                title="{0} [Level {1}]".format(author.name, level),
                color=self.choose_level_color(level),
                description=description
        )
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def ranks(self, ctx, arg=None):
        rank_chart_title = ""
        if arg is None:
            rank_chart_title = "Global power rankings"
        elif arg in [word.word for word in self.words]:
            rank_chart_title = "Rankings for {}".format(arg)
        else:
            await ctx.channel.send("Not a valid rankable stat.")
            return
        ranked_users = self.get_ranks(ctx, arg=arg)
        if len(ranked_users) == 0:
            await ctx.channel.send("There are no ranked users yet.")
            return

        # get top 10
        image=self.bot.get_user(int(ranked_users[0]['id'])).avatar_url
        description = []
        for i in range(0, min(10, len(ranked_users))):
            rank = None
            mention = "<@{}>".format(ranked_users[i]['id'])
            if not arg:
                rank = self.get_level(ranked_users[i])
            else:
                rank = ranked_users[i][arg]
            string = "**{0}: {1}** - lv. {2}".format(i + 1, mention, rank)
            if i == 0:
                string = "**👑: {1} - lv. {2}** ".format(i + 1, mention, rank)
            description.append(string)

        description = "\n".join(description)

        embed = discord.Embed(
                title=rank_chart_title,
                color=discord.Color.gold(),
                description=description
        )       
        embed.set_thumbnail(url=image)
        await ctx.channel.send(embed=embed)

    @commands.command()
    async def rank(self, ctx):
        author = ctx.message.author
        member = None
        arg = None
        print('args')
        for a in ctx.message.content.split(' '):
            print(a)
            if a in [word.word for word in self.words]:
                print('hello')
                arg = a


        if ctx.message.mentions:
            member = ctx.message.mentions[0]

        whose = "Your" if not member else member.name + "'s"

        if not member:
            member = author 

        self.load_user_stats(member)

        rank = next(filter(lambda user: int(user['id']) == member.id, self.get_ranks(ctx, arg)))
        print(rank)
        if arg is None:
            await ctx.channel.send("{1} global power level is {0}".format(self.get_level(rank), whose))
        elif arg in [word.word for word in self.words]:
            await ctx.channel.send("{2} {0} is level {1}".format(arg, rank[arg], whose))

    def get_ranks(self, ctx, arg=None): 
        guild = str(ctx.message.guild.id)
        sql = "SELECT * FROM hmm_stats WHERE guild=?"
        users = []
        self.c.execute(sql, (guild, ))
        users = self.c.fetchall()

        for user in users:
            if not ctx.message.guild.get_member(int(user['id'])):
                users.remove(user)

        if arg:
            users.sort(key=lambda user: user[arg], reverse=True)
        else:
            users.sort(key=lambda user: self.get_level(user), reverse=True)
        return users

    def load_json(self, member):
        member_id = str(member.id)
        guild_id = str(member.guild.id)
        filename = "cogs/hmm/roles/" + guild_id + "/" + member_id + ".json"
        stats = None
        if os.path.exists(filename):
            with open(filename, "r") as f:
                js = f.read()
                js = json.loads(js)
                print(js)
                if "stats" in js:
                    stats = js["stats"]
        else:
            return
        for key in stats.keys():
            if key in [word.word for word in self.words]:
                print("setting {} to {}".format(key, stats[key]))
                self.update_user(member, key, (stats[key]))

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
        fw_guild = await self.bot.fetch_guild(futureworld)

        emoji = discord.utils.get(fw_guild.emojis, name=(word.emoji))
        if emoji:
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
        # check each level
        stats = [int(user[stat]) for stat in user.keys() if stat in [word.word for word in self.words]]
        if len(stats) > 0:
            overall_level = sum(stats)
        else:
            overall_level = 0
        return overall_level

    async def level_up(self, member, word, channel):
        user = self.load_user_stats(member)
        lvl = user[word.word] + 1
        print(user)

        overall_level = self.get_level(user)

        if lvl % 25 == 0 and lvl > 0 and (lvl % 50 == 0 or lvl < 100) or lvl == 10:
            await channel.send("Congrats, {0.mention}, you have advanced to {1} level {2}!".format(member, word.word, lvl))

        if overall_level % 50 == 0 and overall_level > 0:
            await channel.send("Congrats, {0.mention}, you have reached an overall power level of {2}!!".format(member, word.word, overall_level))

        self.update_user(member, word.word, lvl)

    def update_user(self, member, word, lvl):
        # refresh user 
        self.load_user_stats(member)
        member_id = str(member.id)
        sql = """
            UPDATE hmm_stats
            SET {0}=?
            WHERE id=? AND guild=?;
        """.format(word)
        self.c.execute(sql, (int(lvl), str(member.id), str(member.guild.id),))
        self.conn.commit()


    def load_user_stats(self, member):
        sql = "SELECT * FROM hm_stats WHERE (id=? and guild=?)"
        self.c.execute(sql, (str(member.id), str(member.guild.id),))
        result = self.c.fetchone()
        if result:
            return result
        else:
            self.add_new_user_to_db(member)
            return self.load_user_stats(member)

    def add_new_user_to_db(self, member):
        sql = "INSERT INTO hmm_stats (name, id, guild) VALUES (?, ?, ?)"
        self.c.execute(sql, (member.name, str(member.id), member.guild.id))
        self.conn.commit()


def setup(bot):
    bot.add_cog(Hmm(bot))
