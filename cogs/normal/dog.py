from typing import Union

import disnake
from disnake import Member
from disnake.ext import commands
from disnake.ext.commands import Context
from peewee import SqliteDatabase, Model, IntegerField, CharField, BooleanField, AutoField, Field

# Store a reference to the database used by this bot.
db = SqliteDatabase("database/dog_history.db")


class RepeatingIntegerField(Field):
    """
    A simple repeating integer field, which stores the data as a comma separated string on insertion.
    """
    field_type = "REPEATING_INT"

    def db_value(self, value: list[int]) -> str:
        """
        Transforms the incoming list of integers into a comma separated string for storage.
        This is automatically applied when changes are saved to the database.

        :param value: Integers to transform.
        :return: A comma separated string representing the integers provided.
        """
        return ",".join(map(str, value))

    def python_value(self, value: Union[str, int]) -> list[int]:
        """
        Transforms the retrieved comma separated string into a list of integers for use within code.
        This is automatically applied when values are retrieved from the database.

        :param value: A comma separated string representing the integer list desired.
        :return: The integers within the string as a list, delimited by commas.
        """
        if not value:
            return []

        # Upon retrieval from the database, if there's only one value in the list e.g. "1234",
        # it is automatically changed into an int by Python magic. In that case, just return it since it's done what we
        # want already.
        if type(value) is int:
            return [value]

        split_values = value.split(",")
        return list(map(lambda str_value: int(str_value), split_values))


class BaseModel(Model):
    class Meta:
        """
        Tell the model to use the db defined at the top of the file.
        """
        database = db


class DogAct(BaseModel):
    """
    Represents an instance in which users cast votes to determine whether a specific act should be considered dog.
    """
    act_id = AutoField()
    message_id: int = IntegerField(null=True, help_text="Unique identifier for the bot message that this relates to.")
    reporter: int = IntegerField(help_text="Who it was that filed this report against the target.")
    target: int = IntegerField(help_text="The user accused of being a dog.")
    allegation: str = CharField(
        help_text="The reason provided by the reporter as to why they should be considered a dog.")
    required_votes: int = IntegerField(
        help_text="How many votes are required in order for this dog act to be finalised for either outcome.")
    yes_votes: list[int] = RepeatingIntegerField(default=[],
                                                 help_text="Unique member identifiers for those that voted yes, comma separated.")
    no_votes: list[int] = RepeatingIntegerField(default=[],
                                                help_text="Unique member identifiers for those that voted no, comma separated.")
    timed_out: bool = BooleanField(default=False,
                                   help_text="Whether this dog act sat idle for too long and has been cancelled.")

    def set_message_id(self, message_id: int) -> None:
        """
        Updates the message id that is attached to this dog act.

        :param message_id: Unique id of the Discord message that is attached to this dog act.
        """
        self.message_id = message_id
        self.save()

    def add_new_yes_vote(self, author: Member) -> None:
        """
        Updates the vote for the provided author to be a 'yes' vote.

        :param author: Discord Member to be added to the 'yes' list.
        """
        self._clear_votes_for_author(author.id)
        self.yes_votes.append(author.id)
        self.save()

    def add_new_no_vote(self, author: Member) -> None:
        """
        Updates the vote for the provided author to be a 'no' vote.

        :param author: Discord Member to be added to the 'no' list.
        """
        self._clear_votes_for_author(author.id)
        self.no_votes.append(author.id)
        self.save()

    def time_out(self) -> None:
        """
        Times out the current dog act.
        """
        self.timed_out = True
        self.save()

    def vote_outcome(self) -> Union[bool, None]:
        """
        Determines whether the voting has reached a definitive outcome of Guilty or Not Guilty.

        :returns: False when Not Guilty or timed out, True when Guilty, None when not enough votes have been cast.
        """
        if len(self.no_votes) >= self.required_votes or self.timed_out:
            return False
        elif len(self.yes_votes) >= self.required_votes:
            return True
        else:
            return None

    async def create_updated_dog_act_message(self, context: Context) -> str:
        """
        Generates a message detailing information about this dog acct report, including the current status of voting.

        :returns: An up-to-date representation of the status of this dog act.
        """
        reporter_member = await context.guild.get_or_fetch_member(self.reporter)
        target_member = await context.guild.get_or_fetch_member(self.target)
        return (f"Whoah there {reporter_member.mention}, that's a big claim!\n"
                f"Who agrees that {target_member.mention} was really a dog for '{self.allegation}'?\n"
                f"Votes required on one side for a verdict: {self.required_votes}\n"
                f"Current votes: Guilty - {len(self.yes_votes)}, Not Guilty - {len(self.no_votes)}")

    async def create_outcome_message(self, context: Context) -> str:
        """
        Generates a message indicating to the reader what the outcome was of the dog act trial.

        :return: Whether the target is guilty or innocent.
        """
        reporter_member = await context.guild.get_or_fetch_member(self.reporter)
        target_member = await context.guild.get_or_fetch_member(self.target)
        if self.vote_outcome():
            return f"{target_member.mention} has been found guilty of being a dog for '{self.allegation}'!"
        elif self.timed_out:
            return f"{target_member.mention} has been found innocent due to lack of voter participation!"
        else:
            return f"{target_member.mention} has been found innocent! Shame on {reporter_member.mention}"

    async def create_detailed_outcome_message(self, context: Context) -> str:
        """
        Creates a detailed outcome message containing information about the trial.
        Shouldn't be sent to the server as it's not in a nice to read format.

        :returns: Information about the dog act.
        """
        yes_voters = await context.guild.get_or_fetch_members(self.yes_votes)
        no_voters = await context.guild.get_or_fetch_members(self.no_votes)

        def get_voter_name(user: Member):
            return user.name

        guilty_voters: list[str] = list(map(get_voter_name, yes_voters))
        not_guilty_voters: list[str] = list(map(get_voter_name, no_voters))

        return (f"Dog act finalised. "
                f"Verdict: {await self.create_outcome_message(context)}. "
                f"Guilty voters: {guilty_voters}, Not guilty voters: {not_guilty_voters}")

    def _clear_votes_for_author(self, author: int) -> None:
        """
        Removes all votes previously made by the provided author from any relevant lists.
        Doesn't update the database.

        :param author: Discord Member to be removed.
        """
        if author in self.yes_votes:
            self.yes_votes.remove(author)
        if author in self.yes_votes:
            self.yes_votes.remove(author)


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
    async def yes(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        """
        Generates the 'yes' option. Clicking this button causes the clicker to be added to the 'yes' votes list.
        To avoid adding the same user multiple times, their votes are cleared before adding them to the correct list.
        Once the vote has been counted, the view is exited, and the message can be updated as required.

        :param _: Unused parameter for the button the user can click.
        :param interaction: Details about the interaction that occurred with the button.
        """
        self.dog_act.add_new_yes_vote(interaction.author)
        self.stop()

    @disnake.ui.button(label="Not a dog", style=disnake.ButtonStyle.blurple)
    async def no(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        """
        Generates the 'no' option. Clicking this button causes the clicker to be added to the 'no' votes list.

        :param _: Unused parameter for the button the user can click.
        :param interaction: Details about the interaction that occurred with the button.
        """
        self.dog_act.add_new_no_vote(interaction.author)
        self.stop()

    async def on_timeout(self) -> None:
        """
        Overrides what to do when the view times out.
        On Timeout, the dog act is updated, and we cancel waiting.
        """
        self.dog_act.time_out()
        self.stop()


class Dog(commands.Cog, name="dog"):
    """
    Commands for users to interact with the dogging framework.
    Users can mark targets as dogs, giving an optional reason for why it is true.
    If enough other users agree that the target did in fact dog as outlined, the target will be branded a dog and have
    a mark added against their name.
    """
    votes_to_complete: int = 2

    def __init__(self, bot):
        db.connect()
        db.create_tables([DogAct])
        db.close()
        self.bot = bot

    # Here you can just add your own commands, you'll always need to provide "self" as first parameter.
    @commands.command(
        name="dog",
        description="Reports someone for dogging."
    )
    async def dog(self, context: Context,
                  target: Member, *, reason: str = "being a dog, idk") -> None:
        """
        Tag a user and (optionally) provide a reason they should be found guilty of being a dog.

        Reports a user for dogging, with an optionally provided reason.
        Trial by Jury dictates the outcome, and requires at least 2 votes in either direction.
        If the trial goes for more than 5 minutes, the defendant is presumed innocent by lack of participation.

        :param target: The user who dogged.
        :param context: The application command interaction.
        :param reason: Why what they did was considered a dog move.
        """
        member = await context.guild.get_or_fetch_member(target.id)

        # Initialise the dog act, recording details about the message.
        dog_act = DogAct.create(reporter=context.author.id, target=member.id, allegation=reason,
                                required_votes=self.votes_to_complete)

        # Continue waiting for user input until an outcome has been reached.
        message = None
        while dog_act.vote_outcome() is None:
            # Set the embed to the current status of the trial.
            embed = disnake.Embed(description=await dog_act.create_updated_dog_act_message(context),
                                  colour=0x9C84EF)
            choices = DogChoice(dog_act)

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

        print(await dog_act.create_detailed_outcome_message(context))


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
def setup(bot):
    bot.add_cog(Dog(bot))
