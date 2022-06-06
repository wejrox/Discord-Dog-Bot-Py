from typing import Union

from disnake import Member
from disnake.ext.commands import Context
from peewee import IntegerField, AutoField, CharField, BooleanField

from orm.fields.repeating_integer_field import RepeatingIntegerField
from orm.models.base_model import BaseModel


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
                                                 help_text="Unique member identifiers for those that voted yes, "
                                                           "comma separated.")
    no_votes: list[int] = RepeatingIntegerField(default=[],
                                                help_text="Unique member identifiers for those that voted no, "
                                                          "comma separated.")
    timed_out: bool = BooleanField(default=False,
                                   help_text="Whether this dog act sat idle for too long and has been cancelled.")
    found_guilty: bool = BooleanField(default=False,
                                      help_text="Whether the target was found guilty of being a dog.")

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
        If the vote count reaches the threshold, this finds the target guilty.

        :param author: Discord Member to be added to the 'yes' list.
        """
        self._clear_votes_for_author(author.id)
        self.yes_votes.append(author.id)
        if len(self.yes_votes) >= self.required_votes:
            self.found_guilty = True
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
                f"Who agrees that {target_member.mention} was really a :dog: for '{self.allegation}'?\n"
                f"Votes required on one side for a verdict: {self.required_votes}\n"
                f"Current votes: "
                f":dog: Guilty - {len(self.yes_votes)}, "
                f":no_entry_sign: Not Guilty - {len(self.no_votes)}")

    async def create_outcome_message(self, context: Context) -> str:
        """
        Generates a message indicating to the reader what the outcome was of the dog act trial.

        :return: Whether the target is guilty or innocent.
        """
        reporter_member = await context.guild.get_or_fetch_member(self.reporter)
        target_member = await context.guild.get_or_fetch_member(self.target)
        if self.found_guilty:
            return f"{target_member.mention} has been found guilty of being a :dog: for '{self.allegation}'!"
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

    def create_history_summary(self) -> str:
        """
        Creates a historical summary for this dog act, to show what the main outcomes of the act were.

        :return: A summary of the outcome of this dog act.
        """
        if self.found_guilty:
            verdict = "Guilty"
        elif self.timed_out:
            verdict = "Timed Out"
        else:
            verdict = "Not Guilty"
        return (f"**Verdict**: {verdict}"
                f", **Guilty votes**: {len(self.yes_votes)}"
                f", **Not Guilty votes**: {len(self.no_votes)}"
                f", **Allegation**: {self.allegation}")

    def _clear_votes_for_author(self, author: int) -> None:
        """
        Removes all votes previously made by the provided author from any relevant lists.
        Doesn't update the database.

        :param author: Discord Member to be removed.
        """
        if author in self.yes_votes:
            self.yes_votes.remove(author)
        if author in self.no_votes:
            self.no_votes.remove(author)
