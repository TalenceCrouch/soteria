import pytest

from soteria.cli import build_parser


@pytest.mark.parametrize(
    ("argv", "option"),
    [
        (["watch", "BTC-USD", "--levels", "0"], "--levels"),
        (["collect", "BTC-USD", "--seconds", "-1", "--out", "features.csv"], "--seconds"),
    ],
)
def test_positive_integer_options_reject_non_positive_values(
    argv: list[str], option: str, capsys: pytest.CaptureFixture[str]
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(argv)

    stderr = capsys.readouterr().err
    assert exc_info.value.code == 2
    assert option in stderr
    assert "must be a positive integer" in stderr
