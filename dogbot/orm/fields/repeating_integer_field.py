from typing import Union

from peewee import Field


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
