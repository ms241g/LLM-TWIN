from loguru import logger
from typing_extensions import Annotated
from zenml import get_step_context, step

from llm_enginerring.application import utils
from llm_enginerring.domain.documents import UserDocument


@step
def get_or_create_user(user_full_name: str) -> Annotated[UserDocument, "user"]:
    """Get or create a user based on their full name."""
    logger.info(f"Getting or creating user with full name: {user_full_name}")

    first_name, last_name = utils.split_user_full_name(user_full_name)
    logger.info(f"After split_user_full_name: {first_name}, {last_name}")
    user = UserDocument.get_or_create(first_name=first_name, last_name=last_name)
    logger.info(f"After get or create: {user}")

    step_context = get_step_context()
    step_context.add_output_metadata(output_name="user", metadata=_get_metadata(user_full_name, user))
    logger.info(f"After adding metadata to context: {user}")

    return user


def _get_metadata(user_full_name: str, user: UserDocument) -> dict:
    return {
        "query": {"user_full_name": user_full_name,}, 
        "retreived": {  
        "user_id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        },  
    } 

 