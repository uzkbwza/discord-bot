from discord.ext import commands
import re
import discord
import asyncio

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
        Word("hmm",  r"\bh+(r+)?m+"),
        Word("mmh",  r"\bm+(r+)?h+"),
        Word("perhaps", r"\b(per|may)haps"),
        Word("aaaahhhh",  r"\ba+((r+)?g+)?h+\b", emoji="aaahhh"),
        Word("ok", r"\bo+k+((a+y+)|(ie+)|(ey))?\b"),
        Word("choon", r"\bhttps://clyp.it/", file_extensions=["mp3", "wav", "ogg", "flac"])
    ]
    max_level = 200

    def __init__(self, bot):
        self.bot = bot
        print("loaded hmm")

    @commands.Cog.listener()
    async def on_message(self, message):   
        if message.author == self.bot.user:
            return         
        # check message for each trigger
        for word in self.words:
            if self.word_matches_message(word, message):
                await self.bot.wait_until_ready()
                print ("leveling user {0} for:  \"{1}\"".format(message.author.name, message.content))
                await self.level_user_for_word(word, message)

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
        author = message.author
        await self.level_up_role(author, word)
        author_roles = self.get_roles(author, word)
        lvl = self.highest_lvl(author_roles)
        if lvl % 25 == 0 and lvl > 0 and (lvl % 50 == 0 or lvl < 100) or lvl == 10:
            await message.channel.send("Congrats, {0.mention}, you have advanced to {1} level {2}!".format(author, word.word, lvl))
        
        emoji = discord.utils.get(message.guild.emojis, name=(word.emoji))
        if emoji:
            await message.add_reaction(emoji)
            
    def choose_role_color(self, lvl):
        if lvl >= 200:
            return discord.Color.purple()
        if lvl >= 150:
            return discord.Color.dark_blue()
        if lvl >= 100:
            return discord.Color.gold()
        if lvl >= 75:
            return discord.Color.dark_gold()
        if lvl >= 50:
            return discord.Color.blue()
        if lvl >= 25:
            return discord.Color.red()
        if lvl >= 10:
            return discord.Color.teal()
        if lvl >= 5:
            return discord.Color.dark_red()
        if lvl >= 1:
            return discord.Color.dark_magenta()
        return discord.Color.default()
    
    def get_roles(self, guild_or_member, word):
        # matches for "<word> lvl <level>"
        print("getting roles for {0} associated with {1}".format(word.rolename, guild_or_member.name))
        return [role for role in guild_or_member.roles if re.fullmatch(word.rolename +r"\d+", role.name)] 

    async def level_up_role(self, member, word):
        user_roles = self.get_roles(member, word)
        guild_roles = self.get_roles(member.guild, word)
        # get user level
        user_lvl = self.highest_lvl(user_roles)
        # dont level up past the max level
        if user_lvl >= self.max_level:
            return
        # check and make sure next hmm lvl exists
        guild_lvl = self.highest_lvl(guild_roles)
        if not self.lvl_exists(guild_roles, user_lvl + 1):
            await member.guild.create_role(
                name=word.rolename + str(user_lvl + 1),
                color=self.choose_role_color(user_lvl + 1))
        role_to_add = self.get_lvl_role(guild_roles, user_lvl + 1)
        print(role_to_add)
        await self.bot.wait_until_ready()
        # add role to member
        await member.add_roles(role_to_add)
        await asyncio.sleep(0.5)
        # update user roles with the latest one added
        await self.remove_extras(member, word)

        
    def highest_lvl(self, roles):
        highest = 0
        for role in roles:
            role_level = role.name.split(' ')[-1]
            if int(role_level) > highest:
                highest = int(role_level)
        return highest
    
    async def remove_extras(self, member, word):
        roles = self.get_roles(member, word)
        highest = self.highest_lvl(roles)
        for role in roles:
            role_level = role.name.split(' ')[-1]
            if int(role_level) < highest:
                await member.remove_roles(role)

    def lvl_exists(self, roles, lvl):
        print([role.name.split(' ')[-1] for role in roles])
        for role in roles:
            role_level = role.name.split(' ')[-1]
            if int(role_level) == lvl:
                print("role lvl {} DOES exist!".format(lvl))
                return True
        print("role lvl {} DOES NOT exist!".format(lvl))
        return False
    
    def get_lvl_role(self, roles, lvl):
        if self.lvl_exists(roles, lvl):
            for role in roles:
                role_level = role.name.split(' ')[-1]
                if int(role_level) == lvl:
                    return role
        return None

def setup(bot):
    bot.add_cog(Hmm(bot))
