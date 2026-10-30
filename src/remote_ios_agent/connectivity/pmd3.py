from contextlib import AsyncExitStack

from remote_ios_agent.core.errors import RemoteIOSError


def require_pmd3():
    try:
        import pymobiledevice3  # noqa: F401
    except ImportError as exc:
        raise RemoteIOSError("dependency_missing", "Install remote-ios-agent[device]") from exc


async def open_rsd(config, stack: AsyncExitStack):
    require_pmd3()
    from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService

    if config.transport == "rsd":
        return await stack.enter_async_context(RemoteServiceDiscoveryService((config.host, config.port)))
    if config.transport == "usb":
        from pymobiledevice3.remote.rsd_tunnel import PreferredRsdTunnel

        return await stack.enter_async_context(PreferredRsdTunnel(serial=config.identifier, autopair=False))
    if config.transport == "remote-pairing":
        from pymobiledevice3.remote.common import TunnelProtocol
        from pymobiledevice3.remote.tunnel_service import (
            RemotePairingTunnelService,
            start_tunnel_over_remotepairing,
        )

        service = RemotePairingTunnelService(config.identifier, config.host, config.port)
        stack.push_async_callback(service.close)
        await service.connect(autopair=False)
        tunnel = await stack.enter_async_context(
            start_tunnel_over_remotepairing(service, protocol=TunnelProtocol(config.protocol))
        )
        # Kernel tunnel: needs TUN permissions and a routable reverse media path.
        return await stack.enter_async_context(RemoteServiceDiscoveryService((tunnel.address, tunnel.port)))
    raise RemoteIOSError("configuration_error", "Unsupported real-device transport")


async def discover_usb():
    require_pmd3()
    from pymobiledevice3.usbmux import list_devices

    from remote_ios_agent.core.config import DeviceConfig

    return [DeviceConfig(d.serial, d.serial) for d in await list_devices()]
