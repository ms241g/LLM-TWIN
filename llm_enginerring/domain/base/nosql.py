import uuid
from abc import ABC
from typing import Generic, Type, TypeVar, Optional

from loguru import logger
from pydantic import BaseModel, Field, UUID4
from pymongo import errors

from llm_enginerring.domain.exceptions import ImproperlyConfigured
from llm_enginerring.infrastructure.db.mongo import connection
from llm_enginerring.settings import settings

_database = connection.get_database(settings.DATABASE_NAME)

T = TypeVar("T", bound="NoSQLBaseDocument")

class NoSQLBaseDocument(BaseModel, ABC, Generic[T]):
    """Base document for NoSQL databases."""

    id: UUID4 = Field(default_factory=uuid.uuid4)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return False
        return self.id == value.id
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    @classmethod
    def from_mongo(cls: Type[T], data: dict) -> T:
        """convert id str object into id UUID4 object"""
        if not data:
            raise ValueError("No data provided to convert to document.")
        
        id = data.pop("_id")

        return cls(**dict(data, id=id))
    
    def to_mongo(self: T, **kwargs) -> dict:
        """convert id UUID4 object into id str object"""
        exclude_unset = kwargs.pop("exclude_unset", False)
        by_alias = kwargs.pop("by_alias", True)

        parsed = self.model_dump(exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)

        if "_id" not in parsed and "id" in parsed:
            parsed["_id"] = parsed.pop("id")

        for key, value in parsed.items():
            if isinstance(value, uuid.UUID):
                parsed[key] = str(value)
              
        return parsed
    

    def model_dump(self: T, **kwargs) -> dict:
        """Dump the model to a dictionary."""
        dict_ = super().model_dump(**kwargs)

        for key, value in dict_.items():
            if isinstance(value, uuid.UUID):
                dict_[key] = str(value)

        return dict_
    

    def save(self: T, **kwargs) -> T:
        """Save the document to the database."""
        collection = _database[self.get_collection_name()]

        try:
            collection.insert_one(self.to_mongo(**kwargs))

            return self 
        except errors.WriteError as e:
            logger.error(f"Error saving document: {e}")
            
            return None

    @classmethod
    def get_or_create(cls: Type[T], **filter_options) -> T:
        """Get or create a document based on filter options."""
        collection = _database[cls.get_collection_name()]
        
        try:
            instance = collection.find_one(filter_options)
            if instance:
                return cls.from_mongo(instance)
            
            new_instance = cls(**filter_options)
            new_instance = new_instance.save()

            return new_instance
        except errors.OperationFailure:
            logger.exception(f"Failed to retrieve document with filter options: {filter_options}")

            raise

    
    @classmethod
    def bulk_insert(cls: Type[T], documents: list[T], **kwargs) -> bool:
        """Bulk insert a list of documents."""
        collection = _database[cls.get_collection_name()]

        try:
            collection.insert_many([doc.to_mongo(**kwargs) for doc in documents])

            return True
        except (errors.BulkWriteError, errors.WriteError) as e:
            logger.error(f"Failed to insert documents of type {cls.__name__}")

            return False
        
    
    @classmethod
    def find(cls: Type[T], **filter_options) -> T | None:
        """Find a document based on filter options."""
        collection = _database[cls.get_collection_name()]

        try:
            instance = collection.find_one(filter_options)
            if instance:
                return cls.from_mongo(instance)

            return None
        except errors.OperationFailure:
            logger.error("Failed to find document with filter options")

            return None
        
    
    @classmethod
    def bulk_find(cls: Type[T], **filter_options) -> list[T]:
        """Bulk find documents based on filter options."""
        collection = _database[cls.get_collection_name()]

        try:
            instances = collection.find(filter_options)
            return [document for intance in instances if (document := cls.from_mongo(instance)) is not None]
        except errors.OperationFailure:
            logger.error("Failed to bulk find documents with filter options")

            return []
        
    
    @classmethod
    def get_collection_name(cls: Type[T]) -> str:
        """Get the collection name for the document."""
        if not hasattr(cls, "Settings") or not hasattr(cls.Settings, "nam"):
            raise ImproperlyConfigured(
                "Document should define an Settings configuration class with the name of the collection.")
        
        return cls.Settings.name

