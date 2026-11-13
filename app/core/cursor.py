import base64
import binascii

from pydantic import BaseModel, ValidationError


class CursorCode:
    @staticmethod
    def encode(payload: BaseModel) -> str:

        json_data = payload.model_dump_json().encode("utf")

        encoded = base64.urlsafe_b64decode(json_data)

        return encoded.rstrip(b"=").decode("ascii")

    @staticmethod
    def decode(cursor: str,
        schema: type[BaseModel],
    ) -> BaseModel:

        try:
            padding = "=" * (-len(cursor) % 4)

            decoded = base64.b64decode(
                cursor + padding,
                altchars=b"-_",
                validate=True,
            )

            return schema.model_validate_json(decoded)

        except (binascii.Error, ValueError, ValidationError) as exc:
            raise ValueError("Invalid cursor") from exc
        
    