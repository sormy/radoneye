from unittest.mock import AsyncMock, patch

import pytest
from bleak.backends.device import BLEDevice
from inline_snapshot import snapshot

from radoneye.cli import main
from radoneye.model import OutputType
from radoneye.util import serialize_object, to_bq_m3, to_pci_l


@patch("radoneye.cli.RadonEyeClient")
@pytest.mark.asyncio
@pytest.mark.parametrize("output", ["text", "json"])
async def test_unit_get(
    RadonEyeClient: AsyncMock,
    capsys: pytest.CaptureFixture[str],
    output: OutputType,
):
    radoneye_client_outer = RadonEyeClient.return_value
    radoneye_client = radoneye_client_outer.__aenter__.return_value

    radoneye_client.status.return_value = {"display_unit": "pci/l"}

    await main(["radoneye", "unit", "address", "--output", output])

    RadonEyeClient.assert_called_once_with(
        "address", adapter=None, connect_timeout=10, status_read_timeout=5, debug=False
    )
    radoneye_client.status.assert_called_once_with()
    radoneye_client.set_unit.assert_not_called()

    assert capsys.readouterr().out.rstrip() == serialize_object("pci/l", output)


@patch("radoneye.cli.RadonEyeClient")
@pytest.mark.asyncio
@pytest.mark.parametrize("output", ["text", "json"])
async def test_unit_set(
    RadonEyeClient: AsyncMock,
    capsys: pytest.CaptureFixture[str],
    output: OutputType,
):
    radoneye_client_outer = RadonEyeClient.return_value
    radoneye_client = radoneye_client_outer.__aenter__.return_value

    await main(["radoneye", "unit", "address", "--unit", "pci/l", "--output", output])

    RadonEyeClient.assert_called_once_with(
        "address", adapter=None, connect_timeout=10, status_read_timeout=5, debug=False
    )
    radoneye_client.status.assert_not_called()
    radoneye_client.set_unit.assert_called_once_with("pci/l")

    assert capsys.readouterr().out.rstrip() == serialize_object("pci/l", output)


@patch("radoneye.cli.RadonEyeClient")
@pytest.mark.asyncio
@pytest.mark.parametrize("output", ["text", "json"])
async def test_alarm_get(
    RadonEyeClient: AsyncMock,
    capsys: pytest.CaptureFixture[str],
    output: OutputType,
):
    radoneye_client_outer = RadonEyeClient.return_value
    radoneye_client = radoneye_client_outer.__aenter__.return_value

    radoneye_client.status.return_value = {
        "display_unit": "pci/l",
        "alarm_enabled": True,
        "alarm_level_bq_m3": 74.0,
        "alarm_level_pci_l": 2.0,
        "alarm_interval_minutes": 60,
    }

    await main(["radoneye", "alarm", "address", "--output", output])

    RadonEyeClient.assert_called_once_with(
        "address", adapter=None, connect_timeout=10, status_read_timeout=5, debug=False
    )
    radoneye_client.status.assert_called_once_with()
    radoneye_client.set_alarm.assert_not_called()

    assert capsys.readouterr().out.rstrip() == serialize_object(
        {
            "alarm_enabled": True,
            "alarm_level_bq_m3": 74.0,
            "alarm_level_pci_l": 2.0,
            "alarm_interval_minutes": 60,
        },
        output,
    )


@patch("radoneye.cli.RadonEyeClient")
@pytest.mark.asyncio
@pytest.mark.parametrize("output", ["text", "json"])
async def test_alarm_set_all(
    RadonEyeClient: AsyncMock,
    capsys: pytest.CaptureFixture[str],
    output: OutputType,
):
    radoneye_client_outer = RadonEyeClient.return_value
    radoneye_client = radoneye_client_outer.__aenter__.return_value

    await main(
        [
            "radoneye",
            "alarm",
            "address",
            "--status",
            "on",
            "--unit",
            "bq/m3",
            "--level",
            "111",
            "--interval",
            "10",
            "--output",
            output,
        ]
    )

    RadonEyeClient.assert_called_once_with(
        "address", adapter=None, connect_timeout=10, status_read_timeout=5, debug=False
    )
    radoneye_client.status.assert_not_called()
    radoneye_client.set_alarm.assert_called_once_with(
        enabled=True, level=111.0, unit="bq/m3", interval=10
    )

    assert capsys.readouterr().out.rstrip() == serialize_object(
        {
            "alarm_enabled": True,
            "alarm_level_bq_m3": 111.0,
            "alarm_level_pci_l": 3.0,
            "alarm_interval_minutes": 10,
        },
        output,
    )


@patch("radoneye.cli.RadonEyeClient")
@pytest.mark.asyncio
@pytest.mark.parametrize("output", ["text", "json"])
@pytest.mark.parametrize("alarm_status", [True, False])
async def test_alarm_set_status(
    RadonEyeClient: AsyncMock,
    capsys: pytest.CaptureFixture[str],
    output: OutputType,
    alarm_status: bool,
):
    radoneye_client_outer = RadonEyeClient.return_value
    radoneye_client = radoneye_client_outer.__aenter__.return_value

    new_alarm_status = not alarm_status

    fake_status = {
        "display_unit": "pci/l",
        "alarm_enabled": alarm_status,
        "alarm_level_bq_m3": 74.0,
        "alarm_level_pci_l": 2.0,
        "alarm_interval_minutes": 60,
    }

    radoneye_client.status.return_value = fake_status

    await main(
        [
            "radoneye",
            "alarm",
            "address",
            "--status",
            "on" if new_alarm_status else "off",
            "--output",
            output,
        ]
    )

    RadonEyeClient.assert_called_once_with(
        "address", adapter=None, connect_timeout=10, status_read_timeout=5, debug=False
    )
    radoneye_client.status.assert_called_once_with()
    radoneye_client.set_alarm.assert_called_once_with(
        enabled=new_alarm_status,
        level=fake_status["alarm_level_pci_l"],
        unit=fake_status["display_unit"],
        interval=fake_status["alarm_interval_minutes"],
    )

    assert capsys.readouterr().out.rstrip() == serialize_object(
        {
            "alarm_enabled": new_alarm_status,
            "alarm_level_bq_m3": fake_status["alarm_level_bq_m3"],
            "alarm_level_pci_l": fake_status["alarm_level_pci_l"],
            "alarm_interval_minutes": fake_status["alarm_interval_minutes"],
        },
        output,
    )


@patch("radoneye.cli.RadonEyeClient")
@pytest.mark.asyncio
@pytest.mark.parametrize("output", ["text", "json"])
async def test_alarm_set_level_no_unit(
    RadonEyeClient: AsyncMock,
    capsys: pytest.CaptureFixture[str],
    output: OutputType,
):
    radoneye_client_outer = RadonEyeClient.return_value
    radoneye_client = radoneye_client_outer.__aenter__.return_value

    fake_status = {
        "display_unit": "pci/l",
        "alarm_enabled": True,
        "alarm_level_bq_m3": 74.0,
        "alarm_level_pci_l": 2.0,
        "alarm_interval_minutes": 60,
    }

    radoneye_client.status.return_value = fake_status

    await main(
        [
            "radoneye",
            "alarm",
            "address",
            "--level",
            "3.0",
            "--output",
            output,
        ]
    )

    RadonEyeClient.assert_called_once_with(
        "address", adapter=None, connect_timeout=10, status_read_timeout=5, debug=False
    )
    radoneye_client.status.assert_called_once_with()
    radoneye_client.set_alarm.assert_called_once_with(
        enabled=fake_status["alarm_enabled"],
        level=3.0,
        unit=fake_status["display_unit"],
        interval=fake_status["alarm_interval_minutes"],
    )

    assert capsys.readouterr().out.rstrip() == serialize_object(
        {
            "alarm_enabled": fake_status["alarm_enabled"],
            "alarm_level_bq_m3": to_bq_m3(3.0),
            "alarm_level_pci_l": 3.0,
            "alarm_interval_minutes": fake_status["alarm_interval_minutes"],
        },
        output,
    )


@patch("radoneye.cli.RadonEyeClient")
@pytest.mark.asyncio
@pytest.mark.parametrize("output", ["text", "json"])
async def test_alarm_set_level_with_unit(
    RadonEyeClient: AsyncMock,
    capsys: pytest.CaptureFixture[str],
    output: OutputType,
):
    radoneye_client_outer = RadonEyeClient.return_value
    radoneye_client = radoneye_client_outer.__aenter__.return_value

    fake_status = {
        "display_unit": "pci/l",
        "alarm_enabled": True,
        "alarm_level_bq_m3": 74.0,
        "alarm_level_pci_l": 2.0,
        "alarm_interval_minutes": 60,
    }

    radoneye_client.status.return_value = fake_status

    await main(
        [
            "radoneye",
            "alarm",
            "address",
            "--level",
            "111",
            "--unit",
            "bq/m3",
            "--output",
            output,
        ]
    )

    RadonEyeClient.assert_called_once_with(
        "address", adapter=None, connect_timeout=10, status_read_timeout=5, debug=False
    )
    radoneye_client.status.assert_called_once_with()
    radoneye_client.set_alarm.assert_called_once_with(
        enabled=fake_status["alarm_enabled"],
        level=111,
        unit="bq/m3",
        interval=fake_status["alarm_interval_minutes"],
    )

    assert capsys.readouterr().out.rstrip() == serialize_object(
        {
            "alarm_enabled": fake_status["alarm_enabled"],
            "alarm_level_bq_m3": 111.0,
            "alarm_level_pci_l": to_pci_l(111),
            "alarm_interval_minutes": fake_status["alarm_interval_minutes"],
        },
        output,
    )


@patch("radoneye.cli.RadonEyeClient")
@pytest.mark.asyncio
@pytest.mark.parametrize("output", ["text", "json"])
async def test_alarm_set_interval(
    RadonEyeClient: AsyncMock,
    capsys: pytest.CaptureFixture[str],
    output: OutputType,
):
    radoneye_client_outer = RadonEyeClient.return_value
    radoneye_client = radoneye_client_outer.__aenter__.return_value

    fake_status = {
        "display_unit": "pci/l",
        "alarm_enabled": True,
        "alarm_level_bq_m3": 74.0,
        "alarm_level_pci_l": 2.0,
        "alarm_interval_minutes": 60,
    }

    radoneye_client.status.return_value = fake_status

    await main(
        [
            "radoneye",
            "alarm",
            "address",
            "--interval",
            "10",
            "--output",
            output,
        ]
    )

    RadonEyeClient.assert_called_once_with(
        "address", adapter=None, connect_timeout=10, status_read_timeout=5, debug=False
    )
    radoneye_client.status.assert_called_once_with()
    radoneye_client.set_alarm.assert_called_once_with(
        enabled=fake_status["alarm_enabled"],
        level=fake_status["alarm_level_pci_l"],
        unit=fake_status["display_unit"],
        interval=10,
    )

    assert capsys.readouterr().out.rstrip() == serialize_object(
        {
            "alarm_enabled": fake_status["alarm_enabled"],
            "alarm_level_bq_m3": fake_status["alarm_level_bq_m3"],
            "alarm_level_pci_l": fake_status["alarm_level_pci_l"],
            "alarm_interval_minutes": 10,
        },
        output,
    )


@patch("radoneye.cli.RadonEyeClient")
@pytest.mark.asyncio
@pytest.mark.parametrize("output", ["text", "json"])
async def test_get_status(
    RadonEyeClient: AsyncMock,
    capsys: pytest.CaptureFixture[str],
    output: OutputType,
):
    radoneye_client_outer = RadonEyeClient.return_value
    radoneye_client = radoneye_client_outer.__aenter__.return_value

    fake_status = {
        "serial": "RU22201030383",
        "model": "RD200N",
        "firmware_version": "V2.0.2",
        "latest_bq_m3": 10,
        "latest_pci_l": 0.27,
        "day_avg_bq_m3": 8,
        "day_avg_pci_l": 0.22,
        "month_avg_bq_m3": 0,
        "month_avg_pci_l": 0.0,
        "peak_bq_m3": 28,
        "peak_pci_l": 0.76,
        "counts_current": 3,
        "counts_previous": 1,
        "counts_str": "3/1",
        "uptime_minutes": 12409,
        "uptime_str": "8d14h49m",
        "display_unit": "pci/l",
        "alarm_enabled": 1,
        "alarm_level_bq_m3": 74,
        "alarm_level_pci_l": 2.0,
        "alarm_interval_minutes": 60,
    }

    radoneye_client.status.return_value = fake_status

    await main(["radoneye", "status", "address", "--output", output])

    RadonEyeClient.assert_called_once_with(
        "address", adapter=None, connect_timeout=10, status_read_timeout=5, debug=False
    )
    radoneye_client.status.assert_called_once_with()

    assert capsys.readouterr().out.rstrip() == serialize_object(fake_status, output)


@patch("radoneye.cli.RadonEyeClient")
@pytest.mark.asyncio
async def test_trigger_beep(RadonEyeClient: AsyncMock, capsys: pytest.CaptureFixture[str]):
    radoneye_client_outer = RadonEyeClient.return_value
    radoneye_client = radoneye_client_outer.__aenter__.return_value

    await main(["radoneye", "beep", "address"])

    RadonEyeClient.assert_called_once_with("address", adapter=None, connect_timeout=10, debug=False)
    radoneye_client.beep.assert_called_once_with()

    assert capsys.readouterr().out.rstrip() == "beep"


@patch("radoneye.cli.RadonEyeClient")
@pytest.mark.asyncio
@pytest.mark.parametrize("output", ["text", "json"])
async def test_get_history(
    RadonEyeClient: AsyncMock,
    capsys: pytest.CaptureFixture[str],
    output: OutputType,
):
    radoneye_client_outer = RadonEyeClient.return_value
    radoneye_client = radoneye_client_outer.__aenter__.return_value

    fake_history = {
        "values_bq_m3": [1.0 * 37.0, 37 * 2.0, 37 * 3.0],
        "values_pci_l": [1.0, 2.0, 3.0],
    }

    radoneye_client.history.return_value = fake_history

    await main(["radoneye", "history", "address", "--output", output])

    RadonEyeClient.assert_called_once_with(
        "address", adapter=None, connect_timeout=10, history_read_timeout=60, debug=False
    )
    radoneye_client.history.assert_called_once_with()

    out_content = capsys.readouterr().out.rstrip()
    if output == "text":
        assert out_content == snapshot(
            """\
#	Bq/m3	pCi/L
1	37.0	1.0
2	74.0	2.0
3	111.0	3.0\
"""
        )
    else:
        assert out_content == serialize_object(fake_history, output)


@patch("radoneye.cli.RadonEyeScanner.discover")
@pytest.mark.asyncio
@pytest.mark.parametrize("output", ["text", "json"])
async def test_list(
    discover_mock: AsyncMock,
    capsys: pytest.CaptureFixture[str],
    output: OutputType,
):
    dev1 = BLEDevice("70C12E8A-27F6-3AEC-0BAD-95FA94BF17A9", "FR:RU22201030383", None, 0)
    dev2 = BLEDevice("3775964E-C653-C00C-7F02-7C03F9F0122D", "FR:RU22204180050", None, 0)

    discover_mock.return_value = [dev1, dev2]

    await main(["radoneye", "list", "--output", output])

    discover_mock.assert_called_once_with(adapter=None, timeout=5)

    out_content = capsys.readouterr().out.rstrip()
    if output == "text":
        assert out_content == "\n".join(
            [
                "70C12E8A-27F6-3AEC-0BAD-95FA94BF17A9\tFR:RU22201030383",
                "3775964E-C653-C00C-7F02-7C03F9F0122D\tFR:RU22204180050",
            ]
        )
    else:
        assert out_content == serialize_object(
            [
                {"address": "70C12E8A-27F6-3AEC-0BAD-95FA94BF17A9", "name": "FR:RU22201030383"},
                {"address": "3775964E-C653-C00C-7F02-7C03F9F0122D", "name": "FR:RU22204180050"},
            ],
            output,
        )
