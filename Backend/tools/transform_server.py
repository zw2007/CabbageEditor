"""Compatibility wrapper for the relocated Transform MCP server."""

from Backend.network_service.transform_server import (
    app,
    call_actor_operation,
    list_actors,
    main,
    transform_actor,
)

__all__ = ["app", "transform_actor", "list_actors", "call_actor_operation", "main"]


if __name__ == "__main__":
    main()
