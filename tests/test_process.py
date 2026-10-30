import sys

import pytest

from remote_ios_agent.core.errors import RemoteIOSError
from remote_ios_agent.core.process import run


async def test_process_error_and_timeout(tmp_path):
    with pytest.raises(RemoteIOSError) as error:
        await run([sys.executable, "-c", "raise SystemExit(7)"], log=tmp_path / "error.log")
    assert error.value.details["exit_code"] == 7
    with pytest.raises(RemoteIOSError) as error:
        await run([sys.executable, "-c", "import time; time.sleep(10)"], timeout=0.05)
    assert error.value.code == "timeout"


async def test_no_shell_interpolation(tmp_path):
    output = tmp_path / "args.log"
    await run(
        [sys.executable, "-c", "import sys; print(sys.argv[1])", "$(echo unsafe); touch unexpected"],
        log=output,
    )
    assert output.read_text().strip() == "$(echo unsafe); touch unexpected"
