class DeviceResolver:
    def __init__(self):
        self._device_map: dict[str, str] = {}

    def set_device(self, name: str, device_id: str) -> None:
        self._device_map[name.lower()] = device_id

    def resolve(self, device_name: str | None) -> str | None:
        if not device_name:
            return None
        return self._device_map.get(device_name.lower())

    def invalidate(self) -> None:
        self._device_map.clear()
