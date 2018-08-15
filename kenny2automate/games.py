import re
import random
from itertools import accumulate
from bisect import bisect
import asyncio as a
import discord as d
from discord.ext.commands import command
from discord.ext.commands import bot_has_permissions
from .i18n import i18n

class Games(object):
	def __init__(self, bot, logger, db):
		self.bot = bot
		self.logger = logger
		self.db = db

	@command()
	async def numguess(self, ctx):
		"""Play a fun number-guessing game!"""
		self.logger.info('Games.numguess', extra={'ctx': ctx})
		guess = None
		limDn = 0
		limUp = 100
		tries = 7
		secret = random.randint(1, 100)
		await ctx.send(i18n(ctx, 'games/numguess-intro', limDn, limUp, tries))
		while guess != secret and tries > 0:
			await ctx.send(i18n(ctx, 'games/numguess-guess'))
			result = ''
			try:
				guess = await ctx.bot.wait_for('message',
					check=lambda m: m.channel == ctx.channel and re.match('^[0-9]+$', m.content),
					timeout=60.0)
			except a.TimeoutError:
				await ctx.send(i18n(ctx, 'games/numguess-timeout', 60))
				return
			guess = int(guess.content)
			if guess == secret:
				break
			elif guess < limDn or guess > limUp:
				result += i18n(ctx, 'games/numguess-oor')
			elif guess < secret:
				result += i18n(ctx, 'games/numguess-low')
				limDn = guess
			elif guess > secret:
				result += i18n(ctx, 'games/numguess-high')
				limUp = guess
			tries -= 1
			result += i18n(ctx, 'games/numguess-range', limDn, limUp, tries)
			await ctx.send(result)
		if guess == secret:
			await ctx.send(i18n(ctx, 'games/numguess-correct', tries))
		else:
			await ctx.send(i18n(ctx, 'games/numguess-oot', secret))

	#@command()
	@bot_has_permissions(manage_messages=True)
	async def memory(self, ctx):
		#raise NotImplementedError('stub')
		EMOJI_RANGES_UNICODE = (
			('\U0001F300', '\U0001F320'),
			('\U0001F330', '\U0001F335'),
			('\U0001F337', '\U0001F37C'),
			('\U0001F380', '\U0001F393'),
			('\U0001F3A0', '\U0001F3C4'),
			('\U0001F3C6', '\U0001F3CA'),
			('\U0001F3E0', '\U0001F3F0'),
			('\U0001F400', '\U0001F43E'),
			('\U0001F440', '\U0001F4F7'),
			('\U0001F4F9', '\U0001F4FC'),
			('\U0001F500', '\U0001F53C'),
			('\U0001F550', '\U0001F567'),
			('\U0001F5FB', '\U0001F5FF')
		)
		def random_emoji():
			# Weighted distribution
			count = [ord(r[-1]) - ord(r[0]) + 1 for r in EMOJI_RANGES_UNICODE]
			weights = list(accumulate(count))

			# Get one point in ranges
			point = random.randrange(weights[-1])

			# Select correct range
			emridx = bisect(weights, point)
			emr = EMOJI_RANGES_UNICODE[emridx]

			# Calculate index in range
			point_ = point
			if emridx is not 0:
				point_ = point - weights[emridx - 1]

			# Emoji
			emoji = chr(ord(emr[0]) + point_)
			return emoji

		self.logger.info('Games.memory', extra={'ctx': ctx})
		#if self.db.execute('SELECT channel_id FROM mem_channels_occupied WHERE channel_id=?', (ctx.channel.id,)).fetchone() is not None:
		#	await ctx.send("There is already a game going on in this channel!")
		#	ownerq = await self.bot.is_owner(ctx.author)
		#	if not ownerq:
		#		return
		#self.db.execute('INSERT INTO mem_channels_occupied VALUES (?)', (ctx.channel.id,))
		BLACK, QUESTION = '\u2b1b \u2753'.split(' ')
		NUMBERS = '1\u20e3 2\u20e3 3\u20e3 4\u20e3 5\u20e3 6\u20e3'.split(' ')# 7\u20e3 8\u20e3'.split(' ')
		LETTERS = '\U0001f1e6 \U0001f1e7 \U0001f1e8 \U0001f1e9 \U0001f1ea \U0001f1eb'.split(' ')# \U0001f1ec \U0001f1ed \U0001f1ee \U0001f1ef \U0001f1f0'.split(' ')
		ALETTERS = 'abcdef'#gh'
		_once = []
		board = []
		_ems = []
		for i in range(len(ALETTERS) ** 2 // 2):
			_em = random_emoji()
			while _em in _ems:
				_em = random_emoji()
			_ems.append(_em)
		for i in range(len(ALETTERS)):
			board.append([])
			for j in range(len(ALETTERS)):
				_em = random.choice(_ems)
				if _em in _once:
					_ems.remove(_em)
				else:
					_once.append(_em)
				board[i].append([_em, False])
		del _once, _ems
		def constructboard(board):
			boardmsg = QUESTION + "".join(NUMBERS) + '\n'
			for i, row in enumerate(board):
				boardmsg += LETTERS[i]
				for column in row:
					if column[-1]:
						boardmsg += column[0]
					else:
						boardmsg += BLACK
				boardmsg += '\n'
			return d.Embed(description=boardmsg)
		def checkdone(board):
			for row in board:
				for emoji, found in row:
					if not found:
						return False
			return True
		boardmsg = await ctx.send(embed=constructboard(board))
		grid1 = None
		def check_msg(msg):
			global grid1
			if msg.channel.id != ctx.channel.id:
				return False
			if not re.match('^[' + ALETTERS + ALETTERS.upper()
					+ '][1-' + str(len(ALETTERS)) + ']$', msg.content):
				return False
			if grid1 is not None and msg.content.lower() == grid1:
				return False
			gr = msg.content.lower()
			return not board[ALETTERS.index(gr[0])][int(gr[1]) - 1][-1]
		while not checkdone(board):
			grid1 = None
			msg = await ctx.bot.wait_for('message', check=check_msg)
			grid1 = msg.content.lower()
			thing1 = board[ALETTERS.index(grid1[0])][int(grid1[1]) - 1]
			thing1[-1] = True
			await msg.delete()
			await boardmsg.edit(embed=constructboard(board))
			msg = await ctx.bot.wait_for('message', check=check_msg)
			grid2 = msg.content.lower()
			thing2 = board[ALETTERS.index(grid2[0])][int(grid2[1]) - 1]
			thing2[-1] = True
			await msg.delete()
			await boardmsg.edit(embed=constructboard(board))
			if thing1[0] != thing2[0]:
				thing1[-1], thing2[-1] = False, False
				await a.sleep(2)
				await boardmsg.edit(embed=constructboard(board))
		#self.db.execute('DELETE FROM mem_channels_occupied WHERE channel_id=?', (ctx.channel.id,))
