# Here we name the cog and create a new class for the cog.

import disnake
from disnake import Member
from disnake.ext import commands
from disnake.ext.commands import Context


class DogAct:
    """
    Represents an instance in which users have voted whether a specific act should be considered dog.

    Attributes
    ----------
    message_id: :class:`int`
        Unique identifier for the bot message that this relates to.
    reporter: :class:`Member`
        Who it was that filed this report.
    target: :class:`Member`
        Who it is that allegedly dogged.
    allegation: :class:`str`
        Reason that the reporter said they are guilty.
    yes_votes: :class:`list[Member]`
        Unique member identifiers for those that voted yes.
    no_votes: :class:`Member`
        Unique member identifiers for those that voted no.
    required_votes: :class:`int`
        How many votes are required in order for this DogAct to be finalised in either direction.
    """

    # Unique identifier for the bot message that this relates to.
    message_id: int

    # Who it was that reported this person.
    reporter: Member

    # Who it is that allegedly dogged.
    target: Member

    # Reason that the reporter said they are guilty.
    allegation: str

    # Unique member identifiers for those that voted yes.
    yes_votes: list[Member] = []

    # Unique member identifiers for those that voted no.
    no_votes: list[Member] = []

    # How many votes are required in order for this DogAct to be finalised in either direction.
    required_votes: int

    def __init__(self, reporter: Member, target: Member, allegation: str,
                 message_id: int = -1, required_votes: int = 1):
        self.reporter = reporter
        self.target = target
        self.allegation = allegation
        self.message_id = message_id
        self.required_votes = required_votes

    def vote_outcome(self):
        if len(self.no_votes) >= self.required_votes:
            return False
        elif len(self.yes_votes) >= self.required_votes:
            return True
        else:
            return None

    def create_updated_dog_act_message(self):
        """
        Generates a message detailing information about this dog acct report, including the current status of voting.
        """
        return (f"Whoah there {self.reporter.mention}, that's a big claim!\n"
                f"Who agrees that {self.target.mention} was really a dog for '{self.allegation}'?\n"
                f"Current votes: Guilty - {len(self.yes_votes)}, Not Guilty - {len(self.no_votes)}")


class DogChoice(disnake.ui.View):
    """
    Handles what to do when a discord member interacts with the options presented within the message from the bot.
    The two options available are essentially an 'agree' and 'disagree' selection, which update the dog act being
    processed.

    Users are able to swap their votes as they see fit, until voting closes.
    Once the required number of votes for a particular option have been cast, a decision is reached and the choices end.
    If there aren't enough choices by the duration of _timeout_sec then the target is presumed innocent.
    """
    _timeout_sec: int = 5 * 60

    def __init__(self, related_dog_act: DogAct):
        super().__init__(timeout=self._timeout_sec)
        self.dog_act = related_dog_act

    @disnake.ui.button(label="Definitely a dog", style=disnake.ButtonStyle.blurple)
    async def yes(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.clear_votes_for_author(interaction.author)
        self.dog_act.yes_votes.append(interaction.author)

        await self.finish_if_complete()

    @disnake.ui.button(label="Not a dog", style=disnake.ButtonStyle.blurple)
    async def no(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.clear_votes_for_author(interaction.author)
        self.dog_act.no_votes.append(interaction.author)

        await self.finish_if_complete()

    def clear_votes_for_author(self, author: Member):
        if author in self.dog_act.yes_votes:
            self.dog_act.yes_votes.remove(author)
        if author in self.dog_act.no_votes:
            self.dog_act.no_votes.remove(author)

    async def finish_if_complete(self):
        # if self.dog_act.vote_outcome() is not None:
        self.stop()


class Dog(commands.Cog, name="dog-slash"):
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
        Reports a target user for dogging, with a provided reason. Trial by Jury dictates the outcome

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
            if message is None:
                message = await context.send(embed=embed, view=choices)

                # Assign the newly created message to our records for future reference.
                dog_act.message_id = message.id
            else:
                await message.edit(embed=embed, view=choices)

            # Don't do anything until an outcome is reached.
            await choices.wait()

        if dog_act.vote_outcome():
            embed = disnake.Embed(description=f"{dog_act.target.mention} has been found guilty of being a dog!")
        else:
            embed = disnake.Embed(description=f"{dog_act.target.mention} is innocent! "
                                              f"Shame on {dog_act.reporter.mention}")

        await message.edit(embed=embed, view=None)


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
def setup(bot):
    bot.add_cog(Dog(bot))
