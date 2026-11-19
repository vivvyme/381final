hewwo

# TODO


1. Flush out all roles and configs based on rubric (Pings, eigrp, vlans, trunking, ntp)
2. Read and change a switch using restconf (rubric)
3. Docker
4. MCP

# CI

Stages:
1. **yamllint** (`ansible/.yamllint`)
2. **ansible-lint** (`ansible/.ansible-lint`)
3. **syntax-check** (`orchestrator.yml`)

`.github/actions/setup_runners` - Python, pip, Galaxy collections with caching

`ansible/requirements/requirements.txt` - Python Deps

`ansible/collections/requirements.yml` - Ansible Collections
