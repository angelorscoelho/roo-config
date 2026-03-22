## Installing Python-based MCP Servers

This section outlines the process for installing Python-based MCP servers, incorporating lessons learned from recent development sessions.

### Key Lessons Learned:

1.  **Virtual Environment Requirement**: The `uv pip` command requires an active virtual environment. If no virtual environment is found, the installation will fail with an error message like "No virtual environment found."
2.  **Installation Workflow**:
    *   First, create a virtual environment using the command:
        ```bash
        uv venv
        ```
    *   Once the virtual environment is created and activated, you can install packages using:
        ```bash
        uv pip install <package_name>
        ```
        Replace `<package_name>` with the actual name of the MCP server package you wish to install.
3.  **Configuration**: After installation, MCP servers should be registered in the project's configuration file. Add the server details to `configs/mcp_settings.json` following the specified command format.
