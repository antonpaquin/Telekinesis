class ScriptPermissions:
    def __init__(self):
        self.create = 'script.create'

    def read(self, script_id: str):
        return 'script.read.{}'.format(script_id)

    def update(self, script_id: str):
        return 'script.update.{}'.format(script_id)

    def destroy(self, script_id: str):
        return 'script.destroy.{}'.format(script_id)

    def execute(self, script_id: str):
        return 'script.execute.{}'.format(script_id)


class ScriptsPermissions:
    def __init__(self):
        self.read = 'scripts.read'


class UserPermissions:
    def __init__(self):
        self.create = 'user.create'
        self.read = 'user.read'
        self.destroy = 'user.destroy'


class PermissionPermissions:
    def __init__(self):
        self.create = 'permission.create'
        self.destroy = 'permission.destroy'


class Permissions:
    user = UserPermissions()
    scripts = ScriptsPermissions()
    permission = PermissionPermissions()
    script = ScriptPermissions()
