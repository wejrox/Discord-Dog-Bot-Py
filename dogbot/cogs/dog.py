import disnake
from disnake import Member
from disnake.ext import commands
from disnake.ext.commands import Context
from peewee import fn

from dogbot.orm.database import dog_bot_database_proxy
from dogbot.orm.models.dog_act import DogAct


class DogChoice(disnake.ui.View):
    """
    Handles what to do when a discord member interacts with the options presented within the message from the bot.
    The two options available are essentially an 'agree' and 'disagree' selection, which update the dog act being
    processed.

    Users are able to swap their votes as they see fit, until voting closes.
    Once the required number of votes for a particular option have been cast, a decision is reached and the choices end.
    If there aren't enough choices by the duration of _timeout_sec then the target is presumed innocent.
    """

    def __init__(self, related_dog_act: DogAct, timeout_sec: int = 5 * 60):
        """
        :param related_dog_act: Dog act that is being voted on by this Dog choice.
        :param timeout_sec: Seconds to wait before this view times out and is no longer valid.
        """
        super().__init__()
        self.dog_act = related_dog_act
        self.timeout = timeout_sec

    @disnake.ui.button(label="Definitely a dog", style=disnake.ButtonStyle.blurple)
    async def yes_button(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        """
        Generates the 'yes' option. Clicking this button causes the clicker to be added to the 'yes' votes list.
        To avoid adding the same user multiple times, their votes are cleared before adding them to the correct list.
        Once the vote has been counted, the view is exited, and the message can be updated as required.

        :param _: Unused parameter for the button the user can click.
        :param interaction: Details about the interaction that occurred with the button.
        """
        self.dog_act.add_new_yes_vote(interaction.author)

        # When a user initiates a click, we need to do something as a result, or they never receive anything back.
        # Defer prevents them from receiving the 'Interaction failed' message.
        await interaction.response.defer()
        self.stop()

    @disnake.ui.button(label="Not a dog", style=disnake.ButtonStyle.blurple)
    async def no_button(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        """
        Generates the 'no' option. Clicking this button causes the clicker to be added to the 'no' votes list.

        :param _: Unused parameter for the button the user can click.
        :param interaction: Details about the interaction that occurred with the button.
        """
        self.dog_act.add_new_no_vote(interaction.author)

        # When a user initiates a click, we need to do something as a result, or they never receive anything back.
        # Defer prevents them from receiving the 'Interaction failed' message.
        await interaction.response.defer()
        self.stop()

    async def on_timeout(self) -> None:
        """
        Overrides what to do when the view times out.
        On Timeout, the dog act is updated, and we cancel waiting.
        """
        self.dog_act.time_out()
        self.stop()


async def send_top_dogs(context: Context, tag_dogs: bool) -> None:
    """
    Generates and sends the dog leaderboard for the current standings.
    :param context: Discord context for sending messages and retrieving member details.
    :param tag_dogs: Whether to explicitly tag the dogs in the message.
    """
    top_dogs: list[str] = []
    for dog_act in DogAct.select(DogAct.target, fn.Count(DogAct.target).alias('count')).where(
            (DogAct.guild_id == context.guild.id) & (DogAct.found_guilty == 1)).group_by(DogAct.target).order_by(
        'count desc').limit(3):
        top_dog = await context.guild.get_or_fetch_member(dog_act.target)
        if tag_dogs:
            top_dogs.append(top_dog.mention)
        else:
            top_dogs.append(top_dog.name)

    message_rows = []
    if len(top_dogs) > 0:
        message_rows.append(f"**Worst Dogger**\n{top_dogs[0]}")
    if len(top_dogs) > 1:
        message_rows.append("")
        message_rows.append(f"**Still a dog**\n{top_dogs[1]}")
    if len(top_dogs) > 2:
        message_rows.append("")
        message_rows.append(f"**Also a dog**\n{top_dogs[2]}")

    embed = disnake.Embed(title=":dog: Worst 3 Dogs :dog:", description='\n'.join(message_rows), colour=0x9C84EF)
    await context.send(embed=embed)


class Dog(commands.Cog, name="dog"):
    """
    Commands for users to interact with the dogging framework.
    Users can mark targets as dogs, giving an optional reason for why it is true.
    If enough other users agree that the target did in fact dog as outlined, the target will be branded a dog and have
    a mark added against their name.
    """

    def __init__(self, bot):
        dog_bot_database_proxy.connect()
        dog_bot_database_proxy.create_tables([DogAct])
        dog_bot_database_proxy.close()

        self._votes_per_dog_act = bot.config.dog_act_votes
        self._dog_act_timeout_sec = bot.config.dog_act_timeout_sec

    @commands.command(
        name="dog",
        description="Reports someone for dogging."
    )
    async def dog(self, context: Context,
                  tagged_user: Member, *, reason: str = "being a dog, idk") -> None:
        """
        Tag a user and (optionally) provide a reason they should be found guilty of being a dog.

        Reports a user for dogging, with an optionally provided reason.
        Trial by Jury dictates the outcome, and requires at least 2 votes in either direction.
        If the trial goes for more than 5 minutes, the defendant is presumed innocent by lack of participation.

        :param tagged_user: The user who allegedly dogged.
        :param context: The application command interaction.
        :param reason: Why what they did was considered a dog move.
        """
        member = await context.guild.get_or_fetch_member(tagged_user.id)

        # Initialise the dog act, recording details about the message.
        dog_act = DogAct.create(reporter=context.author.id, target=member.id, allegation=reason,
                                guild_id=context.guild.id, required_votes=self._votes_per_dog_act)

        await self.vote_on_dog_act(context, dog_act)

        # Save everything that's been done to this dog_act.
        dog_act.save()

        print(await dog_act.create_detailed_outcome_message(context))

    @commands.command(
        name="dogrevote",
        description="Allows someone to request a re-vote on a specified dog act."
    )
    async def dog_revote(self, context: Context,
                         act_id: int, *, reason: str = "BOO HOO!") -> None:
        """
        Specify an act id (use the dog history command to find the id) and reason to initiate a re-vote on a dog act's
        outcome. Can only be performed once per dog act.

        :param act_id: The dog act which you want to appeal.
        :param context: The application command interaction.
        :param reason: Why the appeal should be considered.
        """
        dog_act: DogAct = DogAct.get(DogAct.act_id == act_id)

        # Only allow appeals once, unless it's the bot owner just in case are really annoyed.
        if dog_act.appeal_attempted and context.author.id not in context.bot.config.owners:
            embed = disnake.Embed(title="Don't you dare!",
                                  description="An appeal can only be attempted once per dog act.")
            await context.send(embed=embed)
            return

        dog_act.begin_appeal_and_save(reason)
        dog_act.reset_voting()
        await self.vote_on_dog_act(context, dog_act)

        # Save everything that's been done to this dog act if we didn't time out,
        # otherwise revert to the data before the re-vote (including the appeal being recorded).
        if dog_act.timed_out:
            # Reset the dog act and mark it as appeal failed.
            dog_act = DogAct.select().where(DogAct.act_id == act_id).limit(1)

        # Regardless of the outcome, save the changes.
        dog_act.save()

        print(await dog_act.create_detailed_outcome_message(context))

    async def vote_on_dog_act(self, context: Context, dog_act: DogAct):

        # Continue waiting for user input until an outcome has been reached.
        message = None
        while dog_act.vote_outcome() is None:
            # Set the embed to the current status of the trial.
            embed = disnake.Embed(description=await dog_act.create_updated_dog_act_message(context),
                                  colour=0x9C84EF)
            # Timeout after an hour (1hr * 60 min * 60 sec).
            choices = DogChoice(dog_act, timeout_sec=self._dog_act_timeout_sec)

            # Initialise the message if required, otherwise update it to match the changes made by the most recent
            # interaction.
            if message is None:
                message = await context.send(embed=embed, view=choices)

                # Assign the newly created message to our record for future reference.
                dog_act.set_message_id(message.id)
            else:
                await message.edit(embed=embed, view=choices)

            # Don't do anything until another interaction occurs.
            await choices.wait()

        embed = disnake.Embed(description=await dog_act.create_outcome_message(context))
        await message.edit(embed=embed, view=None)

    @commands.command(
        name="tagdogs",
        description="Tags the top 3 dogs on the server, and how many times they've dogged. "
                    "Rate limited to once per day."
    )
    @commands.cooldown(1, 1 * 24 * 60 * 60, commands.BucketType.user)
    async def tag_dogs(self, context: Context) -> None:
        """
        Post a message tagging the worst 3 dog offenders. Can only be used once per day, per person.
        """
        await send_top_dogs(context, True)

    @commands.command(
        name="dogs",
        description="Pastes the top 3 dogs on the server, and how many times they've dogged."
    )
    async def dogs(self, context: Context) -> None:
        """
        Post a message listing the worst 3 dog offenders.
        """
        await send_top_dogs(context, False)

    @commands.command(
        name="doghistory",
        description="Shows the dog act history for the provided Member."
    )
    async def dog_history(self, context: Context, tagged_user: Member, limit: int = 10) -> None:
        """
        Post a message listing the accusations made of the provided Member, with reasons and outcomes.
        Optionally, the maximum number of records can be specified.
        """
        if limit > 30:
            normalised_limit = 30
        else:
            normalised_limit = limit

        history: list[str] = []
        total_guilty_acts = 0
        for dog_act in DogAct.select().where(
                (DogAct.guild_id == context.guild.id) & (DogAct.target == tagged_user.id)).group_by(
            DogAct.target).order_by(
            DogAct.act_id.desc()).limit(normalised_limit):
            history.append(dog_act.create_history_summary())

            # It's fun to know how many times someone has been a dog!
            if dog_act.found_guilty:
                total_guilty_acts += 1

        embed = disnake.Embed(title=f"Dog history for {tagged_user.name}",
                              description=f"Total dog acts: **{total_guilty_acts}**\n" +
                                          "------------------\n" +
                                          '\n'.join(history),
                              colour=0x9C84EF)
        await context.send(embed=embed)


def setup(bot):
    """
    Automatically executed when this file is loaded into a bot. It adds a listener for the commands we've defined.

    :param bot: Bot to add the command listener to.
    """
    bot.add_cog(Dog(bot))
