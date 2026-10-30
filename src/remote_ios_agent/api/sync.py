import asyncio

from remote_ios_agent.api.session import AsyncRemoteIOS


class SyncDevice:
    def __init__(self, owner, session):
        self.owner, self.session = owner, session
        self.ui = self

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        method = getattr(self.session, name)
        if not callable(method):
            return method

        def invoke(*args, **kwargs):
            return self.owner.runner.run(method(*args, **kwargs))

        return invoke


class DeviceCollection:
    def __init__(self, owner):
        self.owner = owner

    def list(self):
        return self.owner.runner.run(self.owner.async_api.devices())

    def first(self):
        """Only selects an unambiguous device. Multiple devices require select(name)."""
        return self.select()

    def select(self, identifier=None):
        session = self.owner.runner.run(self.owner.async_api.session(identifier))
        self.owner.runner.run(session.__aenter__())
        self.owner.sessions.append(session)
        return SyncDevice(self.owner, session)


class RemoteIOS:
    """Synchronous facade; use as a context manager to close device resources."""

    def __init__(self, config=None):
        self.runner = asyncio.Runner()
        self.async_api = AsyncRemoteIOS(config)
        self.sessions = []
        self.devices = DeviceCollection(self)

    def __enter__(self):
        return self

    def close(self):
        try:
            for session in reversed(self.sessions):
                self.runner.run(session.__aexit__(None, None, None))
            self.sessions.clear()
        finally:
            self.runner.close()

    def __exit__(self, *exc):
        self.close()
