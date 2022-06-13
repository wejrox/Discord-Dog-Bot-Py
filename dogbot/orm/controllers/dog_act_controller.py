from typing import Union

from disnake.ext.commands import Context

from orm.models.dog_act import DogAct
from orm.models.member import Member
from orm.models.votes import YesVote, NoVote


class DogActController:
    """
    Controller for the provided Dog Act model, containing helper methods to update and modify it.
    The controller pattern has been used to avoid circular imports, and centralise the logic for handling dog acts.
    """
    dog_act: DogAct

    def __init__(self, dog_act: DogAct):
        """
        :param dog_act: Dog act that this controller will be focused on.
        """
        self.dog_act = dog_act

    def set_message_id(self, message_id: int) -> None:
        self.dog_act.message_id = message_id

    def add_new_yes_vote(self, author: int) -> None:
        """
        Updates the vote for the provided author to be a 'yes' vote.
        If the vote count reaches the threshold, this finds the target guilty.

        :param author: Discord Member to be added to the 'yes' list.
        """
        # Get or create returns the resultant entry, and a bool indicating whether it was existent.
        # we only want the result.
        member = Member.get_or_create(id=author)[0]
        self._clear_votes_for_author(member)
        YesVote.create(dog_act=self.dog_act.id, member=member.id)
        self.update_guilt()

    def add_new_no_vote(self, author: int) -> None:
        """
        Updates the vote for the provided author to be a 'no' vote.

        :param author: Discord Member to be added to the 'no' list.
        """
        member = Member.get_or_create(id=author)[0]
        self._clear_votes_for_author(member)
        NoVote.create(dog_act=self.dog_act.id, member=member.id)

    def update_guilt(self) -> None:
        """
        Updates the record of guilt for this dog act based on whether the yes vote count is high enough.
        """
        yes_vote_count = YesVote.select().where(YesVote.dog_act == self.dog_act).count()
        if yes_vote_count >= self.dog_act.required_votes:
            self.dog_act.found_guilty = True

    def reset_voting(self) -> None:
        """
        Reset the voting on this dog act.
        """
        YesVote.delete().where(YesVote.dog_act == self.dog_act.id).execute()
        NoVote.delete().where(NoVote.dog_act == self.dog_act.id).execute()
        self.dog_act.found_guilty = False
        self.dog_act.timed_out = False

    def begin_appeal_and_save(self, reason: str) -> None:
        """
        Reinitialises this dog act, marking it as an appeal and providing the reason it's being appealed.

        :param reason: Why this appeal should be considered.
        """
        self.dog_act.appeal_attempted = True
        self.dog_act.appeal_reason = reason

        # An appeal attempt needs to be saved straight away, or multiple could occur at the same time!
        self.dog_act.save()

    def vote_outcome(self) -> Union[bool, None]:
        """
        Determines whether the voting has reached a definitive outcome of Guilty or Not Guilty.

        :returns: False when the vote fails or timed out,
                  True when the vote succeeds,
                  None when not enough votes have been cast.
        """
        yes_vote_count = YesVote.select().where(YesVote.dog_act == self.dog_act).count()
        no_vote_count = NoVote.select().where(NoVote.dog_act == self.dog_act).count()
        if no_vote_count >= self.dog_act.required_votes or self.dog_act.timed_out:
            return False
        elif yes_vote_count >= self.dog_act.required_votes:
            return True
        else:
            return None

    async def create_updated_dog_act_message(self, context: Context) -> str:
        """
        Generates a message detailing information about this dog acct report, including the current status of voting.

        :param context: Discord context about the user interaction that lead to this method being called.
        :returns: An up-to-date representation of the status of this dog act.
        """
        yes_vote_count = YesVote.select().where(YesVote.dog_act == self.dog_act).count()
        no_vote_count = NoVote.select().where(NoVote.dog_act == self.dog_act).count()
        reporter_member = await context.guild.get_or_fetch_member(self.dog_act.reporter)
        target_member = await context.guild.get_or_fetch_member(self.dog_act.target)

        if self.dog_act.appeal_attempted:
            introduction = f"Someone is appealing this dog act on the grounds '{self.dog_act.appeal_reason}'.\n"
        else:
            introduction = f"Whoah there {reporter_member.mention}, that's a big claim!\n"

        return (introduction +
                f"Who agrees that {target_member.mention} was really a :dog: for '{self.dog_act.allegation}'?\n"
                f"Votes required on one side for a verdict: {self.dog_act.required_votes}\n"
                f"Current votes: "
                f":dog: Guilty - {yes_vote_count}, "
                f":no_entry_sign: Not Guilty - {no_vote_count}")

    async def create_outcome_message(self, context: Context) -> str:
        """
        Generates a message indicating to the reader what the outcome was of the dog act trial.

        :param context: Discord context about the user interaction that lead to this method being called.
        :return: Whether the target is guilty or innocent.
        """
        reporter_member = await context.guild.get_or_fetch_member(self.dog_act.reporter)
        target_member = await context.guild.get_or_fetch_member(self.dog_act.target)

        # If we're in the middle of an appeal, timing out isn't a good thing.
        if self.dog_act.appeal_attempted:
            timeout_text = "Appeal denied due to lack of participation!"
        else:
            timeout_text = f"{target_member.mention} has been found innocent due to lack of voter participation!"

        if self.dog_act.found_guilty:
            return f"{target_member.mention} has been found guilty of being a :dog: for '{self.dog_act.allegation}'!"
        elif self.dog_act.timed_out:
            return timeout_text
        else:
            return f"{target_member.mention} has been found innocent! Shame on {reporter_member.mention}"

    def _clear_votes_for_author(self, author: Member) -> None:
        """
        Removes all votes previously made by the provided author from any relevant lists.
        Doesn't update the database.

        :param author: Discord Member to be removed.
        """
        YesVote.delete().where((YesVote.dog_act == self.dog_act.id) & (YesVote.member == author.id)).execute()
        NoVote.delete().where((NoVote.dog_act == self.dog_act.id) & (NoVote.member == author.id)).execute()

    async def create_detailed_outcome_message(self, context: Context) -> str:
        """
        Creates a detailed outcome message containing information about the trial.
        Shouldn't be sent to the Discord Server as it's not in a nice to read format.

        :param context: Discord context about the user interaction that lead to this method being called.
        :returns: Information about the dog act.
        """
        yes_votes_db_list: [int] = []
        for yes_votes_db in YesVote.select().where(YesVote.dog_act == self.dog_act.id).iterator():
            yes_votes_db_list.append(yes_votes_db.member.id)
        no_votes_db_list: [int] = []
        for no_votes_db in NoVote.select().where(NoVote.dog_act == self.dog_act.id).iterator():
            no_votes_db_list.append(no_votes_db.member.id)
        yes_voters = await context.guild.get_or_fetch_members(yes_votes_db_list)
        no_voters = await context.guild.get_or_fetch_members(no_votes_db_list)

        def get_voter_name(user: Member):
            return user.name

        guilty_voters: list[str] = list(map(get_voter_name, yes_voters))
        not_guilty_voters: list[str] = list(map(get_voter_name, no_voters))

        return (f"Dog act {self.dog_act.id} finalised. "
                f"Verdict: {await self.create_outcome_message(context)}. "
                f"Guilty voters: {guilty_voters}, Not guilty voters: {not_guilty_voters}")

    def create_history_summary(self) -> str:
        """
        Creates a historical summary for this dog act, to show what the main outcomes of the act were.

        :return: A summary of the outcome of this dog act.
        """
        yes_vote_count = YesVote.select().where(YesVote.dog_act == self.dog_act).count()
        no_vote_count = NoVote.select().where(NoVote.dog_act == self.dog_act).count()

        if self.dog_act.found_guilty:
            verdict = "Guilty"
        elif self.dog_act.timed_out:
            verdict = "Timed Out"
        else:
            verdict = "Not Guilty"

        if self.dog_act.appeal_attempted and self.dog_act.found_guilty:
            appeal_text = "(appeal failed)"
        else:
            appeal_text = ""

        return (f"**ID**: {self.dog_act} {appeal_text},"
                f" **Verdict**: {verdict}"
                f", **Guilty votes**: {yes_vote_count}"
                f", **Not Guilty votes**: {no_vote_count}"
                f", **Allegation**: {self.dog_act.allegation}")
