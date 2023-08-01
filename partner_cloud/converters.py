#
# Copyright (C) 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#

"""Data converter using Pydantic JSON conversion."""

import json
from pydantic_core import to_jsonable_python
from temporalio import workflow
from typing import Any, Optional, Type
from temporalio.api.common.v1 import Payload
from temporalio.converter import (
    CompositePayloadConverter,
    DataConverter,
    DefaultPayloadConverter,
    JSONPlainPayloadConverter,
)

with workflow.unsafe.imports_passed_through():
    from pydantic import BaseModel


class PydanticJSONPayloadConverter(JSONPlainPayloadConverter):
    """Pydantic JSON payload converter.

    This extends the JSONPlainPayloadConverter to allow converting
    pydantic objects to json as well.

    Note: this is taken from the temporal.io python examples, however
    it has been updated to use the to_jsonable_python which is the
    preferred method for pydantic 2.
    """

    def to_payload(self, value: Any) -> Optional[Payload]:
        """Convert all values with Pydantic encoder or fail.

        Like the base class, we fail if we cannot convert. This payload
        converter is expected to be the last in the chain, so it can fail if
        unable to convert.
        """
        # We let JSON conversion errors be thrown to caller
        if isinstance(value, BaseModel):
            return super().to_payload(to_jsonable_python(value))
        else:
            return super().to_payload(value)


class PydanticPayloadConverter(CompositePayloadConverter):
    """Payload converter that replaces Temporal JSON conversion with Pydantic
    JSON conversion.
    """

    def __init__(self) -> None:
        super().__init__(
            *(
                c
                if not isinstance(c, JSONPlainPayloadConverter)
                else PydanticJSONPayloadConverter()
                for c in DefaultPayloadConverter.default_encoding_payload_converters
            )
        )


pydantic_data_converter = DataConverter(
    payload_converter_class=PydanticPayloadConverter
)