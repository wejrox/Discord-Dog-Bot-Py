from typing import Union

import disnake
from disnake import Member
from disnake.ext import commands
from disnake.ext.commands import Context


class DogAct:
    """
    Represents an instance in which users cast votes to determine whether a specific act should be considered dog.

    :ivar yes_votes: Unique member identifiers for those that voted yes.
    :ivar no_votes: Unique member identifiers for those that voted no.
    :ivar timed_out: Whether this dog act sat idle for too long and has been cancelled.
    """

    def __init__(self, reporter: Member, target: Member, allegation: str,
                 message_id: int = -1, required_votes: int = 1):
        """
        :param reporter: Who it was that filed this report against the target.
        :param target: The user accused of being a dog.
        :param allegation: The reason provided by the reporter as to why they should be considered a dog.
        :param message_id: Unique identifier for the bot message that this relates to.
        Can't exist before a message has been sent by the bot to the server.
        :param required_votes: How many votes are required in order for this DogAct to be finalised in either direction.
        """
        self.message_id = message_id
        self.reporter = reporter
        self.target = target
        self.allegation = allegation
        self.required_votes = required_votes

        # Default values for mutable variables.
        self.yes_votes: list[Member] = []
        self.no_votes: list[Member] = []
        self.timed_out = False

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

    def add_new_yes_vote(self, author: Member) -> None:
        """
        Updates the vote for the provided author to be a 'yes' vote.

        :param author: Discord Member to be added to the 'yes' list.
        """
        self._clear_votes_for_author(author)
        self.yes_votes.append(author)

    def add_new_no_vote(self, author: Member) -> None:
        """
        Updates the vote for the provided author to be a 'no' vote.

        :param author: Discord Member to be added to the 'no' list.
        """
        self._clear_votes_for_author(author)
        self.no_votes.append(author)

    def create_updated_dog_act_message(self) -> str:
        """
        Generates a message detailing information about this dog acct report, including the current status of voting.

        :returns: An up-to-date representation of the status of this dog act.
        """
        return (f"Whoah there {self.reporter.mention}, that's a big claim!\n"
                f"Who agrees that {self.target.mention} was really a dog for '{self.allegation}'?\n"
                f"Required votes: {self.required_votes}\n"
                f"Current votes: Guilty - {len(self.yes_votes)}, Not Guilty - {len(self.no_votes)}")

    def create_outcome_message(self) -> str:
        """
        Generates a message indicating to the reader what the outcome was of the dog act trial.

        :return: Whether the target is guilty or innocent.
        """
        if self.vote_outcome():
            return f"{self.target.mention} has been found guilty of being a dog for '{self.allegation}'!"
        elif self.timed_out:
            return f"{self.target.mention} has been found innocent due to lack of voter participation!"
        else:
            return f"{self.target.mention} has been found innocent! Shame on {self.reporter.mention}"

    def create_detailed_outcome_message(self) -> str:
        """
        Creates a detailed outcome message containing information about the trial.
        Shouldn't be sent to the server as it's not in a nice to read format.

        :returns: Information about the dog act.
        """

        def get_voter_name(user: Member): return user.name

        guilty_voters: list[str] = list(map(get_voter_name, self.yes_votes))
        not_guilty_voters: list[str] = list(map(get_voter_name, self.no_votes))

        return (f"Dog act finalised. "
                f"Verdict: {self.create_outcome_message()}. "
                f"Guilty voters: {guilty_voters}, Not guilty voters: {not_guilty_voters}")

    def _clear_votes_for_author(self, author: Member) -> None:
        """
        Removes all votes previously made by the provided author from any relevant lists.

        :param author: Discord Member to be removed.
        """
        if author in self.yes_votes:
            self.yes_votes.remove(author)
        if author in self.no_votes:
            self.no_votes.remove(author)


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
        self.dog_act.timed_out = True
        self.stop()


class Dog(commands.Cog, name="dog"):
    """
    Commands for users to interact with the dogging framework.
    Users can mark targets as dogs, giving an optional reason for why it is true.
    If enough other users agree that the target did in fact dog as outlined, the target will be branded a dog and have
    a mark added against their name.
    """
    votes_to_complete: int = 2
    dog_acts: list[DogAct] = []

    def __init__(self, bot):
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
        dog_act = DogAct(reporter=context.author, target=member, allegation=reason,
                         required_votes=self.votes_to_complete)
        self.dog_acts.append(dog_act)

        # Continue waiting for user input until an outcome has been reached.
        message = None
        while dog_act.vote_outcome() is None:
            # Set the embed to the current status of the trial.
            embed = disnake.Embed(description=dog_act.create_updated_dog_act_message(),
                                  colour=0x9C84EF)
            choices = DogChoice(dog_act)

            # Initialise the message if required, otherwise update it to match the changes made by the most recent
            # interaction.
            if message is None:
                message = await context.send(embed=embed, view=choices)

                # Assign the newly created message to our records for future reference.
                dog_act.message_id = message.id
            else:
                await message.edit(embed=embed, view=choices)

            # Don't do anything until another interaction occurs.
            await choices.wait()

        embed = disnake.Embed(description=dog_act.create_outcome_message())
        await message.edit(embed=embed, view=None)

        print(dog_act.create_detailed_outcome_message())


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
def setup(bot):
    bot.add_cog(Dog(bot))
