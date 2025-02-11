from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict
from zenml import Client
from zenml.exceptions import EntityExistsError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    #Openai API key
    OPENAI_MODEL_ID: str = "gpt-4o-mini"
    OPENAI_API_KEY: str | None = None

    #HUGGINGFACE API key
    HUGGINGFACE_ACCESS_TOKEN: str | None = None


    #COMET API key
    COMET_API_KEY: str | None = None
    COMET_PROJECT: str = "twin"

    #mongoDB Database
    DATABASE_HOST: str = "mongodb://localhost:27017/"
    DATABASE_NAME: str = "twin"


    #QUADRANT API key
    USE_QDRANT_CLOUD: bool = False
    QDRANT_DATABASE_HOST: str = "localhost"
    QDRANT_DATABASE_PORT: int = 6333
    QDRANT_CLOUD_URL: str = "https://qdrant.cloud"
    QDRANT_API_KEY: str | None = None

    #AWS AUTH
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY: str | None = None
    AWS_SECRET_KEY: str | None = None
    AWS_ARN_ROLE: str | None = None

    #aws SAGE MAKER
    HF_MODEL_ID: str = "mlabonne/TwinLlama-3.1-8B-DPO"
    GPU_INSTANCE: str = "ml.g5.2xlarge"
    SM_NUM_GPUS: int = 1
    MAX_INPUT_LENGTH: int = 2048
    MAX_TOTAL_TOKENS: int = 4096
    COPIES: int = 1  # number of replicas
    GPUS: int = 1  # number of gpus per replica
    CPUS: int = 4  # number of cpus per replica


    SAGERMAKER_ENDPOINT_CONFIG_INFERENCE: str = "twin"
    SAGERMAKER_ENDPOINT_INFERENCE: str = "twin"
    TEMPERATURE_INFERENCE: float = 0.01
    TOP_P_INFERENCE: float = 0.9
    MAX_NEW_TOKENS_INFERENCE: int = 150

    # RAG
    TEXT_EMBEDDING_MODEL_ID: str = "sentence-transformers/all-MiniLM-L6-v2"
    RERANKING_CROSS_ENCODER_MODEL_ID: str = "cross-encoder/ms-marco-MiniLM-L-4-v2"
    RAG_MODEL_DEVICE: str = "cpu"


    # LinkdIn login
    LINKEDIN_USERNAME: str | None = None
    LINKEDIN_PASSWORD: str | None = None

    @property
    def OPENAI_MAX_TOKEN_WINDOW(self) -> int:
        official_max_token_window = {
            "gpt-3.5-turbo": 16385,
            "gpt-4-turbo": 128000,
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
        }.get(self.OPENAI_MODEL_ID, 128000)

        max_token_window = int(official_max_token_window * 0.9)
                
        return max_token_window
    

    @classmethod
    def load_settings(cls) -> "Settings":
        """
        Tries to load the settings from the ZenML secret store. If the secret does not exist, it initializes the settings from the .env file and default values.

        Returns:
            Settings: The initialized settings object.
        """

        try:
            logger.info("Loading settings from the ZenML secret store.")

            settings_secrets = Client().get_secret("settings")
            settings = Settings(**settings_secrets.secret_values)
        except (RuntimeError, KeyError):
            logger.warning(
                "Failed to load settings from the ZenML secret store. Defaulting to loading the settings from the '.env' file."
            )
            settings = Settings()

        return settings
    

    def export(self) -> None:
        """
        Exports the settings to the ZenML secret store.
        
        """
        env_vars = settings.model_dump()
        for key, value in env_vars.items():
            env_vars[key] = str(value)

        client = Client()
        
        logger.info("Exporting settings to the ZenML secret store.")

        try:
            client.create_secret(name="settings", values=env_vars)
        except EntityExistsError:
            logger.warning("Secret 'scope' already exists. Delete it manually by running 'zenml secret delete settings', before trying to recreate it.")

settings = Settings.load_settings()

