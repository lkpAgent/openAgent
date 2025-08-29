"""Agent configuration service."""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.agent_config import AgentConfig
from ..utils.logger import get_logger
from ..utils.exceptions import ValidationError, NotFoundError

logger = get_logger("agent_config_service")


class AgentConfigService:
    """Service for managing agent configurations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_config(self, config_data: Dict[str, Any]) -> AgentConfig:
        """Create a new agent configuration."""
        try:
            # Validate required fields
            if not config_data.get("name"):
                raise ValidationError("Configuration name is required")
            
            # Check if name already exists
            existing = self.db.query(AgentConfig).filter(
                AgentConfig.name == config_data["name"]
            ).first()
            if existing:
                raise ValidationError(f"Configuration with name '{config_data['name']}' already exists")
            
            # Create new configuration
            config = AgentConfig(
                name=config_data["name"],
                description=config_data.get("description", ""),
                enabled_tools=config_data.get("enabled_tools", ["calculator", "weather", "search", "datetime", "file"]),
                max_iterations=config_data.get("max_iterations", 10),
                temperature=config_data.get("temperature", 0.1),
                system_message=config_data.get("system_message", "You are a helpful AI assistant with access to various tools. Use the available tools to help answer user questions accurately. Always explain your reasoning and the tools you're using."),
                verbose=config_data.get("verbose", True),
                is_active=config_data.get("is_active", True),
                is_default=config_data.get("is_default", False)
            )
            
            # If this is set as default, unset other defaults
            if config.is_default:
                self.db.query(AgentConfig).filter(
                    AgentConfig.is_default == True
                ).update({"is_default": False})
            
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            
            logger.info(f"Created agent configuration: {config.name}")
            return config
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating agent configuration: {str(e)}")
            raise
    
    def get_config(self, config_id: int) -> Optional[AgentConfig]:
        """Get agent configuration by ID."""
        return self.db.query(AgentConfig).filter(
            AgentConfig.id == config_id
        ).first()
    
    def get_config_by_name(self, name: str) -> Optional[AgentConfig]:
        """Get agent configuration by name."""
        return self.db.query(AgentConfig).filter(
            AgentConfig.name == name
        ).first()
    
    def get_default_config(self) -> Optional[AgentConfig]:
        """Get default agent configuration."""
        return self.db.query(AgentConfig).filter(
            and_(AgentConfig.is_default == True, AgentConfig.is_active == True)
        ).first()
    
    def list_configs(self, active_only: bool = True) -> List[AgentConfig]:
        """List all agent configurations."""
        query = self.db.query(AgentConfig)
        if active_only:
            query = query.filter(AgentConfig.is_active == True)
        return query.order_by(AgentConfig.created_at.desc()).all()
    
    def update_config(self, config_id: int, config_data: Dict[str, Any]) -> AgentConfig:
        """Update agent configuration."""
        try:
            config = self.get_config(config_id)
            if not config:
                raise NotFoundError(f"Agent configuration with ID {config_id} not found")
            
            # Check if name change conflicts with existing
            if "name" in config_data and config_data["name"] != config.name:
                existing = self.db.query(AgentConfig).filter(
                    and_(
                        AgentConfig.name == config_data["name"],
                        AgentConfig.id != config_id
                    )
                ).first()
                if existing:
                    raise ValidationError(f"Configuration with name '{config_data['name']}' already exists")
            
            # Update fields
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            # If this is set as default, unset other defaults
            if config_data.get("is_default", False):
                self.db.query(AgentConfig).filter(
                    and_(
                        AgentConfig.is_default == True,
                        AgentConfig.id != config_id
                    )
                ).update({"is_default": False})
            
            self.db.commit()
            self.db.refresh(config)
            
            logger.info(f"Updated agent configuration: {config.name}")
            return config
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating agent configuration: {str(e)}")
            raise
    
    def delete_config(self, config_id: int) -> bool:
        """Delete agent configuration (soft delete by setting is_active=False)."""
        try:
            config = self.get_config(config_id)
            if not config:
                raise NotFoundError(f"Agent configuration with ID {config_id} not found")
            
            # Don't allow deleting the default configuration
            if config.is_default:
                raise ValidationError("Cannot delete the default configuration")
            
            config.is_active = False
            self.db.commit()
            
            logger.info(f"Deleted agent configuration: {config.name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting agent configuration: {str(e)}")
            raise
    
    def set_default_config(self, config_id: int) -> AgentConfig:
        """Set a configuration as default."""
        try:
            config = self.get_config(config_id)
            if not config:
                raise NotFoundError(f"Agent configuration with ID {config_id} not found")
            
            if not config.is_active:
                raise ValidationError("Cannot set inactive configuration as default")
            
            # Unset other defaults
            self.db.query(AgentConfig).filter(
                AgentConfig.is_default == True
            ).update({"is_default": False})
            
            # Set this as default
            config.is_default = True
            self.db.commit()
            self.db.refresh(config)
            
            logger.info(f"Set default agent configuration: {config.name}")
            return config
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error setting default agent configuration: {str(e)}")
            raise
    
    def get_config_dict(self, config_id: Optional[int] = None) -> Dict[str, Any]:
        """Get configuration as dictionary. If no ID provided, returns default config."""
        if config_id:
            config = self.get_config(config_id)
        else:
            config = self.get_default_config()
        
        if not config:
            # Return default values if no configuration found
            return {
                "enabled_tools": ["calculator", "weather", "search", "datetime", "file", "generate_image"],
                "max_iterations": 10,
                "temperature": 0.1,
                "system_message": "You are a helpful AI assistant with access to various tools. Use the available tools to help answer user questions accurately. Always explain your reasoning and the tools you're using.",
                "verbose": True
            }
        
        return {
            "enabled_tools": config.enabled_tools,
            "max_iterations": config.max_iterations,
            "temperature": config.temperature,
            "system_message": config.system_message,
            "verbose": config.verbose
        }