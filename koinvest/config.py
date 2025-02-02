from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_KEY: str
    APP_SECRET: str
    URL_BASE: str 
    
    model_config = SettingsConfigDict(env_file='.env') 

config = Settings()