
    @triad.command(pass_context=True)
    async def test(self, ctx):
        player = ctx.message.author
        gameState = self.UserGameStateCheck(player.id)
        await self.OutputOpenBoard(ctx.message.channel, gameState[1])